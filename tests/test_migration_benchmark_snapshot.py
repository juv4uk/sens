#!/usr/bin/env python3
"""#4458: narrow, source-pinned historical benchmark evidence classification.

This gate DOES NOT alter the executable three-pass migrator or authorize
T5 output; it only prevents snapshot records being miscounted as current
application source during coordination/release reporting.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/migration-benchmark-snapshot-2026-10-08.json"


def git_blob_sha(content: bytes) -> str:
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content).hexdigest()


def archived_program_path(path: str) -> bool:
    """Only a historical results/<dated-snapshot>/programs/*.lisp record."""
    if path.startswith("/") or "\\" in path:
        return False
    segments = PurePosixPath(path).parts
    return (
        len(segments) == 6
        and segments[:3] == ("benchmarks", "sens-surface", "results")
        and bool(re.fullmatch(r"[0-9]{8}-[A-Za-z0-9._-]+", segments[3]))
        and segments[4] == "programs"
        and segments[5] not in ("", ".", "..")
        and segments[5].endswith(".lisp")
        and all(segment not in (".", "..") for segment in path.split("/"))
    )


class ArchivedBenchmarkMigrationGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_metadata_never_claims_executable_conversion(self):
        record = self.record
        self.assertEqual(record["schema"], "sens-t5-archive-evidence/v1")
        self.assertEqual(record["status"], "NONPROGRAM_ARCHIVED_BENCHMARK_EVIDENCE")
        self.assertEqual(record["source_scan_print_blocked_rows"], 75)
        self.assertEqual(record["admitted_as_executable"], 0)
        self.assertEqual(record["emitted_physical_sens"], 0)
        self.assertIs(record["allow_bulk_conversion"], False)
        self.assertIs(record["allow_release_pin_change"], False)

    def test_real_historical_record_is_pinned_to_original_bytes(self):
        entry = self.record["representative"]
        path = entry["path"]
        self.assertTrue(archived_program_path(path), path)
        source = ROOT / path
        self.assertTrue(source.is_file(), path)
        self.assertFalse(source.is_symlink(), path)
        self.assertEqual(git_blob_sha(source.read_bytes()), entry["git_blob_sha"])
        self.assertIn(entry["expected_source_line"], source.read_text(encoding="utf-8"))
        # This is output from an archived BENCHMARK, not standalone SENS source.
        measurement_path = entry["measurement_path"]
        measurement = ROOT / measurement_path
        self.assertEqual(measurement, source.parent.parent / "runs.tsv")
        self.assertTrue(measurement.is_file(), measurement_path)
        self.assertEqual(
            git_blob_sha(measurement.read_bytes()),
            entry["measurement_git_blob_sha"],
        )

    def test_archive_scope_never_swallow_executable_sources(self):
        candidates = (
            "lib/compiler-nucleus.lisp",
            "lib/machine/dispatch/native-first.lisp",
            "lib/core1.lisp",
            "benchmarks/sens-surface/run.py",
            "benchmarks/sens-surface/results/a-program.lisp",
            "benchmarks/sens-surface/results/20260925-example/bench.lisp",
            "benchmarks/sens-surface/results/20260925-example/examples/fib.lisp",
            "benchmarks/sens-surface/results/20260925-example/programs/fib.sens",
            "benchmarks/sens-surface/results/20260925-example/programs/../../../../lib/core1.lisp",
            "/benchmarks/sens-surface/results/20260925-example/programs/fib.lisp",
            "benchmarks\\sens-surface\\results\\20260925-example\\programs\\fib.lisp",
        )
        for candidate in candidates:
            with self.subTest(path=candidate):
                self.assertFalse(archived_program_path(candidate))

    def test_archive_records_are_read_only_and_have_no_auto_sens_twins(self):
        archive_root = ROOT / "benchmarks/sens-surface/results"
        self.assertTrue(archive_root.is_dir())
        records = sorted(
            path for path in archive_root.glob("*/programs/*.lisp")
            if path.is_file()
        )
        self.assertTrue(records, "expected at least one archived benchmark source")
        self.assertIn(ROOT / self.record["representative"]["path"], records)
        for source in records:
            with self.subTest(file=str(source.relative_to(ROOT))):
                self.assertFalse(source.is_symlink())
                self.assertTrue(archived_program_path(source.relative_to(ROOT).as_posix()))
                # This is a non-publishing *read-only* guard.
                self.assertFalse(
                    source.with_suffix(".sens").exists(),
                    f"unreviewed binary twin beside historic snapshot: {source}",
                )


if __name__ == "__main__":
    unittest.main()
