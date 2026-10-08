#!/usr/bin/env python3
"""Exact physical VIEW for preexisting Ukrainian lib, never executable admission."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/surface/ukr-acceptance.lisp"
PHYSICAL = ROOT / "lib/surface/ukr-acceptance.sens"
VIEW = ROOT / "lib/surface/ukr-acceptance"


class UkrainianAcceptancePhysicalView(unittest.TestCase):
    def test_existing_ukrainian_source_and_t5_unchanged(self):
        self.assertTrue(SOURCE.is_file())
        self.assertTrue(PHYSICAL.is_file())
        self.assertEqual(PHYSICAL.stat().st_size, 72)
        self.assertIn("визначити", SOURCE.read_text(encoding="utf-8"))
        self.assertNotEqual(SOURCE.read_bytes(), PHYSICAL.read_bytes())

    def test_exact_extensionless_canonical_view_no_oracle_claim(self):
        self.assertTrue(VIEW.is_file(), "missing physical T5 extensionless view")
        self.assertFalse(VIEW.is_symlink())
        before_source = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        before_binary = hashlib.sha256(PHYSICAL.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="sens-ukr-view-") as work:
            stage = Path(work)
            command = [
                sys.executable, str(ROOT / "scripts/sens_spaced_view.py"),
                "--root", str(ROOT), "--sens", "lib/surface/ukr-acceptance.sens",
                "--stage", str(stage),
            ]
            staged = subprocess.run(command, cwd=ROOT, capture_output=True,
                                    text=True, timeout=60, check=False)
            self.assertEqual(staged.returncode, 0, staged.stderr + staged.stdout)
            expected = stage / "lib/surface/ukr-acceptance"
            self.assertEqual(VIEW.read_bytes(), expected.read_bytes())
            self.assertIn('"semantic_oracle": "NOT_VERIFIED_BY_VIEW_TOOL"', staged.stdout)
            self.assertIn('"release_admitted": false', staged.stdout)
        verified = subprocess.run([
            sys.executable, str(ROOT / "scripts/sens_spaced_view.py"),
            "--root", str(ROOT), "--sens", "lib/surface/ukr-acceptance.sens",
            "--verify",
        ], cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), before_source)
        self.assertEqual(hashlib.sha256(PHYSICAL.read_bytes()).hexdigest(), before_binary)


if __name__ == "__main__":
    unittest.main()
