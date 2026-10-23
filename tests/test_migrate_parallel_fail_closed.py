#!/usr/bin/env python3
"""Fail-closed Zig-only parallel migration orchestration (synthetic workers).

No SENS semantic truth is asserted; a mock worker supplies only file ledger
receipts so the real Bash wrapper must refuse missing/forged/partial reports.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/migrate-parallel.sh"

MOCK_DRIVER = r'''#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--out", required=True)
p.add_argument("--report", required=True)
p.add_argument("--write", action="store_true")
p.add_argument("--zig-codec", action="store_true")
p.add_argument("--source-era", default="auto")
p.add_argument("paths", nargs="+")
a = p.parse_args()
mode = os.environ.get("MOCK_DRIVER_MODE", "valid")
if mode == "missing":
    sys.exit(0)
if mode == "malformed":
    Path(a.report).write_text("{", encoding="utf-8")
    sys.exit(0)

entries = [{"path": Path(path).as_posix(),
            "status": "blocked" if mode == "blocked" else "would-write"}
           for path in a.paths]
if mode == "foreign":
    entries[0]["path"] = "src/forged.lisp"
summary = {"files_seen": len(entries),
           "files_admitted": 0 if mode == "blocked" else len(entries),
           "files_written": 0,
           "files_would_write": 0 if mode == "blocked" else len(entries),
           "files_blocked": len(entries) if mode == "blocked" else 0}
if mode == "bad-count":
    summary["files_seen"] += 1
data = {"schema": "sens-t5-safe-batch/v1", "mode": "dry-run",
        "root": "mock-unchanged-project",
        "output_mirror": str(a.out),
        "authority": {"codec": "zig-physical-only"},
        "files": entries, "summary": summary}
Path(a.report).write_text(json.dumps(data), encoding="utf-8")
if mode == "worker-error":
    sys.exit(1)
'''


class ZigParallelWorkerReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-zig-parallel-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        (self.root / "src").mkdir()
        (self.root / "src/a.lisp").write_text("(110 1 0)\n", encoding="utf-8")
        (self.root / "src/b.lisp").write_text("(110 0 1)\n", encoding="utf-8")
        shutil.copyfile(WRAPPER, self.root / "scripts/migrate-parallel.sh")
        (self.root / "scripts/migrate-t5m-batch.py").write_text(
            MOCK_DRIVER, encoding="utf-8"
        )
        self.report = self.root / "merged.json"
        self.output = self.root / "out"

    def invoke(self, mode: str, *sources: str,
               report: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["MOCK_DRIVER_MODE"] = mode
        return subprocess.run(
            ["bash", str(self.root / "scripts/migrate-parallel.sh"),
             "--jobs", "2", "--out", str(self.output),
             "--report", str(report if report is not None else self.report),
             *sources],
            cwd=self.root, capture_output=True, text=True, timeout=20,
            env=env, check=False,
        )

    def test_valid_two_worker_ledger_merges_exactly_once(self) -> None:
        run = self.invoke("valid", "src/a.lisp", "src/b.lisp")
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        data = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "COMPLETE")
        self.assertEqual([r["path"] for r in data["files"]],
                         ["src/a.lisp", "src/b.lisp"])
        self.assertEqual(data["summary"]["files_seen"], 2)
        self.assertEqual(data["summary"]["files_admitted"], 2)

    def test_existing_sens_output_never_overwritten_by_merged_json(self) -> None:
        (self.output / "lib").mkdir(parents=True)
        protected = self.output / "lib" / "third.sens"
        original = bytes.fromhex("00ff210300")
        protected.write_bytes(original)
        run = self.invoke("valid", "src/a.lisp", "src/b.lisp",
                          report=protected)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=report-output-collision", run.stderr)
        self.assertIn("layer=transport", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertEqual(protected.read_bytes(), original)
        self.assertFalse(self.report.exists())

    def test_future_nested_report_inside_mirror_is_blocked_preflight(self) -> None:
        nested = self.output / "reports" / "summary.json"
        run = self.invoke("valid", "src/a.lisp", "src/b.lisp",
                          report=nested)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=report-output-collision", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertFalse(nested.exists())
        self.assertFalse(self.output.exists())

    def test_dotdot_and_symlink_report_aliases_cannot_reach_sens(self) -> None:
        (self.output / "lib").mkdir(parents=True)
        (self.output / "reports").mkdir()
        protected = self.output / "lib" / "third.sens"
        original = b"DO-NOT-OVERWRITE-ZIG-BYTES"
        protected.write_bytes(original)
        alias = self.root / "receipt-alias.json"
        alias.symlink_to(protected)
        for report in (self.output / "reports" / ".." / "lib" / "third.sens",
                       alias):
            with self.subTest(report=str(report)):
                run = self.invoke("valid", "src/a.lisp", report=report)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn("test_id=report-output-collision", run.stderr)
                self.assertNotIn("--- worker", run.stdout)
                self.assertEqual(protected.read_bytes(), original)
                self.assertFalse(self.report.exists())

    def test_input_lisp_can_never_be_report_destination(self) -> None:
        # A valid merged report cannot overwrite a canonical source file.
        protected = self.root / "src/a.lisp"
        original = protected.read_bytes()
        for report in (protected, self.root / "src" / ".." / "src" / "a.lisp"):
            with self.subTest(report=str(report)):
                run = self.invoke("valid", "src/a.lisp", "src/b.lisp", report=report)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn("test_id=report-source-collision", run.stderr)
                self.assertIn("layer=transport", run.stderr)
                self.assertNotIn("--- worker", run.stdout)
                self.assertEqual(protected.read_bytes(), original)
                self.assertFalse(self.report.exists())
        self.assertFalse(self.output.exists())

    def test_report_symlink_to_source_is_blocked(self) -> None:
        protected = self.root / "src/a.lisp"
        original = protected.read_bytes()
        alias = self.root / "receipt-link.json"
        alias.symlink_to(protected)
        run = self.invoke("valid", "src/a.lisp", report=alias)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=report-source-collision", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertEqual(protected.read_bytes(), original)
        self.assertTrue(alias.is_symlink())
        self.assertFalse(self.report.exists())

    def test_report_hardlink_to_source_is_blocked(self) -> None:
        protected = self.root / "src/a.lisp"
        original = protected.read_bytes()
        alias = self.root / "receipt-hardlink.json"
        try:
            os.link(protected, alias)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"hardlinks unavailable on this host: {exc}")
        self.assertNotEqual(protected.resolve(), alias.resolve())
        self.assertEqual(protected.stat().st_ino, alias.stat().st_ino)
        run = self.invoke("valid", "src/a.lisp", report=alias)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=report-source-collision", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertEqual(protected.read_bytes(), original)
        self.assertEqual(alias.read_bytes(), original)
        self.assertFalse(self.report.exists())

    def test_duplicate_explicit_path_is_blocked_before_any_worker(self) -> None:
        run = self.invoke("valid", "src/a.lisp", "./src/a.lisp")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=duplicate-source", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertFalse(self.report.exists())

    def test_directory_plus_explicit_path_must_not_race_output(self) -> None:
        run = self.invoke("valid", "src", "src/a.lisp")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=duplicate-source", run.stderr)
        self.assertFalse(self.report.exists())

    def test_dotdot_alias_is_same_physical_lisp_and_no_workers_start(self) -> None:
        run = self.invoke("valid", "src/a.lisp", "src/../src/a.lisp")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=duplicate-source", run.stderr)
        self.assertIn("same_physical_source=", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertFalse(self.report.exists())
        self.assertFalse(self.output.exists())

    def test_symlink_alias_is_same_physical_lisp_and_no_workers_start(self) -> None:
        (self.root / "src" / "alias.lisp").symlink_to("a.lisp")
        run = self.invoke("valid", "src/a.lisp", "src/alias.lisp")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=duplicate-source", run.stderr)
        self.assertIn("same_physical_source=", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertFalse(self.report.exists())

    def test_hardlink_alias_is_one_inode_and_no_workers_start(self) -> None:
        # Path.resolve() alone does not identify distinct hardlink names.
        hardlink = self.root / "src" / "hardlink.lisp"
        try:
            os.link(self.root / "src" / "a.lisp", hardlink)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"hardlinks unavailable on this host: {exc}")
        self.assertNotEqual(
            (self.root / "src" / "a.lisp").resolve(), hardlink.resolve()
        )
        run = self.invoke("valid", "src/a.lisp", "src/hardlink.lisp")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=duplicate-source", run.stderr)
        self.assertIn("same_inode=", run.stderr)
        self.assertNotIn("--- worker", run.stdout)
        self.assertFalse(self.report.exists())
        self.assertFalse(self.output.exists())

    def test_separate_inodes_are_allowed_even_with_identical_contents(self) -> None:
        # Byte equality is NOT file identity, and is not SENS semantics.
        (self.root / "src/b.lisp").write_bytes(
            (self.root / "src/a.lisp").read_bytes()
        )
        self.assertNotEqual(
            (self.root / "src/a.lisp").stat().st_ino,
            (self.root / "src/b.lisp").stat().st_ino,
        )
        run = self.invoke("valid", "src/a.lisp", "src/b.lisp")
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        receipt = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "COMPLETE")
        self.assertEqual(receipt["summary"]["files_seen"], 2)

    def test_directory_input_expands_only_distinct_lisp_sources(self) -> None:
        # The documented CLI accepts directories; do not outlaw them to
        # make a negative test green. This is host path expansion, not SENS.
        run = self.invoke("valid", "src")
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        data = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "COMPLETE")
        self.assertEqual([row["path"] for row in data["files"]],
                         ["src/a.lisp", "src/b.lisp"])
        self.assertEqual(data["summary"]["files_seen"], 2)

    def test_missing_and_nonlisp_inputs_block_before_workers(self) -> None:
        (self.root / "src" / "not-source.txt").write_text(
            "not a binary SENS source", encoding="utf-8"
        )
        for path in ("src/missing.lisp", "src/not-source.txt"):
            with self.subTest(path=path):
                run = self.invoke("valid", path)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn("test_id=invalid-source", run.stderr)
                self.assertNotIn("--- worker", run.stdout)
                self.assertFalse(self.report.exists())

    def test_success_exit_without_report_is_not_a_green_receipt(self) -> None:
        run = self.invoke("missing", "src/a.lisp", "src/b.lisp")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("test_id=invalid-worker-report", run.stderr)
        self.assertFalse(self.report.exists())

    def test_malformed_or_forged_or_invalid_count_never_merges(self) -> None:
        for mode in ("malformed", "foreign", "bad-count"):
            with self.subTest(mode=mode):
                self.report.unlink(missing_ok=True)
                run = self.invoke(mode, "src/a.lisp", "src/b.lisp")
                self.assertNotEqual(run.returncode, 0)
                self.assertIn("test_id=invalid-worker-report", run.stderr)
                self.assertFalse(self.report.exists())

    def test_partial_or_failing_worker_does_not_publish_green(self) -> None:
        for mode in ("blocked", "worker-error"):
            with self.subTest(mode=mode):
                self.report.unlink(missing_ok=True)
                run = self.invoke(mode, "src/a.lisp", "src/b.lisp")
                self.assertNotEqual(run.returncode, 0, run.stdout)
                self.assertIn("test_id=worker-rejected", run.stderr)
                data = json.loads(self.report.read_text(encoding="utf-8"))
                self.assertEqual(data["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
