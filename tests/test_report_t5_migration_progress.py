#!/usr/bin/env python3
"""Tests for the read-only T5 migration progress synthesis gate."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "t5_progress", ROOT / "scripts/report_t5_migration_progress.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

ZERO_SHA = "0" * 64


def fixtures() -> tuple[dict, dict, set[str]]:
    pairs = {
        "schema": mod.PAIRS_SCHEMA, "mode": "tracked-only",
        "summary": {"sens_files": 1, "physical_pass": 1},
        "files": [{
            "source": "lib/one.lisp", "sens": "lib/one.sens",
            "physical_status": "PASS", "source_status": "PENDING_ORACLE",
            "physical_sha256": ZERO_SHA, "source_sha256": "1" * 64,
            "typed_word_sha256": "2" * 64,
        }],
    }
    readiness = {
        "schema": mod.READINESS_SCHEMA,
        "mode": "original unpaired .lisp only; three separate physical-free dry-runs",
        "migrator_summary": {"files_seen": 2},
        "skipped_existing_sens_pairs": ["lib/one.lisp"],
        "candidate_rows": [
            {"path": "lib/two.lisp", "source_sha256": "3" * 64,
             "status": {"auto": "blocked", "legacy": "blocked", "current": "blocked"},
             "source_scope": "UNCLASSIFIED_NEEDS_SOURCE_PROOF",
             "physical_published": False, "semantic_oracle_admitted": False,
             "blocker_by_era": {"auto": "unmapped W8"}},
            {"path": "benchmarks/archived.lisp", "source_sha256": "4" * 64,
             "status": {"auto": "would-write", "legacy": "would-write", "current": "blocked"},
             "source_scope": "ARCHIVED_BENCHMARK_NONPROGRAM",
             "physical_published": False, "semantic_oracle_admitted": False,
             "blocker_by_era": {}},
        ],
    }
    return pairs, readiness, {
        "lib/one.lisp", "lib/two.lisp", "benchmarks/archived.lisp",
    }


class T5ProgressLedgerTests(unittest.TestCase):
    def test_audits_combine_only_as_mechanical_progress(self):
        pairs, ready, sources = fixtures()
        report = mod.combine(pairs, ready, sources)
        self.assertEqual(report["status"], "COMPLETE_MECHANICAL_INVENTORY_ONLY")
        self.assertTrue(report["source_complete"])
        self.assertEqual(report["summary"]["tracked_lisp_sources"], 3)
        self.assertEqual(report["summary"]["tracked_physical_sens_pairs"], 1)
        self.assertEqual(report["summary"]["unpaired_source_rows"], 2)
        self.assertEqual(report["summary"]["independently_oracle_certified_from_these_inputs"], 0)
        self.assertEqual([r["status"] for r in report["files"]], [
            "NONPROGRAM_ARCHIVED_NO_EXECUTABLE_T5",
            "PHYSICAL_T5_PAIR_PENDING_INDEPENDENT_ORACLE",
            "UNPAIRED_SOURCE_BLOCKED",
        ])
        self.assertTrue(all(not x["semantic_admitted"] for x in report["files"]))

    def test_source_not_in_either_input_blocks_audit(self):
        pairs, ready, sources = fixtures()
        report = mod.combine(pairs, ready, sources | {"lib/missing.lisp"})
        self.assertEqual(report["status"], "BLOCKED_DISCREPANCY")
        self.assertEqual(report["missing_source_paths"], ["lib/missing.lisp"])

    def test_stale_untracked_source_blocks_audit(self):
        pairs, ready, sources = fixtures()
        report = mod.combine(pairs, ready, sources - {"lib/two.lisp"})
        self.assertEqual(report["untracked_or_stale_source_paths"], ["lib/two.lisp"])
        self.assertEqual(report["status"], "BLOCKED_DISCREPANCY")

    def test_duplicate_paths_are_not_silently_counted_twice(self):
        pairs, ready, sources = fixtures()
        ready["candidate_rows"].append(copy.deepcopy(ready["candidate_rows"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mod.combine(pairs, ready, sources)

    def test_audit_disagreement_about_paired_sources_is_fatal(self):
        pairs, ready, sources = fixtures()
        ready["skipped_existing_sens_pairs"] = []
        with self.assertRaisesRegex(ValueError, "disagree"):
            mod.combine(pairs, ready, sources)

    def test_unpaired_cannot_pretend_to_be_semantically_admitted(self):
        pairs, ready, sources = fixtures()
        ready["candidate_rows"][0]["semantic_oracle_admitted"] = True
        with self.assertRaisesRegex(ValueError, "falsely"):
            mod.combine(pairs, ready, sources)

    def test_misnamed_file_does_not_count_as_valid_pair(self):
        pairs, ready, sources = fixtures()
        pairs["files"][0]["sens"] = "lib/one"
        with self.assertRaisesRegex(ValueError, "same-stem"):
            mod.combine(pairs, ready, sources)

    def test_fail_when_semantic_scope_is_changed_by_guess(self):
        pairs, ready, sources = fixtures()
        ready["candidate_rows"][0]["status"]["auto"] = "MERGED"
        with self.assertRaisesRegex(ValueError, "unexpected source-era"):
            mod.combine(pairs, ready, sources)

    def test_symlink_traversal_path_is_forbidden(self):
        for src in ["../lib/x.lisp", "/tmp/x.lisp", "lib/../../x.lisp",
                    "lib\\x.lisp", "./lib/x.lisp"]:
            with self.subTest(src=src), self.assertRaises(ValueError):
                mod._source_name(src)

    def test_actual_repo_pair_audit_matches_no_implicit_semantic_credit(self):
        # Fast independent, read-only smoke test using already-installed
        # auditor; a physical pass never asserts oracle approval.
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import audit_t5_file_pairs
        report = audit_t5_file_pairs.inspect(ROOT)
        self.assertGreaterEqual(report["summary"]["sens_files"], 1)
        self.assertIsNone(report["summary"]["admitted_executable_semantics"])
        for row in report["files"]:
            self.assertTrue(row["sens"].endswith(".sens"))
            self.assertTrue(row["source"].endswith(".lisp"))


if __name__ == "__main__":
    unittest.main()
