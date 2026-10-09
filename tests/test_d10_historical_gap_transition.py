#!/usr/bin/env python3
"""A historic missing-name census must allow only evidence-linked later SELECT."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_d10_historical_gap_audit as audit

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class GapSnapshotTransition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = read("knowledge/d10-historical-coverage-gap-audit-v1.json")
        cls.inventory = read("knowledge/d10-v1-semantic-inventory.json")
        cls.foundation = read("knowledge/d1-d9-foundation.json")
        cls.dialect = (ROOT / "docs/DIALECT-COMPARISON.md").read_text(encoding="utf-8")
        cls.clos = read("knowledge/d10-historical-clos-interlisp-residual-review-v1.json")

    def promote(self, name, src="knowledge/d10-historical-clos-interlisp-residual-review-v1.json"):
        r = next(x for x in self.clos["rows"] if x["historical_name"] == name)
        obj = copy.deepcopy(self.inventory)
        row = {
            "stable_id": "d10.gap-test." + name.lower(),
            "semantic_name": name,
            "source_path": src,
            "primary_url": r["historical_source"],
            "source_class": "HISTORICAL-CLOS-ROOT-REVIEW",
            "status": "SELECTED-RESEARCH-CANDIDATE",
            "proposal_status": "pending-owner-review",
            "coordinate": None, "coordinate_basis": "UNPLACED",
            "ratified_resident": False,
            "behavior": r["observable_law"],
            "positive_witnesses": [r["positive_witness"]],
            "falsifiers": [r["falsifier"]],
        }
        present = next((i for i, x in enumerate(obj["rows"]) if x["semantic_name"] == name), None)
        if present is None:
            obj["rows"].append(row)
            obj["accounting"]["selected_semantic_candidates"] += 1
            obj["accounting"]["unplaced_selected_candidates"] += 1
            obj["accounting"]["remaining_semantic_inventory"] -= 1
        else:
            obj["rows"][present] = row
        return obj

    def assert_invalid(self, inv):
        with self.assertRaises(AssertionError):
            audit.verify(self.ledger, inv, self.foundation, self.dialect)

    def test_three_clos_reviewed_laws_may_evolve_from_missing_to_selected(self):
        for name in ("REMOVE-METHOD", "CHANGE-CLASS", "FIND-METHOD"):
            with self.subTest(name=name):
                inv = self.promote(name)
                result = audit.verify(self.ledger, inv, self.foundation, self.dialect)
                self.assertEqual(result["newly_ratified"], 0)
                self.assertEqual(result["newly_selected"], 0)  # historic report, not current growth
                for key, bad in (
                    ("source_path", "unrelated.json"), ("primary_url", "https://wrong.invalid"),
                    ("coordinate", "0000000000"), ("ratified_resident", True),
                    ("proposal_status", "ratified"), ("source_class", "HOST-ONLY")
                ):
                    damaged=copy.deepcopy(inv)
                    next(x for x in damaged["rows"] if x["semantic_name"] == name)[key]=bad
                    self.assert_invalid(damaged)

    def test_other_holds_cannot_fake_selection(self):
        for forbidden in ("DYNAMIC-WIND", "COMPUTE-APPLICABLE-METHODS", "MASTERSCOPE"):
            with self.subTest(forbidden=forbidden):
                inv = copy.deepcopy(self.inventory)
                if any(x["semantic_name"] == forbidden for x in inv["rows"]):
                    continue
                inv["rows"].append({
                    "semantic_name": forbidden,
                    "source_path": "knowledge/d10-historical-clos-interlisp-residual-review-v1.json",
                    "source_class": "HISTORICAL-CLOS-ROOT-REVIEW",
                    "status": "SELECTED-RESEARCH-CANDIDATE",
                    "proposal_status": "pending-owner-review",
                    "coordinate": None, "coordinate_basis": "UNPLACED",
                    "ratified_resident": False,
                })
                self.assert_invalid(inv)

if __name__ == "__main__":
    unittest.main()
