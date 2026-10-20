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
        "mode": "original unpaired .lisp only; one physical-free dry-run (SID8/Sens8 eras retired)",
        "migrator_summary": {"files_seen": 2},
        "skipped_existing_sens_pairs": ["lib/one.lisp"],
        "candidate_rows": [
            {"path": "lib/two.lisp", "source_sha256": "3" * 64,
             "status": {"auto": "blocked"},
             "source_scope": "UNCLASSIFIED_NEEDS_SOURCE_PROOF",
             "physical_published": False, "semantic_oracle_admitted": False,
             "empty": "unmapped W8"},
            {"path": "benchmarks/archived.lisp", "source_sha256": "4" * 64,
             "status": {"auto": "would-write"},
             "source_scope": "ARCHIVED_BENCHMARK_NONPROGRAM",
             "physical_published": False, "semantic_oracle_admitted": False,
             "empty": None},
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

    def test_complete_source_inventory_is_not_full_sens_roundtrip(self):
        pairs, ready, sources = fixtures()
        report = mod.combine(pairs, ready, sources)
        self.assertEqual(report["status"], "COMPLETE_MECHANICAL_INVENTORY_ONLY")
        self.assertIs(report["all_executable_lisp_roundtrip_verified"], False)
        self.assertEqual(report["executable_roundtrip_coverage"], {
            "executable_or_unclassified_sources": 2,
            "independent_runtime_oracle_verified": 0,
            "blocked_or_unverified": 2,
            "nonprogram_excluded_from_executable_target": 1,
        })

    def test_strict_cli_blocks_missing_native_oracle_even_when_inventory_complete(self):
        import json
        import tempfile
        from unittest.mock import patch
        pairs, ready, sources = fixtures()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paired = root / "pairs.json"
            unpaired = root / "unpaired.json"
            output = root / "audit.json"
            paired.write_text(json.dumps(pairs), encoding="utf-8")
            unpaired.write_text(json.dumps(ready), encoding="utf-8")
            with patch.object(mod, "tracked_lisp_paths", return_value=sources):
                verdict = mod.main([
                    "--pairs", str(paired), "--readiness", str(unpaired),
                    "--root", str(root), "--out", str(output),
                    "--require-executable-roundtrip",
                ])
            self.assertEqual(verdict, 2)
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(written["source_complete"])
            self.assertFalse(written["all_executable_lisp_roundtrip_verified"])

    def test_one_auto_pass_rejects_retired_three_era_evidence(self):
        pairs, ready, sources = fixtures()
        ready["candidate_rows"][0]["status"]["legacy"] = "blocked"
        with self.assertRaisesRegex(ValueError, "incomplete source-era"):
            mod.combine(pairs, ready, sources)

    def test_reviewed_data_never_counts_as_executable_migration(self):
        pairs, ready, sources = fixtures()
        ready["candidate_rows"][0]["source_scope"] = "NONPROGRAM_DATA_REVIEWED"
        report = mod.combine(pairs, ready, sources)
        reviewed = next(r for r in report["files"] if r["source"] == "lib/two.lisp")
        self.assertEqual(reviewed["status"], "NONPROGRAM_REVIEWED_NO_EXECUTABLE_T5")
        self.assertFalse(reviewed["semantic_admitted"])

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

    def test_noncanonical_aliases_rejected_by_source_inventory(self):
        self.assertEqual(mod._source_name("lib/one.lisp"), "lib/one.lisp")
        for source in (
            "lib//one.lisp", "lib/./one.lisp", "lib/sub/../one.lisp",
            "lib/\x00one.lisp", "lib\\one.lisp",
        ):
            with self.subTest(source=source), self.assertRaises(ValueError):
                mod._source_name(source)
        pairs, readiness, tracked = fixtures()
        with self.assertRaises(ValueError):
            mod.combine(pairs, readiness, tracked | {"lib//one.lisp"})

    def test_orphan_physical_sens_without_source_is_named(self):
        pairs, readiness, tracked = fixtures()
        orphan = copy.deepcopy(pairs["files"][0])
        orphan["source"] = "lib/orphan.lisp"
        orphan["sens"] = "lib/orphan.sens"
        orphan["physical_sha256"] = "5" * 64
        pairs["files"].append(orphan)
        pairs["summary"]["sens_files"] = 2
        pairs["summary"]["physical_pass"] = 2
        readiness["skipped_existing_sens_pairs"].append("lib/orphan.lisp")
        report = mod.combine(pairs, readiness, tracked)
        self.assertEqual(report["status"], "BLOCKED_DISCREPANCY")
        self.assertEqual(report["orphan_physical_sens_paths"], ["lib/orphan.sens"])
        self.assertEqual(report["summary"]["orphan_physical_sens_without_tracked_lisp"], 1)
        self.assertIn("lib/orphan.lisp", report["untracked_or_stale_source_paths"])
        self.assertEqual(report["summary"]["independently_oracle_certified_from_these_inputs"], 0)

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
