#!/usr/bin/env python3
"""Regression: frozen historical HOLDs survive lawful D10 research selection."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_d10_clos_slot_state_history as slot_history
import check_d10_historical_clos_interlisp_review as method_history


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class HistoricalSelectionEvolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.foundation = read("knowledge/d1-d9-foundation.json")
        cls.inventory = read("knowledge/d10-v1-semantic-inventory.json")
        cls.slots = read("knowledge/d10-clos-slot-state-historical-review-v1.json")
        cls.methods = read("knowledge/d10-historical-clos-interlisp-residual-review-v1.json")

    def replay(self, name, donor, triage_field, historical_path):
        obj = copy.deepcopy(self.inventory)
        row = next(r for r in donor["rows"] if r["historical_name"] == name)
        self.assertEqual(row[triage_field], "REVIEW-SEMANTIC-CANDIDATE")
        selected = {
            "stable_id": "d10.test." + name.lower(),
            "semantic_name": name,
            "source_path": historical_path,
            "primary_url": row["primary_url"] if "primary_url" in row else row["historical_source"],
            "source_class": "HISTORICAL-CLOS-ROOT-REVIEW",
            "status": "SELECTED-RESEARCH-CANDIDATE",
            "proposal_status": "pending-owner-review",
            "coordinate": None,
            "coordinate_basis": "UNPLACED",
            "ratified_resident": False,
            "behavior": row["observable_law"],
            "positive_witnesses": [row["positive_witness"]],
            "falsifiers": [row["falsifier"]],
        }
        preexisting = [r for r in obj["rows"] if r["semantic_name"] == name]
        if preexisting:
            obj["rows"][obj["rows"].index(preexisting[0])] = selected
        else:
            obj["rows"].append(selected)
            obj["accounting"]["selected_semantic_candidates"] += 1
            obj["accounting"]["unplaced_selected_candidates"] += 1
            obj["accounting"]["remaining_semantic_inventory"] -= 1
        return obj, selected

    def test_slot_selection_is_traced_not_confused_with_duplicate(self):
        for name in ("SLOT-BOUNDP", "SLOT-MAKUNBOUND"):
            with self.subTest(name=name):
                inv, row = self.replay(name, self.slots, "triage",
                    "knowledge/d10-clos-slot-state-historical-review-v1.json")
                self.assertEqual(slot_history.verify(self.slots, self.foundation, inv)["status"], "PASS")
                for key, bad in (
                    ("source_path", "bad/donor.json"), ("primary_url", "https://wrong.example"),
                    ("coordinate", "0000000000"), ("ratified_resident", True),
                    ("status", "RATIFIED"), ("source_class", "HOST-MECHANISM"),
                    ("proposal_status", "ratified"),
                ):
                    damaged = copy.deepcopy(inv)
                    next(item for item in damaged["rows"] if item["semantic_name"] == name)[key] = bad
                    with self.subTest(name=name,corruption=key), self.assertRaises(AssertionError):
                        slot_history.verify(self.slots, self.foundation, damaged)

    def test_hold_slot_never_gains_identity(self):
        inv = copy.deepcopy(self.inventory)
        old = next(r for r in self.slots["rows"] if r["historical_name"] == "SLOT-UNBOUND")
        inv["rows"].append({
            "semantic_name": "SLOT-UNBOUND", "source_path": "knowledge/d10-clos-slot-state-historical-review-v1.json",
            "primary_url": old["primary_url"], "source_class": "HISTORICAL-CLOS-ROOT-REVIEW",
            "status": "SELECTED-RESEARCH-CANDIDATE", "proposal_status": "pending-owner-review",
            "coordinate": None, "coordinate_basis": "UNPLACED", "ratified_resident": False,
            "behavior": old["observable_law"], "positive_witnesses": [old["positive_witness"]],
            "falsifiers": [old["falsifier"]],
        })
        inv["accounting"]["selected_semantic_candidates"] += 1
        inv["accounting"]["unplaced_selected_candidates"] += 1
        inv["accounting"]["remaining_semantic_inventory"] -= 1
        with self.assertRaisesRegex(AssertionError, "Promoted historical HOLD"):
            slot_history.verify(self.slots, self.foundation, inv)

    def test_method_transition_only_for_review_semantics(self):
        inv, row = self.replay("REMOVE-METHOD", self.methods, "triage_status",
                    "knowledge/d10-historical-clos-interlisp-residual-review-v1.json")
        res = method_history.verify(self.methods, self.foundation, inv)
        self.assertEqual(res["proposals"], 9)
        for key,bad in (("source_path", "other"), ("primary_url", "https://wrong.example"),
                        ("coordinate", "0000000000"), ("ratified_resident", True),
                        ("proposal_status", "approved")):
            damaged = copy.deepcopy(inv);next(item for item in damaged["rows"] if item["semantic_name"] == "REMOVE-METHOD")[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                method_history.verify(self.methods,self.foundation,damaged)

    def test_unreviewed_method_can_never_be_promoted(self):
        inv = copy.deepcopy(self.inventory)
        old = next(r for r in self.methods["rows"] if r["historical_name"] == "ADD-METHOD")
        inv["rows"].append({
            "semantic_name": "ADD-METHOD", "source_path": "knowledge/d10-historical-clos-interlisp-residual-review-v1.json",
            "primary_url": old["historical_source"], "source_class": "HISTORICAL-CLOS-ROOT-REVIEW",
            "status": "SELECTED-RESEARCH-CANDIDATE", "proposal_status": "pending-owner-review",
            "coordinate": None, "coordinate_basis": "UNPLACED", "ratified_resident": False,
            "behavior": old["observable_law"], "positive_witnesses": [old["positive_witness"]],
            "falsifiers": [old["falsifier"]],
        })
        with self.assertRaisesRegex(ValueError, "untraced or unauthorized historical promotion"):
            method_history.verify(self.methods, self.foundation, inv)


if __name__ == "__main__":
    unittest.main()
