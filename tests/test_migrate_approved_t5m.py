#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-approved-t5m.py"
CAAR = "tests/fixtures/migration-d4-selector-cohort/caar.lisp"
EXPECTED_PHYSICAL = bytes.fromhex(
    "6612c47ec47ec32da42dc32da42ea937a813b1a1"
)

class ApprovedT5MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Publication requires the real Rust reader; do not let missing
        # --reader turn negative tests into accidental successes.
        build = subprocess.run(
            ["cargo", "build", "--locked", "-p", "sens-cli", "--features", "zig-transport", "--bin", "sens-trit"],
            cwd=ROOT, capture_output=True, text=True, timeout=240,
        )
        if build.returncode != 0:
            raise AssertionError(
                "cannot build independent Rust D2 reader:\n"
                + build.stdout + build.stderr
            )

    def run_cli(self, manifest, out, report, dry_run=False):
        args = [
            sys.executable, str(SCRIPT), str(ROOT),
            "--manifest", str(manifest),
            "--out", str(out),
            "--report", str(report),
        ]
        if dry_run:
            args.append("--dry-run")
        else:
            reader_name = "sens-trit.exe" if sys.platform == "win32" else "sens-trit"
            args.extend(["--reader", str(ROOT / "target" / "debug" / reader_name)])
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=120)

    def test_approved_driver_loads_current_exact_domain_maps(self):
        """Historical SID8 succession must not be mistaken for ratified D8/D9."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("sens_approved_t5_current_test", SCRIPT)
        self.assertIsNotNone(spec)
        approved = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(approved)
        maps = approved.load_engine_maps(ROOT)
        self.assertEqual(len(maps), 3, "expected current (my, upper, text7), not retired legacy map")
        my, upper, text7 = maps
        self.assertTrue(my and upper and text7, "current domain + D7 maps must be populated")
        foundation = approved.engine.load_foundation(ROOT / "knowledge/d1-d11-foundation.json")
        for domain, width, count in (("D8", 8, 256), ("D9", 9, 512), ("D10", 10, 1024)):
            residents = foundation["domains"][domain]["residents"]
            self.assertEqual(len(residents), count)
            self.assertTrue(all(len(bits) == width and set(bits) <= {"0", "1"}
                                for bits in residents), f"{domain} exact-width coordinates")
        # A ratified resident is not proof of an admitted runtime call.

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
            self.assertEqual(state["files"][0]["physical_producer"],
                             "REFERENCE_PREVIEW_ONLY")
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

    def test_success_publishes_physical_t5m_and_rerun_refuses_overwrite(self):
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
            receipt = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(receipt["files"][0]["physical_producer"], "ZIG_ATTESTED")
            self.assertEqual(receipt["files"][0]["physical_codec"], "T5M")
            self.assertEqual(receipt["files"][0]["semantic_oracle"], "NOT_VERIFIED")
            rerun = self.run_cli(manifest, out, report)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertEqual(target.read_bytes(), EXPECTED_PHYSICAL)

    def test_zig_unavailable_never_publishes_python_reference_bytes(self):
        """Negative: a valid manifest + Rust reader cannot bypass missing Zig."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            manifest = base / "manifest.json"
            out = base / "out"
            report = base / "report.json"
            manifest.write_text(json.dumps({"files": [CAAR]}), encoding="utf-8")
            reader_name = "sens-trit.exe" if sys.platform == "win32" else "sens-trit"
            args = [
                sys.executable, str(SCRIPT), str(ROOT),
                "--manifest", str(manifest),
                "--out", str(out),
                "--report", str(report),
                "--reader", str(ROOT / "target" / "debug" / reader_name),
            ]
            missing_zig = base / "nonexistent-zig"
            result = subprocess.run(
                args, cwd=ROOT, capture_output=True, text=True, timeout=120,
                env={**os.environ, "ZIG": str(missing_zig)},
            )
            self.assertNotEqual(result.returncode, 0, "missing Zig cannot publish .sens")
            self.assertFalse(list(out.rglob("*.sens")) if out.exists() else False)
            self.assertTrue(report.is_file(), result.stderr + result.stdout)
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["published"], 0)
            self.assertIn("ZIG_CODEC_UNAVAILABLE", state["files"][-1]["reason"])

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
