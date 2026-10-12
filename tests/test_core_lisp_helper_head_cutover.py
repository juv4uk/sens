#!/usr/bin/env python3
"""Доказ вузького міграційного зрізу: внутрішні функції Core — не нові D8."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core.lisp"
OLD_BLOB = "fd5f087f90d916a6c6d7d005170fe754f13854d8"
REWRITES = (
    ("(00011111 ", "(nondecreasing-from? ", 3),
    ("(00100000 ", "(nonincreasing-from? ", 3),
)


def original_source() -> str:
    raw = subprocess.run(
        ["git", "cat-file", "blob", OLD_BLOB],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if sha != OLD_BLOB:
        raise ValueError("PIN_DRIFT: вихідний Git blob не збігається")
    return raw.decode("utf-8")


def expected_source() -> str:
    src = original_source()
    for old, new, count in REWRITES:
        if src.count(old) != count:
            raise ValueError("PIN_DRIFT: змінено кількість історичних викличних голів")
        src = src.replace(old, new)
    return src


def assert_exact_migration(src: str) -> None:
    if src != expected_source():
        raise ValueError("SOURCE_DELTA_BLOCK: дозволено тільки шість замін голів")


class CoreHelperCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SOURCE.read_text(encoding="utf-8")

    def test_six_exact_changes_no_other_source_rewrites(self):
        assert_exact_migration(self.src)
        for old, new, _ in REWRITES:
            self.assertNotIn(old, self.src)
            self.assertGreaterEqual(self.src.count(new), 3)

    def test_helper_definitions_remain_ordinary_lisp_owned_functions(self):
        for name in ("nondecreasing-from?", "nonincreasing-from?"):
            self.assertEqual(
                len(re.findall(r"(?m)^\(0011\s+" + re.escape(name) + r"\s*$", self.src)),
                1,
                f"{name}: рівно одне власне визначення",
            )
        self.assertIn("(0011 <=", self.src)
        self.assertIn("(0011 >=", self.src)

    def test_provenance_classifies_old_slots_as_internal_not_domains(self):
        data = json.loads(
            (ROOT / "knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8")
        )
        rows = {row["legacy_code"]: row for row in data["rows"]}
        for bits, name in (("00011111", "nondecreasing-from?"),
                           ("00100000", "nonincreasing-from?")):
            row = rows[bits]
            self.assertEqual(row["classification"], "INTERNAL-NO-SEMANTIC-SLOT")
            self.assertIsNone(row["current_target"])
            self.assertEqual(row["legacy_name"], name)

    def test_reintroduced_historical_executable_head_rejected(self):
        corrupted = self.src.replace("(nondecreasing-from? (100 remaining)",
                                      "(00011111 (100 remaining)", 1)
        self.assertNotEqual(corrupted, self.src)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            assert_exact_migration(corrupted)

    def test_quoted_or_unrelated_form_mutation_rejected(self):
        corrupted = self.src.replace("(0011 quotient", "(0011 altered-quotient", 1)
        self.assertNotEqual(corrupted, self.src)
        with self.assertRaisesRegex(ValueError, "SOURCE_DELTA_BLOCK"):
            assert_exact_migration(corrupted)


if __name__ == "__main__":
    unittest.main()
