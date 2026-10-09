import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_d10_finite_bayes_selection",
    ROOT / "scripts/check_d10_finite_bayes_selection.py",
)
assert SPEC and SPEC.loader
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)


def load(path):
    return G.load(ROOT / path)


class FiniteBayesSelectionTests(unittest.TestCase):
    def setUp(self):
        self.inv = load("knowledge/d10-v1-semantic-inventory.json")
        self.state = load("knowledge/d10-fill-v1-state.json")
        self.foundation = load("knowledge/d1-d9-foundation.json")
        self.dossier = load("knowledge/d10-finite-bayes-update-research-v1.json")
        self.ledger = (ROOT / "knowledge/d10-proposal-ledger.tsv").read_text(encoding="utf-8")
        self.history = load("knowledge/d10-selection-transition-history.json")

    def test_selected_as_unplaced_research_only(self):
        result = G.verify(self.inv, self.state, self.foundation, self.dossier, self.ledger, self.history)
        live_count = len(self.inv["rows"])
        self.assertEqual(result["historical_bayes_selected"], 635)
        self.assertEqual(result["live_selected"], live_count)
        self.assertEqual(result["unplaced"], result["unplaced"] if "unplaced" in result else live_count - 256)
        self.assertEqual(result["live_unplaced"], live_count - 256)
        self.assertEqual(result["live_remaining"], 1024 - live_count)
        self.assertEqual(result["ratified"], 0)
        self.assertIsNone(result["coordinate"])

    def test_eight_fail_closed_controls_and_growth_gate(self):
        G.self_test(self.inv, self.state, self.foundation, self.dossier, self.ledger, self.history)

    def test_old_donor_dossier_remains_immutable_proposal_evidence(self):
        self.assertFalse(self.dossier["selected"])
        self.assertFalse(self.dossier["ratified"])
        self.assertIsNone(self.dossier["coordinate"])
        row = next(r for r in self.inv["rows"] if r["stable_id"] == G.STABLE_ID)
        self.assertEqual(row["positive_witnesses"], self.dossier["witnesses"])
        self.assertIn("PENDING-OWNER-REVIEW", row["derivability_review"])

    def test_accepts_explicit_future_append_after_bayes(self):
        inv, state, history = G.synthetic_append(self.inv, self.state, self.history)
        result = G.verify(inv, state, self.foundation, self.dossier, self.ledger, history)
        self.assertEqual(result["historical_bayes_selected"], 635)
        self.assertEqual(result["live_selected"], len(self.inv["rows"]) + 1)

    def test_rejects_future_append_without_transition(self):
        inv, state, _history = G.synthetic_append(self.inv, self.state, self.history)
        with self.assertRaises(G.GateFailure):
            G.verify(inv, state, self.foundation, self.dossier, self.ledger, self.history)


if __name__ == "__main__":
    unittest.main()
