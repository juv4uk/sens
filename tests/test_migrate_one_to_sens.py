#!/usr/bin/env python3
"""Тести безпечного one-file T5 runner."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-one-to-sens.py"


class MigrateOneToSensTests(unittest.TestCase):
    def test_dry_run_of_existing_known_fixture_is_side_effect_free(self):
        source = ROOT / "tests" / "fixtures" / "migration-multiform-cohort" / "two-forms.lisp"
        before = source.read_bytes()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "would-write")
        self.assertEqual(report["output"].replace("\\", "/"),
                         "tests/fixtures/migration-multiform-cohort/two-forms.sens")
        self.assertEqual(source.read_bytes(), before)

    def test_existing_target_is_never_overwritten(self):
        source = ROOT / "tests" / "fixtures" / "migration-multiform-cohort" / "two-forms.lisp"
        target = ROOT / "tests" / "fixtures" / "migration-multiform-cohort" / "two-forms.sens"
        before = target.read_bytes()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing overwrite", result.stderr)
        self.assertEqual(target.read_bytes(), before)

    def test_source_outside_repo_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "outside.lisp"
            source.write_text("000\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--dry-run"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("inside the repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
