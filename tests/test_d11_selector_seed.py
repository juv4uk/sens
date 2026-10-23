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

    def test_all_512_selectors_are_mathematically_defined_not_direct_opcodes(self):
        report = MOD.validate_documents(self.documents)
        self.assertEqual(report["status"], "MECHANICAL_PASS")
        self.assertEqual(report["semantic_status"], "DERIVED_BY_COMPOSITION")
        self.assertEqual(report["derived_count"], 512)
        self.assertEqual(report["derived_status"], "MATHEMATICALLY_DERIVED_SELECTOR_FUNCTIONS")
        self.assertEqual(self.documents["seed"]["law"]["derived_by_law"], True)
        self.assertEqual(self.documents["seed"]["accounting"]["d11_mathematically_defined_selectors"], 512)
        self.assertEqual(self.documents["seed"]["accounting"]["selector_derived_coordinates"], 512)
        self.assertEqual(self.documents["seed"]["accounting"]["defined_d11_selector_functions_in_math"], 512)
        self.assertEqual(self.documents["seed"]["accounting"]["independently_ratified_selector_primitive_laws"], 0)
        self.assertEqual(self.documents["seed"]["accounting"]["derived_selectors_without_direct_opcode_admission"], 512)
        self.assertEqual(report["selector_parents"], 256)
        self.assertEqual(report["unique_coordinates"], 512)
        self.assertEqual(report["unique_names"], 512)
        self.assertEqual(report["testing_only_rows"], 43)
        self.assertEqual(report["derived_testing_coordinate_collisions"], 0)
        self.assertEqual(report["derived_testing_name_collisions"], 0)
        self.assertEqual(report["callable_admissions_added"], 0)
        self.assertEqual(report["ratified_residents_added"], 0)

    def test_historical_pin_drift_is_reported_after_all_parents_are_revalidated(self):
        report = MOD.validate_documents(self.documents)
        self.assertFalse(report["historical_pin_matches_current"])
        self.assertIn("all 256 derived parents revalidated", report["source_pin_note"])

    def test_current_d11_table_has_512_derived_and_43_legacy_rows_stay_archived(self):
        report = MOD.validate_documents(self.documents)
        self.assertEqual(report["derived_count"], 512)
        self.assertEqual(report["testing_only_rows"], 43)
        self.assertEqual(self.documents["seed"]["accounting"]["new_ratified_residents"], 0)
        self.assertEqual(self.documents["seed"]["accounting"]["callable"], 0)

    def test_rejects_attempt_to_make_derived_a_research_derived_or_new_primitive(self):
        docs = self.changed()
        docs["seed"]["law"]["derived_by_law"] = False
        self.assert_rejected(docs, "DERIVED_LAW")

        docs = self.changed()
        docs["seed"]["law"]["opcode_admission"] = "ALLOW_NEW_DIRECT_OPCODE"
        self.assert_rejected(docs, "OPCODE_ADMISSION")

    def test_rejects_truncated_ten_bit_derived(self):
        docs = self.changed()
        docs["seed"]["rows"][0][0] = docs["seed"]["rows"][0][0][:-1]
        self.assert_rejected(docs, "DERIVED_WIDTH")

    def test_rejects_duplicate_derived_coordinate(self):
        docs = self.changed()
        docs["seed"]["rows"][1][0] = docs["seed"]["rows"][0][0]
        self.assert_rejected(docs, "DERIVED_DUP_COORD")

    def test_rejects_duplicate_derived_name(self):
        docs = self.changed()
        docs["seed"]["rows"][1][1] = docs["seed"]["rows"][0][1]
        self.assert_rejected(docs, "DERIVED_DUP_NAME")

    def test_rejects_d11_projection_drift_in_every_surface(self):
        row = next(line for line in self.documents["d11_table"].splitlines()
                   if line.startswith("  (01100000000 "))
        for column in ("ук", "укр", "san", "en"):
            with self.subTest(column=column):
                docs = self.changed()
                import re
                damaged = re.sub(r"(\(" + column + r"\s+)[^()\s]+",
                                 r"\1wrong-projection", row, count=1)
                self.assertNotEqual(damaged, row)
                docs["d11_table"] = docs["d11_table"].replace(row, damaged, 1)
                self.assert_rejected(docs, "D11_TABLE_PROJECTION")

        docs = self.changed()
        damaged = row.replace("(sym ())", "(sym +)", 1)
        self.assertNotEqual(damaged, row)
        docs["d11_table"] = docs["d11_table"].replace(row, damaged, 1)
        self.assert_rejected(docs, "D11_TABLE_PROJECTION")

    def test_rejects_d11_projection_column_order_and_duplicate(self):
        row = next(line for line in self.documents["d11_table"].splitlines()
                   if line.startswith("  (01100000000 "))
        for damaged in (
            row.replace("(ук ", "(tmp ", 1).replace("(укр ", "(ук ", 1).replace("(tmp ", "(укр ", 1),
            row.replace("(san ", "(uk ", 1),
            row.replace("(sym ())", "(sym ()) (sym ())", 1),
        ):
            with self.subTest(damaged=damaged[:100]):
                self.assertNotEqual(damaged, row)
                docs = self.changed()
                docs["d11_table"] = docs["d11_table"].replace(row, damaged, 1)
                self.assert_rejected(docs, "D11_TABLE_PROJECTION")

    def test_rejects_current_d11_table_coordinate_drift(self):
        docs = self.changed()
        self.assertIn("  (01100000000 (ук ", docs["d11_table"])
        docs["d11_table"] = docs["d11_table"].replace(
            "  (01100000000 (ук ", "  (00000000000 (ук ", 1)
        self.assert_rejected(docs, "D11_TABLE_DERIVATION")

    def test_rejects_current_d11_table_name_drift(self):
        docs = self.changed()
        self.assertIn("(LISP CDAAAAAAAAR)", docs["d11_table"])
        docs["d11_table"] = docs["d11_table"].replace(
            "(LISP CDAAAAAAAAR)", "(LISP WRONGSELECTOR)", 1)
        self.assert_rejected(docs, "D11_TABLE_DERIVATION")


    def test_archived_coordinate_overlap_is_accounted_not_forbidden(self):
        docs = self.changed()
        docs["d11_vocabulary"]["table"][0]["bits"] = docs["seed"]["rows"][0][0]
        self.assert_rejected(docs, "ACCOUNTING")
        docs["seed"]["accounting"]["test_coordinate_collisions"] = 1
        docs["seed"]["accounting"]["coordinates_outside_testing_and_derived_selectors"] += 1
        report = MOD.validate_documents(docs)
        self.assertEqual(report["derived_testing_coordinate_collisions"], 1)

    def test_archived_name_overlap_is_accounted_not_forbidden(self):
        docs = self.changed()
        docs["d11_vocabulary"]["table"][0]["lisp"] = docs["seed"]["rows"][0][1]
        self.assert_rejected(docs, "ACCOUNTING")
        docs["seed"]["accounting"]["test_name_collisions"] = 1
        report = MOD.validate_documents(docs)
        self.assertEqual(report["derived_testing_name_collisions"], 1)

    def test_rejects_wrong_selector_suffix_name(self):
        docs = self.changed()
        bits, name = docs["seed"]["rows"][0]
        docs["seed"]["rows"][0][1] = "NOT-A-SELECTOR-NAME"
        self.assert_rejected(docs, "DERIVED_NAME_DERIVATION")

    def test_rejects_derived_without_a_current_d10_selector_parent(self):
        docs = self.changed()
        bits, name = docs["seed"]["rows"][0]
        docs["seed"]["rows"][0][0] = "11111111111"
        self.assert_rejected(docs, "DERIVED_PARENT")

    def test_rejects_accidental_d11_ratification_or_callability(self):
        docs = self.changed()
        docs["seed"]["status"] = "RATIFIED"
        self.assert_rejected(docs, "NOT_MATHEMATICAL_DERIVATION")

        docs = self.changed()
        docs["seed"]["accounting"]["callable"] = 512
        self.assert_rejected(docs, "ACCOUNTING")

    def test_rejects_missing_child_pair(self):
        docs = self.changed()
        docs["seed"]["rows"].pop()
        self.assert_rejected(docs, "DERIVED_COUNT")


if __name__ == "__main__":
    unittest.main()
