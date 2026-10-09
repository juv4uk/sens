"""Adversarial checks: research candidate cannot become a fake domain resident."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_d10_flavors_restarts_research_v1.py"
spec = importlib.util.spec_from_file_location("d10_flavors_contract", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class D10FlavorsRestartsResearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = lambda name: json.loads((ROOT / name).read_text(encoding="utf-8"))
        cls.ledger = read(mod.LEDGER)
        cls.inventory = read(mod.INVENTORY)
        cls.foundation = read(mod.FOUNDATION)

    def test_live_d1_d10_corpus_safety(self):
        result = mod.verify_contract(self.ledger, self.inventory, self.foundation)
        self.assertEqual(result["newly_ratified"], 0)
        self.assertEqual(result["proposed_outside_inventory"], 8)
        self.assertEqual(result["original_executable_t5_migrations"],
                         "NOT_ATTESTED_BY_RESEARCH")


    def test_method_query_uses_standard_precedence_not_registration_order(self):
        row = next(row for row in self.ledger["rows"]
                   if row["proposal_id"] == "D10-FR-001")
        self.assertIn("argument-precedence-order", row["semantic_law"])
        self.assertIn("registration order", row["falsifier"])
        self.assertIn("without invoking", row["semantic_law"])
        self.assertIn(
            "https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/sec_7-6-6-1-2.html",
            row["source_url"],
        )
        self.assertNotIn(
            "must yield explicit ambiguity", row["falsifier"]
        )

    def test_find_restart_is_dynamic_query_and_never_control_transfer(self):
        row = next(row for row in self.ledger["rows"]
                   if row["proposal_id"] == "D10-FR-007")
        self.assertIn("current dynamic environment", row["semantic_law"])
        self.assertIn("innermost", row["semantic_law"])
        self.assertIn("never invoke", row["semantic_law"])
        self.assertIn("dynamic extent ends", row["falsifier"])
        self.assertIn(
            "https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_find-restart.html",
            row["source_url"],
        )

    def test_standard_method_combination_plan_is_observational_and_ordered(self):
        row = next(row for row in self.ledger["rows"]
                   if row["proposal_id"] == "D10-FR-004")
        for phrase in (
            "around methods most-specific-first",
            "before methods most-specific-first",
            "primary methods most-specific-first",
            "after methods least-specific-first",
        ):
            self.assertIn(phrase, row["semantic_law"])
        self.assertIn("without invoking methods", row["semantic_law"])
        self.assertIn("missing-primary failure", row["falsifier"])

    def test_all_eight_rows_remain_unratified_and_outside_physical_admission(self):
        self.assertEqual(len(self.ledger["rows"]), 8)
        for row in self.ledger["rows"]:
            with self.subTest(proposal_id=row["proposal_id"]):
                self.assertFalse(row["ratified_resident"])
                self.assertIsNone(row["coordinate"])
                self.assertFalse(row["physical_t5_authorized"])
        self.assertEqual(self.ledger["snapshot"]["selected_main_at_authoring"], 625)
        self.assertEqual(self.ledger["snapshot"]["existing_semantic_inventory_mutated"], False)

    def test_invented_coordinate_or_physical_admission_blocks(self):
        for edit in (
            {"coordinate": "0000000000"},
            {"ratified_resident": True},
            {"physical_t5_authorized": True},
        ):
            with self.subTest(edit=edit):
                ledger = copy.deepcopy(self.ledger)
                ledger["rows"][0].update(edit)
                with self.assertRaises(AssertionError):
                    mod.verify_contract(ledger, self.inventory, self.foundation)

    def test_existing_d10_and_d1_name_reuse_blocks(self):
        for name in (
            self.inventory["rows"][0]["semantic_name"],
            "CAR",
        ):
            with self.subTest(name=name):
                ledger = copy.deepcopy(self.ledger)
                ledger["rows"][0]["semantic_name"] = name
                with self.assertRaises(AssertionError):
                    mod.verify_contract(ledger, self.inventory, self.foundation)

    def test_unreviewable_or_unknown_historical_source_blocks(self):
        for edit in ({"source_url": "https://fake.invalid/original"},
                     {"falsifier": ""}, {"triage_status": "RATIFIED"}):
            with self.subTest(edit=edit):
                ledger = copy.deepcopy(self.ledger)
                ledger["rows"][0].update(edit)
                with self.assertRaises(AssertionError):
                    mod.verify_contract(ledger, self.inventory, self.foundation)


if __name__ == "__main__":
    unittest.main()
