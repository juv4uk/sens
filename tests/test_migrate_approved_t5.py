#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-approved-t5.py"
CAAR = "tests/fixtures/migration-d4-selector-cohort/caar.lisp"
EXPECTED_PHYSICAL = bytes.fromhex(
    "6612c47ec47ec32da42dc32da42ea937a813b1a1"
)

class ApprovedT5MigrationTests(unittest.TestCase):
    def run_cli(self, manifest, out, report, dry_run=False):
        args = [
            sys.executable, str(SCRIPT), str(ROOT),
            "--manifest", str(manifest),
            "--out", str(out),
            "--report", str(report),
        ]
        if dry_run:
            args.append("--dry-run")
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=60)

    def test_dry_run_is_manifest_only(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            manifest = base / "manifest.json"
            out = base / "out"
            report = base / "report.json"
            manifest.write_text(json.dumps({"files": [CAAR]}), encoding="utf-8")
            run = self.run_cli(manifest, out, report, dry_run=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["files_requested"], 1)
            self.assertEqual(state["summary"]["files_ready"], 1)
            self.assertEqual(state["summary"]["files_blocked"], 0)
            self.assertEqual(state["summary"]["published"], 0)
            self.assertFalse(out.exists())

    def test_source_hash_can_be_pinned(self):
        source = ROOT / CAAR
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            manifest = base / "manifest.json"
            out = base / "out"
            report = base / "report.json"
            manifest.write_text(
                json.dumps({"files": [{"path": CAAR, "sha256": digest}]}),
                encoding="utf-8",
            )
            run = self.run_cli(manifest, out, report, dry_run=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)

    def test_blocked_member_prevents_partial_publication(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            manifest = base / "manifest.json"
            out = base / "out"
            report = base / "report.json"
            manifest.write_text(
                json.dumps({
                    "files": [
                        CAAR,
                        "tests/fixtures/migration-d4-selector-cohort/missing.lisp",
                    ]
                }),
                encoding="utf-8",
            )
            run = self.run_cli(manifest, out, report)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse(out.exists() and any(out.rglob("*.sens")))

    def test_success_publishes_physical_t5_and_rerun_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            manifest = base / "manifest.json"
            out = base / "out"
            report = base / "report.json"
            manifest.write_text(json.dumps({"files": [CAAR]}), encoding="utf-8")
            run = self.run_cli(manifest, out, report)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            target = out / "tests/fixtures/migration-d4-selector-cohort/caar.sens"
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(), EXPECTED_PHYSICAL)
            rerun = self.run_cli(manifest, out, report)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertEqual(target.read_bytes(), EXPECTED_PHYSICAL)

    def test_manifest_rejects_duplicate_entries(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            manifest = base / "manifest.json"
            out = base / "out"
            report = base / "report.json"
            manifest.write_text(json.dumps({"files": [CAAR, CAAR]}), encoding="utf-8")
            run = self.run_cli(manifest, out, report)
            self.assertNotEqual(run.returncode, 0)

if __name__ == "__main__":
    unittest.main()
