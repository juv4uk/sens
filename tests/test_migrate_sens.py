#!/usr/bin/env python3
"""Operational CLI contract: real migration, physical bytes, SHA, dry-run, blockers."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/migrate-sens.py"
FIXTURE = "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
EXPECTED = ROOT / "tests/fixtures/migration-d1-cond-cohort/branch.sens"

spec = importlib.util.spec_from_file_location("sens_migration_cli", CLI)
assert spec and spec.loader
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


class OperationalMigrationTests(unittest.TestCase):
    def args(self, out: Path, report: Path, *extras: str) -> list[str]:
        return [sys.executable, str(CLI), "--root", str(ROOT),
                "--source", FIXTURE, "--out", str(out),
                "--report", str(report), *extras]

    def test_pin_manifest_is_real_sha_and_rejects_escape_or_duplicates(self):
        pinned = runner.pin_sources([FIXTURE], ROOT)["files"]
        self.assertEqual(len(pinned), 1)
        self.assertEqual(pinned[0]["path"], FIXTURE)
        import hashlib
        self.assertEqual(pinned[0]["sha256"], hashlib.sha256(
            (ROOT / FIXTURE).read_bytes()).hexdigest())
        for paths in ([FIXTURE, FIXTURE], ["../outside.lisp"],
                      ["/tmp/escape.lisp"], ["tests/fixtures/nonexistent.lisp"],
                      ["tests/fixtures/migration-d1-cond-cohort/branch.sens"]):
            with self.subTest(paths=paths), self.assertRaises(runner.MigrationBlocked):
                runner.pin_sources(paths, ROOT)

    def test_migrator_is_real_physical_t5_and_repeat_is_no_clobber(self):
        with tempfile.TemporaryDirectory(prefix="sens-operational-") as tmp:
            temp = Path(tmp)
            out = temp / "out"
            report = temp / "report.json"
            dry = subprocess.run(self.args(out, report, "--dry-run"),
                                 cwd=temp, capture_output=True, text=True)
            self.assertEqual(dry.returncode, 0, dry.stdout + dry.stderr)
            self.assertFalse((out / "tests/fixtures/migration-d1-cond-cohort/branch.sens").exists())
            dry_report = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(dry_report["summary"]["files_ready"], 1)
            self.assertEqual(dry_report["summary"]["published"], 0)

            run = subprocess.run(self.args(out, report),
                                 cwd=temp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            target = out / "tests/fixtures/migration-d1-cond-cohort/branch.sens"
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(), EXPECTED.read_bytes())
            self.assertNotEqual(target.read_bytes(), (ROOT / FIXTURE).read_bytes())
            record = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(record["summary"]["published"], 1)
            self.assertEqual(runner.verify_published(record, out, False), 1)
            self.assertTrue((ROOT / FIXTURE).is_file())

            second = subprocess.run(self.args(out, report),
                                    cwd=temp, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2, second.stdout + second.stderr)
            self.assertEqual(target.read_bytes(), EXPECTED.read_bytes())

    def test_verifier_fails_closed_on_tampered_bytes(self):
        with tempfile.TemporaryDirectory(prefix="sens-corrupt-") as tmp:
            out = Path(tmp) / "out"
            report = Path(tmp) / "report.json"
            run = subprocess.run(self.args(out, report),
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            target = out / "tests/fixtures/migration-d1-cond-cohort/branch.sens"
            target.write_bytes(target.read_bytes() + bytes([243]))
            with self.assertRaises((runner.MigrationBlocked, ValueError)):
                runner.verify_published(json.loads(report.read_text()), out, False)

    def test_manifest_paths_always_receive_content_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "approved.json"
            manifest.write_text(json.dumps({"files": [FIXTURE]}), encoding="utf-8")
            pinned = runner.pin_manifest(manifest, ROOT)
            self.assertEqual(pinned, runner.pin_sources([FIXTURE], ROOT))
            manifest.write_text(json.dumps(pinned), encoding="utf-8")
            self.assertEqual(runner.pin_manifest(manifest, ROOT), pinned)

    def test_manifest_rejects_stale_sha_and_untrusted_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "approved.json"
            cases = [
                {"files": [{"path": FIXTURE, "sha256": "0" * 64}]},
                {"files": [{"path": FIXTURE, "sha256": "not-a-hash"}]},
                {"files": [FIXTURE, FIXTURE]},
                {"files": ["../escape.lisp"]},
                {"files": ["/tmp/escape.lisp"]},
                {"files": [FIXTURE.replace(".lisp", ".sens")]},
                {"files": [{"path": FIXTURE, "unsafe": True}]},
                {"files": []},
                {"files": {"path": FIXTURE}},
            ]
            for value in cases:
                with self.subTest(value=value):
                    manifest.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaises(runner.MigrationBlocked):
                        runner.pin_manifest(manifest, ROOT)

    def test_actual_manifest_cli_and_two_source_atomic_dry_run(self):
        other = "tests/fixtures/core1-third-domain-canary/third.lisp"
        with tempfile.TemporaryDirectory(prefix="sens-manifest-") as tmp:
            t = Path(tmp)
            approved = t / "approved.json"
            out, report = t / "out", t / "report.json"
            approved.write_text(json.dumps({"files": [FIXTURE, other]}), encoding="utf-8")
            command = [
                sys.executable, str(CLI), "--root", str(ROOT),
                "--manifest", str(approved), "--out", str(out),
                "--report", str(report), "--dry-run", "--source-era", "legacy",
            ]
            result = subprocess.run(command, cwd=t, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(evidence["summary"]["files_requested"], 2)
            self.assertEqual(evidence["summary"]["files_ready"], 2)
            self.assertEqual(evidence["summary"]["published"], 0)
            self.assertEqual(len(list(out.rglob("*.sens"))) if out.exists() else 0, 0)
            # Change the expected source digest: no transaction is attempted,
            # and no target can be silently created.
            approved.write_text(json.dumps({"files": [
                {"path": FIXTURE, "sha256": "0" * 64}, other
            ]}), encoding="utf-8")
            report.unlink()
            blocked = subprocess.run(command, cwd=t, capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertIn("BLOCKED", blocked.stderr)
            self.assertFalse(report.exists())

    def test_real_w8_auto_blocks_but_explicit_legacy_is_exact_physical_t5(self):
        real = "tests/fixtures/core1-third-domain-canary/third.lisp"
        expected = ROOT / real.replace(".lisp", ".sens")
        with tempfile.TemporaryDirectory(prefix="sens-w8-era-") as tmp:
            t = Path(tmp)
            out, report = t / "binary", t / "report.json"
            cmd = [sys.executable, str(CLI), "--root", str(ROOT),
                   "--source", real, "--out", str(out), "--report", str(report)]
            blocked = subprocess.run(cmd, cwd=t, capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertFalse((out / real.replace(".lisp", ".sens")).exists())
            self.assertEqual(json.loads(report.read_text())["source_era"], "auto")
            accepted = subprocess.run(cmd + ["--source-era", "legacy"],
                                      cwd=t, capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            self.assertEqual((out / real.replace(".lisp", ".sens")).read_bytes(),
                             expected.read_bytes())
            self.assertEqual(json.loads(report.read_text())["source_era"], "legacy")

    def test_outside_root_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.json"
            self.assertEqual(runner.main(["--source", FIXTURE, "--out", str(ROOT),
                                          "--report", str(report)]), 2)


    def test_manifest_pins_and_vetoes_all_four_nonprogram_families(self):
        known = [
            "lib/machine/isa/adx.lisp",
            "contracts/bija3-l1-l5-ratification.lisp",
            "evidence/G5/my-lisp/196d7f2.lisp",
            "tests/fixtures/canon-laws-v2-witness.lisp",
        ]
        records = runner._nonprogram_manifest_paths(ROOT)
        for name in known:
            with self.subTest(source=name):
                source = ROOT / name
                self.assertTrue(source.is_file())
                self.assertEqual(
                    runner._git_blob_sha(source.read_bytes()), records[name],
                    f"manifest source drift for {name}"
                )
                with self.assertRaisesRegex(runner.MigrationBlocked, "NONPROGRAM"):
                    runner.pin_sources([name], ROOT)
        self.assertEqual(
            runner._git_blob_sha(b"hello\\n"),
            "ce013625030ba8dba906f756967f9e9ca394464a"
        )

    def test_archived_print_snapshot_not_executable_even_if_mechanically_convertible(self):
        historical = ("benchmarks/sens-surface/results/"
                      "20260925-icount-33bfb53a/programs/empty-en.lisp")
        original = ROOT / historical
        self.assertEqual(original.read_bytes(), b"(print 0)\\n")
        self.assertEqual(
            runner._git_blob_sha(original.read_bytes()),
            "6e30e07f9a44391fb341f5e0ff21ba1e682b5d0f",
        )
        with self.assertRaisesRegex(runner.MigrationBlocked, "archived benchmark"):
            runner.pin_sources([historical], ROOT)
        # The archive output fence must not prevent unrelated active programs.
        self.assertTrue(runner.pin_sources(["benchmarks/arithmetic.lisp"], ROOT)["files"])

    def test_mixed_original_manifest_aborts_before_any_publication(self):
        old_data = "lib/machine/isa/adx.lisp"
        with tempfile.TemporaryDirectory(prefix="sens-nonprogram-veto-") as tmp:
            t = Path(tmp)
            manifest = t / "selected.json"
            manifest.write_text(json.dumps({"files": [FIXTURE, old_data]}))
            out, report = t / "physical", t / "report.json"
            proc = subprocess.run([
                sys.executable, str(CLI), "--root", str(ROOT),
                "--manifest", str(manifest), "--out", str(out),
                "--report", str(report), "--source-era", "legacy"
            ], capture_output=True, text=True, cwd=t)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("NONPROGRAM", proc.stderr)
            self.assertFalse(report.exists())
            self.assertFalse(out.exists())
            self.assertFalse((ROOT / old_data).with_suffix(".sens").exists())

    def test_manifest_source_drift_is_never_silently_reclassified_executable(self):
        with unittest.mock.patch.object(runner, "_git_blob_sha", return_value="0"*40):
            with self.assertRaisesRegex(runner.MigrationBlocked,
                                        "NONPROGRAM source authority drift"):
                runner.pin_sources(["lib/machine/isa/adx.lisp"], ROOT)

    def test_known_active_core1_binary_remains_allowed_for_publication(self):
        selected = runner.pin_sources([FIXTURE], ROOT)
        self.assertEqual(selected["files"][0]["path"], FIXTURE)



if __name__ == "__main__":
    unittest.main()
