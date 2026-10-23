#!/usr/bin/env python3
"""Інструментальні тести CLI D11: не пропонувати неіснуючі селекторні координати."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "add-d11-function.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class AddD11FunctionCliTests(unittest.TestCase):
    def test_existing_selector_is_offered_with_exact_coordinate(self) -> None:
        result = run_cli("--parent", "0110000000", "--suffix", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("01100000000 → CDAAAAAAAAR", result.stdout)

    def test_nonselector_parent_is_rejected_instead_of_proposing_a_row(self) -> None:
        result = run_cli("--parent", "0000000000", "--suffix", "0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("D11_NON_SELECTOR_PARENT", result.stderr)
        self.assertIn("input=D10:0000000000", result.stderr)
        self.assertNotIn("нових рядок за законом", result.stdout)

    def test_suffix_outside_binary_law_is_rejected(self) -> None:
        result = run_cli("--parent", "0110000000", "--suffix", "2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("D11_PARENT_SUFFIX_INVALID", result.stderr)

    def test_nonbinary_parent_is_rejected(self) -> None:
        result = run_cli("--parent", "abcdefghij", "--suffix", "0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("D11_PARENT_SUFFIX_INVALID", result.stderr)


if __name__ == "__main__":
    unittest.main()
