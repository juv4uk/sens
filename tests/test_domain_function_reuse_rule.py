"""Тест правила драбин (мінімальне відновлення після placeholder; повний: apply-debt0-test.py)."""
from __future__ import annotations
import importlib.util
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "guard-domain-function-reuse.py"
SEARCH = ROOT / "scripts" / "search-domain-function.py"
PROBE = ROOT / "lib" / "_rule_probe.lisp"

def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], cwd=ROOT,
                          capture_output=True, text=True, check=False)

class DomainFunctionReuseRule(unittest.TestCase):
    def tearDown(self) -> None:
        if PROBE.exists():
            PROBE.unlink()

    def test_guard_self_test_is_green(self) -> None:
        result = run(GUARD, "--self-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_search_self_test_is_green(self) -> None:
        result = run(SEARCH, "--self-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_explicit_missing_lisp_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing-guard-input.lisp"
            result = run(GUARD, "--file", str(missing))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("НЕ ПЕРЕВІРЕНО", result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()
