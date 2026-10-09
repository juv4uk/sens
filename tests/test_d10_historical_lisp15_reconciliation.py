import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "d10_historical_lisp15_reconciliation",
    ROOT / "scripts/check_d10_historical_lisp15_reconciliation.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def synthetic_transition(inventory, history):
    current = copy.deepcopy(inventory)
    row = copy.deepcopy(current["rows"][-1])
    row.update({
        "stable_id": "d10.test.append-only.v1",
        "semantic_name": "TEST-APPEND-ONLY-TRANSITION",
        "behavior": "synthetic test row for transition-reconstruction tests only",
        "source_class": "TEST-ONLY",
        "provenance": ["synthetic transition test"],
        "coordinate": None,
        "coordinate_basis": "UNPLACED",
        "ratified_resident": False,
        "status": "SELECTED-RESEARCH-CANDIDATE",
    })
    source = "knowledge/d10-test-append-only-transition.json"
    previous_blob = MODULE.git_blob(current)
    previous_count = len(current["rows"])
    current["rows"].append(row)
    current["sources"].append(source)
    current["accounting"]["selected_semantic_candidates"] += 1
    current["accounting"]["unplaced_selected_candidates"] += 1
    current["accounting"]["remaining_semantic_inventory"] -= 1
    event = {
        "id": "test.append-only.1",
        "previous_inventory_blob_sha": previous_blob,
        "resulting_inventory_blob_sha": MODULE.git_blob(current),
        "added_stable_ids": [row["stable_id"]],
        "appended_sources": [source],
        "coordinates_added": 0,
        "ratified_added": 0,
        "delta_selected": 1,
        "previous_selected": previous_count,
        "resulting_selected": previous_count + 1,
    }
    extended_history = copy.deepcopy(history)
    extended_history["transitions"].append(event)
    return current, extended_history


class HistoricalLisp15ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.review = load("knowledge/d10-historical-lisp15-reconciliation-20261009.json")
        self.foundation = load("knowledge/d1-d9-foundation.json")
        self.inventory = load("knowledge/d10-v1-semantic-inventory.json")
        self.history = load("knowledge/d10-selection-transition-history.json")

    def test_review_is_research_only_and_cross_checked(self):
        result = MODULE.verify(self.review, self.foundation, self.inventory)
        self.assertEqual(result["rows_reconciled"], 31)
        self.assertEqual(result["d10_historical_selected"], 625)
        self.assertEqual(result["d10_live_selected"], len(self.inventory["rows"]))
        self.assertEqual(result["selected_added_by_historical_audit"], 0)
        self.assertEqual(result["coordinates_added_by_historical_audit"], 0)
        self.assertEqual(result["ratifications_added_by_historical_audit"], 0)

    def test_forbids_promotion(self):
        review = copy.deepcopy(self.review)
        review["rows"][0]["selected_d10"] = True
        with self.assertRaises(ValueError):
            MODULE.verify(review, self.foundation, self.inventory)

    def test_existing_mapatoms_is_deduplicated_and_obarray_remains_hold(self):
        review = copy.deepcopy(self.review)
        row = next(x for x in review["rows"] if x["review_id"] == "L15-31")
        self.assertIn("MAPATOMS", [x["name"] for x in row["exact_selected_d10_name_matches"]])
        self.assertEqual(row["exact_name_residuals"], ["OBARRAY", "OBLIST"])
        MODULE.verify(review, self.foundation, self.inventory)

    def test_historical_snapshot_survives_proven_append_only_transition(self):
        current, history = synthetic_transition(self.inventory, self.history)
        result = MODULE.verify(self.review, self.foundation, current, history)
        self.assertEqual(result["d10_historical_selected"], 625)
        self.assertEqual(result["d10_live_selected"], len(self.inventory["rows"]) + 1)
        self.assertEqual(MODULE.git_blob(MODULE.historical_inventory_view(
            current, self.review["snapshot"]["d10_inventory_blob"], history
        )), self.review["snapshot"]["d10_inventory_blob"])

    def test_rejects_append_without_explicit_transition(self):
        current, _history = synthetic_transition(self.inventory, self.history)
        with self.assertRaises(ValueError):
            MODULE.verify(self.review, self.foundation, current, None)

    def test_rejects_mutation_of_a_historical_row_even_with_transition(self):
        current, history = synthetic_transition(self.inventory, self.history)
        current["rows"][0]["behavior"] = "changed historical behavior"
        # Recompute the event result so the only remaining failure is whether
        # reversing the append recovers the original pinned base blob.
        history["transitions"][0]["resulting_inventory_blob_sha"] = MODULE.git_blob(current)
        with self.assertRaises(ValueError):
            MODULE.verify(self.review, self.foundation, current, history)

    def test_rejects_coordinate_or_ratification_in_transition(self):
        current, history = synthetic_transition(self.inventory)
        current["rows"][-1]["coordinate"] = "1111111111"
        history["transitions"][0]["resulting_inventory_blob_sha"] = MODULE.git_blob(current)
        with self.assertRaises(ValueError):
            MODULE.verify(self.review, self.foundation, current, history)

    def test_requires_explicit_obarray_hypothesis(self):
        review = copy.deepcopy(self.review)
        review["rows"] = review["rows"][:-1]
        with self.assertRaises(ValueError):
            MODULE.verify(review, self.foundation, self.inventory)


if __name__ == "__main__":
    unittest.main()
