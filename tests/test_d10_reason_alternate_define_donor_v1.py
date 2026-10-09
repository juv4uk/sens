"""Adversarial source-era evidence checks: research not selected D10."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/check_d10_reason_alternate_define_donor_v1.py"
spec = importlib.util.spec_from_file_location("d10_reason_audit", path)
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class D10ReasonAlternateDefine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = audit.read(audit.LEDGER)
        cls.raw = audit.SOURCE.read_bytes()
        cls.inventory = audit.read(audit.INVENTORY)
        cls.state = audit.read(audit.STATE)
        cls.canonical = audit.read(audit.CANONICAL)
        cls.existing = audit.read(audit.RAW_EXISTING)
        cls.d9 = audit.read(audit.D9)

    def verify(self, *, ledger=None, raw=None, inventory=None, state=None,
               canonical=None, existing=None, d9=None):
        return audit.verify(
            self.ledger if ledger is None else ledger,
            self.raw if raw is None else raw,
            self.inventory if inventory is None else inventory,
            self.state if state is None else state,
            self.canonical if canonical is None else canonical,
            self.existing if existing is None else existing,
            self.d9 if d9 is None else d9,
        )

    def test_exact_37_historical_definitions_and_zero_admissions(self):
        result = self.verify()
        self.assertEqual(result["historical_source_defs"], 37)
        self.assertEqual(result["already_selected_names_not_promoted"], 6)
        self.assertEqual(result["needs_behavioral_dedup"], 26)
        self.assertEqual(result["unreviewed_d9_name_collisions"], 7)
        self.assertEqual(result["unreviewed_without_exact_d9_name_match"], 19)
        self.assertEqual(
            {x["source_name"]: x["existing_coordinate"]
             for x in result["unreviewed_d9_name_collision_witnesses"]},
            {"reason": "101001110", "prove-goal": "101011011",
             "prove-goals": "101010001", "explain-proof": "101001011",
             "reason-explain": "101100111", "source-of": "101110000",
             "provenance": "101101111"},
        )
        self.assertTrue(all(
            x["review"] == "NAME_COLLISION_BEHAVIOR_UNPROVEN"
            and x["new_d10_resident"] is False
            for x in result["unreviewed_d9_name_collision_witnesses"]
        ))
        self.assertEqual(result["selected_added"], 0)
        self.assertEqual(result["original_executable_t5_migrations"], 0)

    def test_different_source_byte_or_location_rejected(self):
        with self.assertRaisesRegex(ValueError, "source bytes/SHA"):
            self.verify(raw=self.raw + b" ")
        altered = copy.deepcopy(self.ledger)
        altered["rows"][0]["line"] += 1
        with self.assertRaisesRegex(ValueError, "donor mismatch"):
            self.verify(ledger=altered)

    def test_forged_resident_or_coordinate_rejected(self):
        for edit in ({"ratified": True}, {"coordinate": "0000000001"},
                     {"semantic_law_verified": True}, {"head": "1111"}):
            with self.subTest(edit=edit):
                altered = copy.deepcopy(self.ledger)
                altered["rows"][2].update(edit)
                with self.assertRaisesRegex(ValueError, "donor mismatch"):
                    self.verify(ledger=altered)

    def test_promoted_selected_count_and_replaced_canonical_laws_rejected(self):
        state = copy.deepcopy(self.state)
        state["target"]["ratified_residents"] = 1
        with self.assertRaisesRegex(ValueError, "selected D10 accounting"):
            self.verify(state=state)
        canonical = copy.deepcopy(self.canonical)
        canonical["rows"].pop()
        with self.assertRaisesRegex(ValueError, "39 reviewed"):
            self.verify(canonical=canonical)

    def test_selected_duplicate_not_exchanged_for_new_law(self):
        altered = copy.deepcopy(self.ledger)
        selected = next(x for x in altered["rows"]
                        if x["classification"] == "ALREADY_SELECTED_NAME")
        selected["classification"] = "RESEARCH_UNREVIEWED"
        with self.assertRaisesRegex(ValueError, "donor mismatch"):
            self.verify(ledger=altered)


    def test_d9_unratified_or_duplicate_name_authority_is_blocked(self):
        altered = copy.deepcopy(self.d9)
        altered["status"] = "research"
        with self.assertRaisesRegex(ValueError, "normative D9 duplicate authority"):
            self.verify(d9=altered)
        altered = copy.deepcopy(self.d9)
        altered["residents"]["111111111"] = altered["residents"]["101001110"]
        with self.assertRaisesRegex(ValueError, "D9 normalized name collision"):
            self.verify(d9=altered)

    def test_d9_name_only_collision_is_not_semantic_equivalence(self):
        altered = copy.deepcopy(self.d9)
        altered["residents"]["101001110"] = "HISTORICAL-DIFFERENT-NAME"
        result = self.verify(d9=altered)
        self.assertEqual(result["unreviewed_d9_name_collisions"], 6)
        self.assertEqual(result["unreviewed_without_exact_d9_name_match"], 20)
        self.assertEqual(result["selected_added"], 0)
        self.assertEqual(result["ratified_added"], 0)

    def test_d9_corrupt_width_and_coverage_block(self):
        altered = copy.deepcopy(self.d9)
        value = altered["residents"].pop("101001110")
        altered["residents"]["1010011100"] = value
        with self.assertRaisesRegex(ValueError, "D9 resident width or coverage"):
            self.verify(d9=altered)
        altered = copy.deepcopy(self.d9)
        altered["occupancy"] = 511
        with self.assertRaisesRegex(ValueError, "normative D9 duplicate authority"):
            self.verify(d9=altered)



if __name__ == "__main__":
    unittest.main()
