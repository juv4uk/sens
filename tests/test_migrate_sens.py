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
            dry_receipt = json.loads(dry.stdout)
            self.assertEqual(dry_receipt["status"], "DRY_RUN_READY")
            self.assertEqual(dry_receipt["semantic_oracle"], "NOT_VERIFIED")
            self.assertFalse(dry_receipt["release_admitted"])
            self.assertFalse((out / "tests/fixtures/migration-d1-cond-cohort/branch.sens").exists())
            dry_report = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(dry_report["summary"]["files_ready"], 1)
            self.assertEqual(dry_report["summary"]["published"], 0)

            run = subprocess.run(self.args(out, report),
                                 cwd=temp, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            physical_receipt = json.loads(run.stdout)
            self.assertEqual(physical_receipt["status"], "PHYSICAL_AND_D2_VERIFIED_ORACLE_PENDING")
            self.assertEqual(physical_receipt["semantic_oracle"], "NOT_VERIFIED")
            self.assertFalse(physical_receipt["release_admitted"])
            target = out / "tests/fixtures/migration-d1-cond-cohort/branch.sens"
            self.assertTrue(target.is_file())
            self.assertEqual(target.read_bytes(), EXPECTED.read_bytes())
            self.assertNotEqual(target.read_bytes(), (ROOT / FIXTURE).read_bytes())
            record = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(record["summary"]["published"], 1)
            self.assertEqual(runner.verify_published(record, out, False), 1)
            self.assertEqual(record["files"][0]["d2_syntax"], "PASS")
            self.assertEqual(record["files"][0]["semantic_oracle"], "NOT_VERIFIED")
            self.assertTrue((ROOT / FIXTURE).is_file())

            # A stale or forged lower-level receipt cannot claim successful
            # admission, even when bytes and the source SHA still match.
            missing_reader = {**record, "d2_reader": "/nonexistent/sens-trit"}
            with self.assertRaises(runner.MigrationBlocked):
                runner.verify_published(missing_reader, out, False)
            for property_name, forged in (
                ("d2_syntax", "NOT_VERIFIED"),
                ("semantic_oracle", "PASS"),
            ):
                altered = {**record, "files": [{**record["files"][0], property_name: forged}]}
                with self.subTest(field=property_name), self.assertRaises(runner.MigrationBlocked):
                    runner.verify_published(altered, out, False)

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
            runner._git_blob_sha(b"hello\n"),
            "ce013625030ba8dba906f756967f9e9ca394464a"
        )

    def test_publisher_tracks_all_seven_reviewed_data_manifest_cohorts(self):
        # The source-scope reporter is the existing owner of these seven
        # immutable classifications. Publication must never lag its inventory.
        expected = {
            "domain-table": "lib/domains/d1.lisp",
            "comment-only-loader": "lib/core2.lisp",
            "isa": "lib/machine/isa/adx.lisp",
            "schema": "contracts/bija3-l1-l5-ratification.lisp",
            "evidence": "evidence/G5/my-lisp/196d7f2.lisp",
            "expr-record": "tests/fixtures/canon-laws-v2-witness.lisp",
            "knowledge-record": "knowledge/agent-discoveries.lisp",
        }
        records = runner._nonprogram_manifest_paths(ROOT)
        self.assertEqual(len(runner.REVIEWED_NONPROGRAM_MANIFESTS), 7)
        self.assertEqual(
            len(records),
            sum(count for _, _, count in runner.REVIEWED_NONPROGRAM_MANIFESTS),
        )
        self.assertEqual(len(records), 92)
        for cohort, path in expected.items():
            with self.subTest(cohort=cohort):
                source = ROOT / path
                self.assertEqual(
                    runner._git_blob_sha(source.read_bytes()), records[path]
                )
                with self.assertRaisesRegex(runner.MigrationBlocked, "NONPROGRAM"):
                    runner.pin_sources([path], ROOT)

    def test_recent_data_cohort_in_mixed_manifest_aborts_before_any_t5_write(self):
        # The old publisher protected 67 records, leaving these 25 reviewed
        # originals unprotected. The 3 new cohorts must be vetoed atomically.
        sources = [
            "lib/domains/d2.lisp", "lib/surface/ukr.lisp",
            "knowledge/agent-discoveries.lisp",
        ]
        for forbidden in sources:
            with self.subTest(source=forbidden):
                with tempfile.TemporaryDirectory(prefix="sens-92-veto-") as td:
                    temp = Path(td)
                    requested = temp / "selected.json"
                    requested.write_text(json.dumps({"files": [FIXTURE, forbidden]}))
                    out, report = temp / "out", temp / "receipt.json"
                    process = subprocess.run([
                        sys.executable, str(CLI), "--root", str(ROOT),
                        "--manifest", str(requested), "--out", str(out),
                        "--report", str(report), "--source-era", "legacy",
                    ], capture_output=True, text=True, cwd=temp)
                    self.assertEqual(process.returncode, 2,
                                     process.stdout + process.stderr)
                    self.assertIn("NONPROGRAM", process.stderr)
                    self.assertFalse(out.exists())
                    self.assertFalse(report.exists())

    def test_nonprogram_authority_loss_or_incomplete_ledger_fails_closed(self):
        with unittest.mock.patch.object(
            runner, "REVIEWED_NONPROGRAM_MANIFESTS",
            runner.REVIEWED_NONPROGRAM_MANIFESTS +
            (("missing-cohort", "knowledge/missing-owner-authority.json", 1),)
        ):
            with self.assertRaisesRegex(runner.MigrationBlocked, "NONPROGRAM"):
                runner.pin_sources([FIXTURE], ROOT)
        with unittest.mock.patch.object(
            runner, "load_nonprogram_classification", return_value={}
        ):
            with self.assertRaisesRegex(runner.MigrationBlocked, "incomplete"):
                runner.pin_sources([FIXTURE], ROOT)

    def test_archived_print_snapshot_not_executable_even_if_mechanically_convertible(self):
        historical = ("benchmarks/sens-surface/results/"
                      "20260925-icount-33bfb53a/programs/empty-en.lisp")
        original = ROOT / historical
        self.assertEqual(original.read_bytes(), b"(print 0)\n")
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
