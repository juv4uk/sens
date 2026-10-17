#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_d11_selector_seed.py"
SPEC = importlib.util.spec_from_file_location("check_d11_selector_seed", SCRIPT)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class D11SelectorSeedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = MOD.load_documents(ROOT)

    def changed(self):
        return copy.deepcopy(self.documents)

    def assert_rejected(self, docs, test_id):
        with self.assertRaises(MOD.AuditError) as caught:
            MOD.validate_documents(docs)
        self.assertEqual(caught.exception.test_id, test_id)

    def test_current_selector_seed_is_exactly_512_candidates_not_residents(self):
        report = MOD.validate_documents(self.documents)
        self.assertEqual(report["status"], "MECHANICAL_PASS")
        self.assertEqual(report["semantic_status"], "NOT_VERIFIED")
        self.assertEqual(report["candidate_count"], 512)
        self.assertEqual(report["selector_parents"], 256)
        self.assertEqual(report["unique_coordinates"], 512)
        self.assertEqual(report["unique_names"], 512)
        self.assertEqual(report["testing_only_rows"], 43)
        self.assertEqual(report["candidate_testing_coordinate_collisions"], 0)
        self.assertEqual(report["candidate_testing_name_collisions"], 0)
        self.assertEqual(report["callable_admissions_added"], 0)
        self.assertEqual(report["ratified_residents_added"], 0)

    def test_historical_pin_drift_is_reported_after_all_parents_are_revalidated(self):
        report = MOD.validate_documents(self.documents)
        self.assertFalse(report["historical_pin_matches_current"])
        self.assertIn("all 256 candidate parents revalidated", report["source_pin_note"])

    def test_canonical_d11_table_stays_the_43_row_testing_vocabulary(self):
        report = MOD.validate_documents(self.documents)
        self.assertEqual(report["testing_only_rows"], 43)
        self.assertEqual(self.documents["seed"]["accounting"]["new_ratified_residents"], 0)
        self.assertEqual(self.documents["seed"]["accounting"]["callable"], 0)

    def test_rejects_truncated_ten_bit_candidate(self):
        docs = self.changed()
        docs["seed"]["rows"][0][0] = docs["seed"]["rows"][0][0][:-1]
        self.assert_rejected(docs, "CANDIDATE_WIDTH")

    def test_rejects_duplicate_candidate_coordinate(self):
        docs = self.changed()
        docs["seed"]["rows"][1][0] = docs["seed"]["rows"][0][0]
        self.assert_rejected(docs, "CANDIDATE_DUP_COORD")

    def test_rejects_duplicate_candidate_name(self):
        docs = self.changed()
        docs["seed"]["rows"][1][1] = docs["seed"]["rows"][0][1]
        self.assert_rejected(docs, "CANDIDATE_DUP_NAME")

    def test_rejects_collision_with_ratified_d11_testing_coordinate(self):
        docs = self.changed()
        docs["seed"]["rows"][0][0] = docs["d11_vocabulary"]["table"][0]["bits"]
        self.assert_rejected(docs, "D11_TEST_COORD_COLLISION")

    def test_rejects_collision_with_ratified_d11_testing_name(self):
        docs = self.changed()
        docs["seed"]["rows"][0][1] = docs["d11_vocabulary"]["table"][0]["lisp"]
        self.assert_rejected(docs, "D11_TEST_NAME_COLLISION")

    def test_rejects_wrong_selector_suffix_name(self):
        docs = self.changed()
        bits, name = docs["seed"]["rows"][0]
        docs["seed"]["rows"][0][1] = name[:-2] + "DR"
        self.assert_rejected(docs, "CANDIDATE_NAME_DERIVATION")

    def test_rejects_candidate_without_a_current_d10_selector_parent(self):
        docs = self.changed()
        bits, name = docs["seed"]["rows"][0]
        docs["seed"]["rows"][0][0] = "11111111111"
        self.assert_rejected(docs, "CANDIDATE_PARENT")

    def test_rejects_accidental_d11_ratification_or_callability(self):
        docs = self.changed()
        docs["seed"]["status"] = "RATIFIED"
        self.assert_rejected(docs, "NOT_RESEARCH_ONLY")

        docs = self.changed()
        docs["seed"]["accounting"]["callable"] = 512
        self.assert_rejected(docs, "ACCOUNTING")

    def test_rejects_missing_child_pair(self):
        docs = self.changed()
        docs["seed"]["rows"].pop()
        self.assert_rejected(docs, "CANDIDATE_COUNT")


if __name__ == "__main__":
    unittest.main()
