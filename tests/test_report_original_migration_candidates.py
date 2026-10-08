#!/usr/bin/env python3
"""Regression for read-only old source T5 migratability census."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import json
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/report_original_migration_candidates.py"
spec = importlib.util.spec_from_file_location("original_candidate_report", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class OriginalCandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pin_real_git_blob_sha_not_plain_sha1(self):
        sample = self.root / "old.lisp"
        sample.write_bytes(b"hello\n")
        self.assertEqual(mod.git_blob_sha(sample),
                         "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_mechanical_candidate_not_semantically_admitted(self):
        source = self.root / "old.lisp"
        source.write_text("(001 ())\n", encoding="utf-8")
        row = mod.categorize({
            "path":"old.lisp", "status":"would-write",
            "bytes":4, "physical_sha256":"a"*64,
            "typed_word_sha256":"b"*64, "semantic_word_count":5,
            "passes":{"already-exact":1},
        },self.root)
        self.assertEqual(row["status"], "CANDIDATE_NOT_ADMITTED")
        self.assertEqual(row["destination"], "old.sens")
        self.assertFalse(row["same_stem_sens_already_exists"])
        self.assertFalse(row["source_is_executable_proven"])
        self.assertFalse(row["independent_semantic_oracle_passed"])
        self.assertEqual(row["proposed_bytes"], 4)

    def test_real_archived_benchmark_is_not_active_source_completion(self):
        path = ("benchmarks/sens-surface/results/"
                "20260925-icount-33bfb53a/programs/empty-en.lisp")
        source = ROOT / path
        self.assertEqual(mod.git_blob_sha(source),
                         "6e30e07f9a44391fb341f5e0ff21ba1e682b5d0f")
        row = mod.categorize({
            "path": path, "status": "would-write",
            "bytes": 4, "physical_sha256": "a"*64,
            "typed_word_sha256": "b"*64, "semantic_word_count": 5,
            "passes": {"pass2-my-lisp": 1},
        }, ROOT)
        self.assertEqual(row["source_scope"], "ARCHIVED_BENCHMARK_NONPROGRAM")
        self.assertFalse(row["source_is_executable_proven"])
        self.assertFalse(row["independent_semantic_oracle_passed"])

    def test_ordinary_active_source_is_not_mistaken_for_snapshot(self):
        self.root.joinpath("local.lisp").write_text("(00000001 ())\\n")
        row = mod.categorize({
            "path": "local.lisp", "status": "blocked",
            "reason": "ambiguous W8 executable head 00001001",
        }, self.root)
        self.assertEqual(row["source_scope"], "UNCLASSIFIED_MAY_NEED_EXECUTABLE_PROOF")
        self.assertEqual(row["work_cohort"], "W8_ERA_PROVENANCE")

    def test_already_paired_cannot_count_as_old_unpaired(self):
        self.root.joinpath("old.lisp").write_text("(001 ())\n", encoding="utf-8")
        self.root.joinpath("old.sens").write_bytes(b"not relevant to classification")
        row = mod.categorize({
            "path":"old.lisp", "status":"would-write",
            "bytes":4, "physical_sha256":"a"*64,
            "typed_word_sha256":"b"*64, "semantic_word_count":5,
            "passes":{},
        }, self.root)
        self.assertTrue(row["same_stem_sens_already_exists"])

    def test_blocked_lisp_stays_blocked(self):
        self.root.joinpath("unknown.lisp").write_text("(unknown ())\n", encoding="utf-8")
        row = mod.categorize({
            "path":"unknown.lisp","status":"blocked",
            "reason":"legacy-unmapped current function",
        }, self.root)
        self.assertEqual(row["status"], "BLOCKED")
        self.assertIn("legacy-unmapped",row["reason"])

    def test_paths_and_missing_or_symlink_sources_fail_closed(self):
        for path in ["../escape.lisp", "/tmp/escape.lisp", "test.sens"]:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    mod.categorize({"path":path,"status":"blocked"}, self.root)
        with self.assertRaises(ValueError):
            mod.categorize({"path":"missing.lisp","status":"blocked"},self.root)
        link = self.root / "link.lisp"
        link.symlink_to(self.root / "missing.lisp")
        with self.assertRaises(ValueError):
            mod.categorize({"path":"link.lisp","status":"blocked"},self.root)


    def test_current_d1_d9_unpaired_source_era_is_default(self):
        self.assertIn("knowledge/d1-d9-foundation.json", mod.ARGS)
        self.assertNotIn("knowledge/d1-d7-foundation.json", mod.ARGS)

    def test_real_original_report_excludes_paired_before_counting(self):
        (self.root / "new-old.lisp").write_text("(unknown ())\\n", encoding="utf-8")
        (self.root / "paired.lisp").write_text("()\\n", encoding="utf-8")
        (self.root / "paired.sens").write_bytes(b"\\x00")
        report = {
            "mode": "dry-run",
            "summary": {
                "files_seen": 1,
                "files_written": 0,
                "files_would_write": 0,
                "files_blocked": 1,
                "files_skipped_paired": 1,
            },
            "skipped_paired_paths": ["paired.lisp"],
            "files": [{
                "path": "new-old.lisp", "status": "blocked",
                "reason": "unratified historical unknown",
            }],
        }
        def fake_run(command, **kwargs):
            self.assertIn("--unpaired-only", command)
            self.assertEqual(command[command.index("--source-era")+1], "auto")
            self.assertIn("knowledge/d1-d9-foundation.json", command)
            Path(command[command.index("--report")+1]).write_text(json.dumps(report))
            return subprocess.CompletedProcess(command, 2, "", "")
        with patch.object(mod.subprocess, "run", side_effect=fake_run):
            result = mod.build_report(self.root)
        summary = result["summary"]
        self.assertEqual(summary["scanned"], 1)
        self.assertEqual(summary["blocked"], 1)
        self.assertEqual(summary["already_paired_sources_excluded"], 1)
        self.assertEqual(result["already_paired_sources_excluded"], ["paired.lisp"])
        self.assertEqual(summary["mechanical_candidates"], 0)
        self.assertEqual(result["source_era"], "auto")
        self.assertEqual(summary["original_unpaired_executables_migrated_by_this_tool"], 0)

    def test_false_pair_in_unpaired_ledger_fails_closed(self):
        (self.root / "paired.lisp").write_text("()\\n")
        (self.root / "paired.sens").write_bytes(b"\\x01")
        report = {
            "mode": "dry-run",
            "summary": {
                "files_seen": 1, "files_written": 0,
                "files_would_write": 1, "files_blocked": 0,
                "files_skipped_paired": 0,
            },
            "skipped_paired_paths": [],
            "files": [{
                "path": "paired.lisp", "status": "would-write",
                "bytes": 1, "physical_sha256": "a"*64,
                "typed_word_sha256": "b"*64, "semantic_word_count": 1,
                "passes": {},
            }],
        }
        def fake_run(command, **kwargs):
            Path(command[command.index("--report")+1]).write_text(json.dumps(report))
            return subprocess.CompletedProcess(command, 0, "", "")
        with patch.object(mod.subprocess, "run", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "already paired"):
                mod.build_report(self.root)


if __name__ == "__main__":
    unittest.main()
