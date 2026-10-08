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
