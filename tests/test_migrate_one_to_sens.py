#!/usr/bin/env python3
"""Regression for canonical one-file T5 staging, not semantic admission."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-one-to-sens.py"
PROVEN = ROOT / "tests" / "fixtures" / "migration-multiform-cohort" / "two-forms.lisp"
EXISTING = PROVEN.with_suffix(".sens")


def invoke(source: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(source), *args],
        cwd=ROOT, capture_output=True, text=True
    )


class CanonicalOneFileMigration(unittest.TestCase):
    def test_real_proven_canary_dry_run_does_not_write(self):
        before = PROVEN.read_bytes()
        result = invoke(PROVEN, "--dry-run", "--source-era", "legacy")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        state = json.loads(result.stdout)
        self.assertEqual(state["status"], "would-write")
        self.assertEqual(state["semantic_parity"], "NOT_VERIFIED")
        self.assertEqual(state["source_era"], "legacy")
        self.assertEqual(state["physical_sha256"], hashlib.sha256(EXISTING.read_bytes()).hexdigest())
        self.assertEqual(PROVEN.read_bytes(), before)

    def test_existing_target_is_never_overwritten(self):
        before = EXISTING.read_bytes()
        result = invoke(PROVEN, "--source-era", "legacy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing overwrite", result.stderr)
        self.assertEqual(EXISTING.read_bytes(), before)

    def test_real_binary_staging_agrees_with_current_canonical_three_pass(self):
        before = PROVEN.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "two-forms.sens"
            result = invoke(PROVEN, "--output", str(output), "--source-era", "legacy")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "written")
            self.assertEqual(report["semantic_parity"], "NOT_VERIFIED")
            self.assertEqual(report["source"], str(PROVEN.relative_to(ROOT)))
            self.assertEqual(report["bytes"], 14)
            self.assertEqual(output.read_bytes(), EXISTING.read_bytes())
            self.assertEqual(report["physical_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            second = invoke(PROVEN, "--output", str(output), "--source-era", "legacy")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("refusing overwrite", second.stderr)
        self.assertEqual(PROVEN.read_bytes(), before)

    def test_unknown_ukrainian_identifiers_are_not_encoded_as_fake_calls(self):
        source = ROOT / "lib" / "surface" / "ukr-acceptance.lisp"
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ukr-acceptance.sens"
            result = invoke(source, "--source-era", "legacy", "--output", str(target))
            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "blocked")
            self.assertIn("reason", report)
            self.assertFalse(target.exists())
        self.assertEqual(source.read_bytes(), before)

    def test_repository_publication_requires_separate_oracle_admission(self):
        source = ROOT / "benchmarks" / "lists.lisp"
        target = source.with_suffix(".sens")
        self.assertFalse(target.exists())
        result = invoke(source, "--source-era", "legacy")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("in-repository publication needs independent", result.stderr)
        self.assertFalse(target.exists())

    def test_peer_identity_acceptance_uses_full_current_surface_set(self):
        source = ROOT / "lib" / "surface" / "peer-identity-acceptance.lisp"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(source), "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "would-write")
        self.assertEqual(
            report["output"].replace("\\", "/"),
            "lib/surface/peer-identity-acceptance.sens",
        )
        self.assertGreater(report["bytes"], 0)
        self.assertGreater(len(report["words"]), 0)

    def test_source_outside_repository_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "outside.lisp"
            source.write_text("000\n", encoding="utf-8")
            result = invoke(source, "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside the repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
