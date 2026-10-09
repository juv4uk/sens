#!/usr/bin/env python3
"""Current D10 machine inventory vs human Archipelago counts. No ratification."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/architecture/ARCHIPELAGO-V1.uk.md"
INV = ROOT / "knowledge/d10-v1-semantic-inventory.json"


def snapshot(doc: str) -> dict:
    part = re.search(
        r"## D10 ownership gate\s+Поточний стан:\s+\x60{3}text\s*\n(.*?)\n\x60{3}",
        doc, re.DOTALL,
    )
    if part is None:
        raise ValueError("D10 ownership gate block missing")
    text = part.group(1)
    patterns = {
        "selected": r"^\s*D10 selected\s+(\d+)/(\d+)\s*$",
        "law_forced": r"^\s*law-forced\s+(\d+)\s*$",
        "unplaced": r"^\s*unplaced\s+(\d+)\s*$",
        "remaining": r"^\s*remaining\s+(\d+)\s*$",
        "ratified": r"^\s*ratified\s+(\d+)\s*$",
    }
    result = {}
    for name, pattern in patterns.items():
        found = re.findall(pattern, text, flags=re.MULTILINE)
        if len(found) != 1:
            raise ValueError(f"missing or duplicate D10 field {name}")
        if name == "selected":
            result["selected"], result["capacity"] = map(int, found[0])
        else:
            result[name] = int(found[0])
    return result


def validate(doc: str, inventory: dict) -> None:
    actual = snapshot(doc)
    a = inventory["accounting"]
    expected = {
        "capacity": inventory["capacity"],
        "selected": a["selected_semantic_candidates"],
        "law_forced": a["law_forced_coordinates"],
        "unplaced": a["unplaced_selected_candidates"],
        "remaining": a["remaining_semantic_inventory"],
        "ratified": a["ratified_d10_residents"],
    }
    if actual != expected:
        raise ValueError(f"stale D10 Archipelago projection {actual} != {expected}")
    if inventory["width"] != 10 or expected["capacity"] != 1024:
        raise ValueError("D10 width/capacity changed")
    if expected["law_forced"] + expected["unplaced"] != expected["selected"]:
        raise ValueError("D10 placement accounting invalid")
    if expected["selected"] + expected["remaining"] != expected["capacity"]:
        raise ValueError("D10 remaining budget invalid")
    if expected["ratified"] != 0:
        raise ValueError("D10 ratification unauthorized")
    if len(inventory["rows"]) != expected["selected"]:
        raise ValueError("D10 inventory row count mismatch")
    if any(row.get("ratified_resident") is not False for row in inventory["rows"]):
        raise ValueError("D10 row secretly ratified")


class D10DocumentationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.inv = json.loads(INV.read_text(encoding="utf-8"))

    def test_live_projection_matches_machine_inventory(self):
        validate(self.doc, self.inv)

    def test_old_counts_are_rejected(self):
        for original, stale in [
            ("625/1024", "434/1024"),
            ("law-forced                256", "law-forced                257"),
            ("unplaced                  369", "unplaced                  178"),
            ("remaining                 399", "remaining                 590"),
            ("ratified                    0", "ratified                    1"),
        ]:
            with self.subTest(stale=stale):
                self.assertIn(original, self.doc)
                with self.assertRaisesRegex(ValueError, "stale D10"):
                    validate(self.doc.replace(original, stale, 1), self.inv)

    def test_corrupt_selected_rows_or_ratification_fail(self):
        broken = json.loads(json.dumps(self.inv))
        broken["rows"][0]["ratified_resident"] = True
        with self.assertRaisesRegex(ValueError, "secretly ratified"):
            validate(self.doc, broken)
        broken = json.loads(json.dumps(self.inv))
        broken["rows"].pop()
        with self.assertRaisesRegex(ValueError, "row count"):
            validate(self.doc, broken)

    def test_missing_or_duplicate_machine_projection_fails(self):
        with self.assertRaisesRegex(ValueError, "ownership gate block"):
            snapshot(self.doc.replace("## D10 ownership gate", "## Historical D10 gate", 1))
        with self.assertRaisesRegex(ValueError, "duplicate D10 field"):
            snapshot(self.doc.replace(
                "remaining                 399",
                "remaining                 399\nremaining                 399", 1,
            ))


if __name__ == "__main__":
    unittest.main()
