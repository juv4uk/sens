#!/usr/bin/env python3
"""Регресійні тести fail-closed для історичного сканера COND (#5029)."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "cond-modernize.py"

LEGACY = """(00000111
  ((00000011 x y) (0) (00000001 no-branch))
  ((00000010 x) (1) (00000001 yes-branch)))
"""


class CondModernizeGuardTests(unittest.TestCase):
    def run_scanner(self, root: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_yes_and_no_never_rewrite_source_or_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = root / "legacy.lisp"
            source.write_text(LEGACY, encoding="utf-8")
            stage = root / "stage"
            for extra in ((), ("--out", str(stage))):
                with self.subTest(extra=extra):
                    run = self.run_scanner(root, str(source), *extra)
                    self.assertEqual(run.returncode, 4, run.stdout + run.stderr)
                    self.assertIn("BLOCK:", run.stdout)
                    self.assertEqual(source.read_bytes(), LEGACY.encode("utf-8"))
                    self.assertFalse(stage.exists(), "No preview artifact is authorized")

    def test_unrecognized_patterns_never_get_false_green(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = root / "other.lisp"
            original = '; (00000111 ((00000011 x y) (0) (00000001 quoted)))\n"not executable"\n'
            source.write_text(original, encoding="utf-8")
            run = self.run_scanner(root, str(source))
            self.assertEqual(run.returncode, 4, run.stdout + run.stderr)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_scan_remains_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            library = root / "lib"
            library.mkdir()
            source = library / "legacy.lisp"
            source.write_text(LEGACY, encoding="utf-8")
            run = self.run_scanner(root, "--scan")
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("# файлів зі старими cond-клаузами: 1", run.stdout)
            self.assertEqual(source.read_text(encoding="utf-8"), LEGACY)


if __name__ == "__main__":
    unittest.main()
