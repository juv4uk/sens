from __future__ import annotations

import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSURE = ROOT / "benchmarks" / "d6-closure-map" / "run.py"
FORECAST = ROOT / "scripts" / "research-2322-generative-domain-forecast.py"
RATIFIED = ROOT / "knowledge" / "d6-ratified.json"


class CurrentD6ClosureAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.closure_ns = runpy.run_path(str(CLOSURE))
        cls.rows = cls.closure_ns["build_map"]()
        cls.ratified = json.loads(RATIFIED.read_text(encoding="utf-8"))
        cls.forecast_ns = runpy.run_path(str(FORECAST))

    def test_all_64_residents_match_owner_ratification(self) -> None:
        expected = self.ratified["residents"]
        actual = {row["coordinate"]: row["resident"] for row in self.rows}
        self.assertEqual(len(self.rows), 64)
        self.assertEqual(actual, expected)
        self.assertEqual(len(set(actual.values())), 64)
        self.assertTrue(all(row["semantic_member_of_ratified_domain"] for row in self.rows))
        self.assertEqual(sum(row["status"] == "UNKNOWN/free" for row in self.rows), 0)

    def test_current_selector_closure_matches_forecast_and_ratified_names(self) -> None:
        selectors = {
            row["coordinate"]: row
            for row in self.rows
            if row["status"] == "generated"
        }
        expected = set(self.forecast_ns["current_selector_words"](6))
        self.assertEqual(set(selectors), expected)
        self.assertEqual(len(selectors), 16)
        self.assertTrue(all(coord.startswith(("011", "100")) for coord in selectors))
        for coordinate, row in selectors.items():
            self.assertEqual(row["resident"], self.ratified["residents"][coordinate])
            self.assertEqual(row["resident"], row["display_name"])

    def test_remaining_residents_are_not_misclassified_as_vacant(self) -> None:
        other = [row for row in self.rows if row["status"] == "owner-ratified-other-resident"]
        self.assertEqual(len(other), 48)
        self.assertTrue(all(row["resident_authority"] == "#3393" for row in other))
        self.assertTrue(all(row["semantic_member_of_ratified_domain"] for row in other))


if __name__ == "__main__":
    unittest.main()
