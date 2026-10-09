import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "d10_historical_lisp15_reconciliation",
    ROOT / "scripts/check_d10_historical_lisp15_reconciliation.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

class HistoricalLisp15ReconciliationTests(unittest.TestCase):
    def test_review_is_research_only_and_cross_checked(self):
        result = MODULE.verify(
            load("knowledge/d10-historical-lisp15-reconciliation-20261009.json"),
            load("knowledge/d1-d9-foundation.json"),
            load("knowledge/d10-v1-semantic-inventory.json"),
        )
        self.assertEqual(result["rows"], 31)
        self.assertEqual(result["selected_added"], 0)
        self.assertEqual(result["coordinates_added"], 0)
        self.assertEqual(result["ratifications_added"], 0)

    def test_forbids_promotion(self):
        review = load("knowledge/d10-historical-lisp15-reconciliation-20261009.json")
        review["rows"][0]["selected_d10"] = True
        with self.assertRaises(ValueError):
            MODULE.verify(review, load("knowledge/d1-d9-foundation.json"),
                          load("knowledge/d10-v1-semantic-inventory.json"))

    def test_requires_explicit_obarray_hypothesis(self):
        review = load("knowledge/d10-historical-lisp15-reconciliation-20261009.json")
        review["rows"] = review["rows"][:-1]
        with self.assertRaises(ValueError):
            MODULE.verify(review, load("knowledge/d1-d9-foundation.json"),
                          load("knowledge/d10-v1-semantic-inventory.json"))

if __name__ == "__main__":
    unittest.main()
