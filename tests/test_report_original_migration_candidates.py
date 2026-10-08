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
        self.assertEqual(result["first_blocker_partition"]["first_blocked_total"], 1)
        self.assertEqual(result["first_blocker_partition"]["semantically_admitted_executable_sources"], 0)
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



    def test_partition_every_old_source_once_by_exact_first_blocker(self):
        source_paths = ["w8a.lisp", "w8b.lisp", "w8c.lisp", "syntax.lisp", "text.lisp"]
        for name in source_paths:
            (self.root / name).write_text("(placeholder ())\n", encoding="utf-8")
        reasons = [
            "ambiguous W8 executable head 00001001: choose --source-era legacy or current",
            "ambiguous W8 executable head 00001001: choose --source-era legacy or current",
            "ambiguous W8 executable head 00001011: choose --source-era legacy or current",
            "word 2: requires exact D1..D9 0/1 word, got 'symbol'",
            "Text7 cannot encode something without ratified character identity",
        ]
        rows = []
        for name, reason in zip(source_paths, reasons):
            row = mod.categorize({"path": name, "status": "blocked",
                                 "reason": reason, "token": "symbol",
                                 "line": 2, "column": 3}, self.root)
            rows.append(row)
        partition = mod.first_blocker_cohorts(rows)
        self.assertEqual(partition["status"], "TRIAGE_ONLY_NO_ORACLE")
        self.assertEqual(partition["first_blocked_total"], 5)
        self.assertEqual(sum(x["first_blocked_sources"] for x in partition["cohorts"]), 5)
        self.assertEqual(partition["cohorts"][0]["family"], "W8_ERA_AMBIGUITY")
        self.assertEqual(partition["cohorts"][0]["coordinate"], "00001001")
        self.assertEqual(partition["cohorts"][0]["first_blocked_sources"], 2)
        self.assertEqual(partition["source_counts_by_family"]["W8_ERA_AMBIGUITY"], 3)
        self.assertEqual(partition["source_counts_by_family"]["NON_BINARY_WORD"], 1)
        self.assertEqual(partition["semantically_admitted_executable_sources"], 0)
        members = [m for group in partition["cohorts"] for m in group["original_sources"]]
        self.assertEqual({m["path"] for m in members}, set(source_paths))
        self.assertTrue(all(len(m["source_git_blob_sha"]) == 40 for m in members))
        self.assertEqual({m["line"] for m in members}, {2})
        self.assertTrue(all(g["not_executable_or_semantic_admission"] for g in partition["cohorts"]))

    def test_cohort_rejects_fake_sha_duplicate_and_paired_input(self):
        (self.root / "old.lisp").write_text("(unknown ())\n")
        base = mod.categorize({
            "path": "old.lisp", "status": "blocked", "reason": "ambiguous W8 executable head 00001001",
        }, self.root)
        with self.assertRaisesRegex(ValueError, "non-disjoint"):
            mod.first_blocker_cohorts([base, base])
        corrupt = dict(base, source_git_blob_sha="0" * 39)
        with self.assertRaisesRegex(ValueError, "Git blob"):
            mod.first_blocker_cohorts([corrupt])
        paired = dict(base, same_stem_sens_already_exists=True)
        with self.assertRaisesRegex(ValueError, "paired file"):
            mod.first_blocker_cohorts([paired])

    def test_explicit_first_blocker_not_a_claim_of_executable_classification(self):
        self.assertEqual(mod.first_blocker_identity({
            "reason": "legacy-unmapped SID8/Sens8 00100010: no current resident",
        }), ("LEGACY_SUCCESSOR", "00100010"))
        self.assertEqual(mod.first_blocker_identity({
            "reason": "D2 word 10 is structural control only",
        }), ("D2_STRUCTURE_AS_DATA", "D2"))
        self.assertEqual(mod.first_blocker_identity({
            "reason": "word 3: requires exact D1-D9 binary word",
        }), ("NON_BINARY_WORD", "word3"))
        self.assertEqual(mod.first_blocker_identity({
            "reason": "unrecognized dynamic function head",
        }), ("OTHER_UNPROVEN", "other"))
        self.assertEqual(mod.first_blocker_cohorts([])["cohorts"], [])


if __name__ == "__main__":
    unittest.main()
