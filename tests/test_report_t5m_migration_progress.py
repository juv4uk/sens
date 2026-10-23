#!/usr/bin/env python3
"""Tests for the read-only T5 migration progress synthesis gate."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "t5_progress", ROOT / "scripts/report_t5m_migration_progress.py"
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
            "physical_status": "PASS", "physical_codec": "t5m",
            "source_status": "PENDING_ORACLE",
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
    def test_tracked_census_does_not_reactivate_superseded_contest(self):
        import subprocess
        from unittest.mock import patch
        git_paths = (b"benchmarks/contest-uk/winner.lisp\0"
                     b"benchmarks/contest-uk/superseded/older.lisp\0"
                     b"lib/normal.lisp\0")
        response = subprocess.CompletedProcess([], 0, stdout=git_paths, stderr=b"")
        with patch.object(mod.subprocess, "run", return_value=response):
            active = mod.tracked_lisp_paths(Path("."))
        self.assertEqual(active, {"benchmarks/contest-uk/winner.lisp",
                                  "lib/normal.lisp"})

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
            "PHYSICAL_T5M_PAIR_PENDING_INDEPENDENT_ORACLE",
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

    def test_legacy_t5_does_not_count_as_current_t5m(self):
        pairs, ready, sources = fixtures()
        pairs["files"][0]["physical_codec"] = "t5"
        report = mod.combine(pairs, ready, sources)
        self.assertEqual(report["status"], "COMPLETE_MECHANICAL_INVENTORY_ONLY")
        self.assertEqual(report["files"][1]["status"],
                         "PHYSICAL_LEGACY_T5_PAIR_REQUIRES_T5M")
        self.assertEqual(report["files"][1]["physical_codec"], "t5")
        self.assertEqual(report["summary"]["mechanically_canonical_physical_pairs"], 1)
        self.assertEqual(report["summary"]["mechanically_canonical_current_t5m_pairs"], 0)
        self.assertEqual(report["summary"]["legacy_t5_pairs_requiring_t5m"], 1)
        self.assertFalse(report["all_executable_lisp_roundtrip_verified"])

    def test_current_t5m_is_mechanical_only_without_native_oracle(self):
        pairs, ready, sources = fixtures()
        report = mod.combine(pairs, ready, sources)
        self.assertEqual(report["summary"]["mechanically_canonical_current_t5m_pairs"], 1)
        self.assertEqual(report["summary"]["legacy_t5_pairs_requiring_t5m"], 0)
        self.assertEqual(report["files"][1]["physical_codec"], "t5m")
        self.assertFalse(report["files"][1]["semantic_admitted"])

    def test_physical_pass_without_identified_codec_is_rejected(self):
        pairs, ready, sources = fixtures()
        pairs["files"][0].pop("physical_codec")
        with self.assertRaisesRegex(ValueError, "without identified T5M/T5 codec"):
            mod.combine(pairs, ready, sources)

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

    def test_current_nonprogram_status_stays_out_of_executable_denominator(self):
        pairs, ready, sources = fixtures()
        item = ready["candidate_rows"][0]
        item["status"]["auto"] = "not-program"
        item["source_scope"] = "NONPROGRAM_DATA_REVIEWED"
        report = mod.combine(pairs, ready, sources)
        self.assertEqual(report["executable_roundtrip_coverage"]["nonprogram_excluded_from_executable_target"], 2)
        self.assertFalse(report["all_executable_lisp_roundtrip_verified"])
        item["source_scope"] = "NONPROGRAM_COMMENT_ONLY"
        report = mod.combine(pairs, ready, sources)
        self.assertIn("NONPROGRAM_COMMENT_ONLY_NO_EXECUTABLE_T5",
                      [row["status"] for row in report["files"]])
        item["source_scope"] = "UNCLASSIFIED_NEEDS_SOURCE_PROOF"
        with self.assertRaisesRegex(ValueError, "unreviewed not-program"):
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

    def test_bits_backed_sens_fixture_does_not_inflate_lisp_coverage(self):
        pairs, ready, sources = fixtures()
        binary = copy.deepcopy(pairs["files"][0])
        binary.update({
            "source": "tests/semantic/sample.bits",
            "sens": "tests/semantic/sample.sens",
            "source_status": "EXACT_BINARY_SOURCE",
        })
        pairs["files"].append(binary)
        pairs["summary"]["sens_files"] = 2
        pairs["summary"]["physical_pass"] = 2
        report = mod.combine(pairs, ready, sources)
        self.assertEqual(report["status"], "COMPLETE_MECHANICAL_INVENTORY_ONLY")
        self.assertTrue(report["source_complete"])
        self.assertEqual(report["summary"]["tracked_lisp_sources"], 3)
        self.assertEqual(report["summary"]["tracked_physical_sens_pairs"], 1)
        self.assertEqual(report["summary"]["tracked_binary_source_fixture_pairs"], 1)
        self.assertEqual(report["summary"]["mechanically_canonical_physical_pairs"], 1)
        self.assertEqual(report["executable_roundtrip_coverage"]["blocked_or_unverified"], 2)
        self.assertNotIn("tests/semantic/sample.bits",
                         {row["source"] for row in report["files"]})
        self.assertFalse(report["all_executable_lisp_roundtrip_verified"])

    def test_broken_bits_fixture_reports_real_physical_defect(self):
        pairs, ready, sources = fixtures()
        binary = copy.deepcopy(pairs["files"][0])
        binary.update({
            "source": "tests/semantic/broken.bits",
            "sens": "tests/semantic/broken.sens",
            "source_status": "BLOCKED",
            "physical_status": "BLOCKED",
        })
        pairs["files"].append(binary)
        pairs["summary"]["sens_files"] = 2
        # The real physical auditor counts only the first pair as PASS.
        report = mod.combine(pairs, ready, sources)
        self.assertEqual(report["status"], "BLOCKED_DISCREPANCY")
        self.assertEqual(report["summary"]["binary_source_fixture_physical_blocked"], 1)
        self.assertEqual(report["summary"]["tracked_physical_sens_pairs"], 1)
        self.assertEqual(report["summary"]["mechanically_canonical_physical_pairs"], 1)
        self.assertEqual(report["summary"]["missing_from_both_audits"], 0)

    def test_actual_repo_pair_audit_matches_no_implicit_semantic_credit(self):
        # Fast independent, read-only smoke test using already-installed
        # auditor; a physical pass never asserts oracle approval.
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import audit_t5_t5m_file_pairs
        report = audit_t5_t5m_file_pairs.inspect(ROOT)
        self.assertGreaterEqual(report["summary"]["sens_files"], 1)
        self.assertIsNone(report["summary"]["admitted_executable_semantics"])
        for row in report["files"]:
            self.assertTrue(row["sens"].endswith(".sens"))
            # The physical auditor also accepts exact .bits-backed fixtures.
            # Their existence never proves an unpaired executable .lisp.
            self.assertTrue(row["source"].endswith((".lisp", ".bits")))


if __name__ == "__main__":
    unittest.main()
