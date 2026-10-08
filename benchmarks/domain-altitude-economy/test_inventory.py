from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("d8_inventory", HERE / "inventory.py")
assert SPEC and SPEC.loader
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class D8InventoryTests(unittest.TestCase):
    def test_current_authority_yields_strict_bounded_candidate_set(self):
        repo = HERE.parents[1]
        report = inventory.build_inventory(
            json.loads((repo / "knowledge/d8-ratified.json").read_text(encoding="utf-8")),
            json.loads(
                (repo / "knowledge/d8-v2-semantic-inventory.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        self.assertEqual(report["candidate_count"], 22)
        self.assertEqual(report["dividend_ready_count"], 0)
        names = {row["resident"] for row in report["candidates"]}
        for expected in {"EQUAL", "MINUSP", "ONEP", "PAIR", "AND", "OR"}:
            self.assertIn(expected, names)

    def test_no_unrestricted_row_is_selected_by_default(self):
        ratified = {
            "rows": [
                {"resident": f"R{i}", "coordinate": f"{i:08b}"}
                for i in range(256)
            ]
        }
        semantic = {
            "rows": [
                {
                    "resident": f"R{i}",
                    "derivability": "UNRESTRICTED-BY-RESIDENCY",
                    "lower_domain_comparison": "No exact lower-domain duplicate established.",
                }
                for i in range(256)
            ]
        }
        report = inventory.build_inventory(ratified, semantic)
        self.assertEqual(report["candidate_count"], 0)


if __name__ == "__main__":
    unittest.main()
