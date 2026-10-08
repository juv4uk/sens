#!/usr/bin/env python3
"""Independent source oracle for the first original T5 admission."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmarks/sens-surface/results/20260925-icount-33bfb53a/programs/empty-en.lisp"
EXPECTED = SOURCE.with_name("empty.expected")
LEDGER = ROOT / "knowledge/sens8-current-coverage-v1.json"

class PrintZeroOriginalOracle(unittest.TestCase):
    def test_source_and_expected_observation_are_pinned(self):
        self.assertEqual(SOURCE.read_text(encoding="utf-8"), "(print 0)\n")
        self.assertEqual(EXPECTED.read_text(encoding="utf-8"), "0\n")

    def test_print_successor_is_exactly_one_audited_current_target(self):
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
        rows = [row for row in data["rows"] if row.get("legacy_code") == "01001000"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["classification"], "DIRECT-CURRENT-IDENTITY")
        self.assertEqual(rows[0]["current_target"], "D8:11011011 PRINT")

    def test_existing_mylisp_executes_the_original_source(self):
        expected = EXPECTED.read_text(encoding="utf-8").strip()
        result = subprocess.run(
            ["cargo", "run", "-q", "-p", "sens-cli", "--bin", "sens",
             "--", str(SOURCE.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, timeout=180, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        self.assertTrue(lines, result.stdout)
        self.assertEqual(lines[-1], expected, result.stdout)

if __name__ == "__main__":
    unittest.main()
