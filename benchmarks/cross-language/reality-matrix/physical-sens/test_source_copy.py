"""Перевірки source-to-result baseline для SENS T5 та Python."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from source_copy_bench import check_parity, p95, python_command


ROOT = Path(__file__).resolve().parents[4]
PYTHON_SOURCE = Path(__file__).parent / "fixtures" / "recursive_pair_copy.py"


class SourceCopyBenchmarkTests(unittest.TestCase):
    def test_python_source_recursively_copies_pair_list_to_exact_observable(self):
        completed = subprocess.run(
            python_command(PYTHON_SOURCE),
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        self.assertEqual(completed.stdout, "(1 0 ())\n")

    def test_parity_gate_admits_only_identical_nonempty_observables(self):
        self.assertTrue(check_parity("(1 0 ())\n", "(1 0 ())\n"))
        self.assertFalse(check_parity("(1 0 ())\n", "(1 1 ())\n"))
        self.assertFalse(check_parity("", ""))

    def test_p95_uses_nearest_rank_not_interpolation(self):
        self.assertEqual(p95(list(range(1, 21))), 19)


if __name__ == "__main__":
    unittest.main()
