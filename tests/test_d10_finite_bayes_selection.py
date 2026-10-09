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
        self.assertEqual(result["selected"], 635)
        self.assertEqual(result["unplaced"], 379)
        self.assertEqual(result["remaining"], 389)
        self.assertEqual(result["ratified"], 0)
        self.assertIsNone(result["coordinate"])

    def test_eight_fail_closed_controls(self):
        G.self_test(self.inv, self.state, self.foundation, self.dossier, self.ledger, self.history)

    def test_old_donor_dossier_remains_immutable_proposal_evidence(self):
        self.assertFalse(self.dossier["selected"])
        self.assertFalse(self.dossier["ratified"])
        self.assertIsNone(self.dossier["coordinate"])
        row = next(r for r in self.inv["rows"] if r["stable_id"] == G.STABLE_ID)
        self.assertEqual(row["positive_witnesses"], self.dossier["witnesses"])
        self.assertIn("PENDING-OWNER-REVIEW", row["derivability_review"])

if __name__ == "__main__":
    unittest.main()
