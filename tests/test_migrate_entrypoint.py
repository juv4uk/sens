#!/usr/bin/env python3
"""Не дозволяти агентам обходити канонічний допуск міграції."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sens_migrate_frontdoor", ROOT / "scripts/migrate.py")
assert spec and spec.loader
migrate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = migrate
spec.loader.exec_module(migrate)


class CanonicalMigrateEntrypointTests(unittest.TestCase):
    def test_candidates_always_read_only_original_report(self):
        argv = migrate.parser().parse_args(["candidates", "--report", "/tmp/candidates.json"])
        self.assertEqual(migrate.command(argv)[1].split("/")[-1],
                         "report_original_migration_candidates.py")
        self.assertEqual(migrate.command(argv)[-2:], ["--out", "/tmp/candidates.json"])

    def test_preview_runs_existing_three_pass_batch_in_dry_mode(self):
        args = migrate.parser().parse_args(
            ["preview", "benchmarks/lists.lisp", "--mirror", "/tmp/mirror",
             "--report", "/tmp/preview.json"])
        cmd = migrate.command(args)
        self.assertEqual(Path(cmd[1]).name, "migrate-t5-batch.py")
        self.assertIn("benchmarks/lists.lisp", cmd)
        self.assertNotIn("--write", cmd)
        self.assertEqual(cmd[-4:], ["--report", "/tmp/preview.json", "--source-era", "auto"])
        historical = migrate.parser().parse_args(["preview", "tests/fixtures/migration-multiform-cohort/two-forms.lisp", "--mirror", "/tmp/m", "--report", "/tmp/r.json", "--source-era", "legacy"])
        self.assertEqual(migrate.command(historical)[-2:], ["--source-era", "legacy"])
        with self.assertRaises(SystemExit):
            migrate.parser().parse_args(
                ["preview", "benchmarks/lists.lisp", "--mirror", "/tmp/mirror",
                 "--report", "/tmp/preview.json", "--write"])

    def test_admit_requires_all_independent_evidence_and_write_is_explicit(self):
        p = migrate.parser()
        with self.assertRaises(SystemExit):
            p.parse_args(["admit", "--write"])
        base = ["admit", "--manifest", "/tmp/proof.json",
                "--mirror", "/tmp/mirror", "--reader", "/tmp/sens-trit",
                "--report", "/tmp/status.json"]
        dry = migrate.command(p.parse_args(base))
        actual = migrate.command(p.parse_args(base + ["--write"]))
        self.assertEqual(Path(dry[1]).name, "admit-t5-migration.py")
        self.assertNotIn("--write", dry)
        self.assertEqual(actual, dry + ["--write"])

    def test_blocked_exit_code_is_never_rewritten_as_success(self):
        with mock.patch.object(migrate.subprocess, "run",
                               return_value=subprocess.CompletedProcess([], 2)) as run:
            status = migrate.main(["candidates", "--report", "/tmp/candidates.json"])
        self.assertEqual(status, 2)
        self.assertFalse(run.call_args.kwargs.get("shell", False))
        self.assertFalse(run.call_args.kwargs.get("check", True))
        self.assertEqual(run.call_args.kwargs["cwd"], ROOT)

    def test_preview_displays_real_reason_from_report_and_preserves_block(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "reason.json"
            report.write_text(json.dumps({"files": [{
                "path": "lib/machine/block.lisp",
                "status": "blocked",
                "reason": "unresolved executable machine-block / missing current source law",
            }]}), encoding="utf-8")
            message = io.StringIO()
            with mock.patch.object(migrate.subprocess, "run",
                                   return_value=subprocess.CompletedProcess([], 2)):
                with contextlib.redirect_stderr(message):
                    code = migrate.main(["preview", "lib/machine/block.lisp",
                                         "--mirror", str(Path(td) / "out"),
                                         "--report", str(report)])
            self.assertEqual(code, 2)
            self.assertIn("lib/machine/block.lisp", message.getvalue())
            self.assertIn("unresolved executable machine-block", message.getvalue())

    def test_missing_or_malformed_blocked_report_never_becomes_success(self):
        with tempfile.TemporaryDirectory() as td:
            report = Path(td) / "broken.json"
            self.assertEqual(migrate.blocked_reasons(report), [])
            report.write_text("this is not JSON", encoding="utf-8")
            self.assertEqual(migrate.blocked_reasons(report), [])
            report.write_text(json.dumps({"files": [False, None, {"status": "would-write"}]}))
            self.assertEqual(migrate.blocked_reasons(report), [])
            with mock.patch.object(migrate.subprocess, "run",
                                   return_value=subprocess.CompletedProcess([], 2)):
                self.assertEqual(migrate.main(["preview", "benchmarks/lists.lisp",
                                                "--mirror", str(Path(td) / "out"),
                                                "--report", str(report)]), 2)
    def test_no_shell_injection_or_untrusted_extra_flags(self):
        suspicious = "benchmarks/x;touch /tmp/owned.lisp"
        args = migrate.parser().parse_args(
            ["preview", suspicious, "--mirror", "/tmp/out", "--report", "/tmp/r.json"])
        self.assertIn(suspicious, migrate.command(args))
        self.assertIsInstance(migrate.command(args), list)


if __name__ == "__main__":
    unittest.main()
