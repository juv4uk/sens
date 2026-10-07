#!/usr/bin/env python3
"""Correctness tests for shared corpus — no Valgrind required."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from corpus import CASES, EXPECTED, python_source

HERE = Path(__file__).resolve().parent
DRIVER = HERE / "cpython_phases.py"


class CorpusCorrectness(unittest.TestCase):
    def test_all_workloads_match_expected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in CASES:
                path = root / f"{name}.py"
                path.write_text(python_source(name), encoding="utf-8")
                proc = subprocess.run(
                    [sys.executable, str(DRIVER), str(path), "full"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                got = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()][-1]
                self.assertEqual(got, EXPECTED[name], msg=name)

    def test_ready_does_not_require_print(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fib.py"
            path.write_text(python_source("fib"), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(DRIVER), str(path), "ready"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_repeat_amplifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "loop.py"
            path.write_text(python_source("loop"), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(DRIVER), str(path), "repeat", "3", "--print-result"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            got = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()][-1]
            self.assertEqual(got, EXPECTED["loop"])


if __name__ == "__main__":
    unittest.main()
