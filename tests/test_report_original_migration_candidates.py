#!/usr/bin/env python3
"""Regression for read-only old source T5 migratability census."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
