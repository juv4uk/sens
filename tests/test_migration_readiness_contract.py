#!/usr/bin/env python3
"""Regress the ORIGINAL unpaired readiness contract against real mainline D1-D9.

These tests do NOT claim any unpaired Lisp has semantic/oracle admission.
They verify that the census uses the exact same ratified foundation and
fail-closed W8 default as the merged production batch migrator.
"""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "migration-readiness-census.py"
spec = importlib.util.spec_from_file_location("migration_readiness_contract", PATH)
assert spec and spec.loader
census = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = census
spec.loader.exec_module(census)


def fake_migrator_call(*, newly_eligible=0, per_era_candidates=None, archived_auto=False):
    """Mock the canonical 3 source-era scans using REAL present source names."""
    observed = []
    calls = []
    first = "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
    second = "tests/fixtures/core1-third-domain-canary/third.lisp"
    archive = "benchmarks/sens-surface/results/20260925-icount-33bfb53a/programs/empty-en.lisp"
    possible = per_era_candidates or {}

    def run(argv, **kwargs):
        calls.append(list(argv))
        observed.extend(argv)
        assert kwargs["cwd"] == ROOT
        assert kwargs["timeout"] == 180
        era = argv[argv.index("--source-era") + 1]
        out = Path(argv[argv.index("--report") + 1])
        selected = possible.get(era, [])
        if newly_eligible and era == "auto":
            selected = [second]
        if archived_auto and era == "auto":
            selected = [archive]
        rows = [
            {"path": path, "status": "would-write" if path in selected else "blocked",
             "reason": None if path in selected else
                f"ambiguous W8 executable head 00001001: {era}"}
            for path in ((first, second, archive) if archived_auto else (first, second))
        ]
        blocked = sum(row["status"] == "blocked" for row in rows)
        ready = len(rows) - blocked
        state = {
            "schema": "sens-three-pass-t5-migration/v3",
            "authority": {"foundation_sha256": "mock-ratified-sha256"},
            "source_era": era,
            "summary": {
                "files_seen": len(rows),
                "files_written": 0,
                "files_would_write": ready,
                "files_blocked": blocked,
            },
            "skipped_paired_paths": ["tests/fixtures/core1-domain-canary/second.lisp"],
            "files": rows,
        }
        out.write_text(json.dumps(state), encoding="utf-8")
        return SimpleNamespace(returncode=0 if ready else 2, stdout="", stderr="")

    return observed, run


# Real authoritative decoder used for the integration test, even while the
# bounded mock report tests suppress the unrelated 67 true original records.
REAL_REVIEWED_LOADER = census.load_nonprogram_classification


class ReadinessContractTests(unittest.TestCase):
    def setUp(self):
        mock = patch.object(census, "load_nonprogram_classification", return_value={})
        mock.start()
        self.addCleanup(mock.stop)

    def test_uses_owner_ratified_d1_d9_not_stale_d1_d7(self):
        assert (ROOT / "knowledge" / "d1-d9-foundation.json").is_file()
        self.assertIn("--foundation", census.ARTIFACT_ARGS)
        i = census.ARTIFACT_ARGS.index("--foundation")
        self.assertEqual(census.ARTIFACT_ARGS[i+1], "knowledge/d1-d9-foundation.json")
        self.assertNotIn("knowledge/d1-d7-foundation.json", census.ARTIFACT_ARGS)

    def test_census_invokes_era_auto_and_excludes_existing_pairs_without_writes(self):
        observed, fn = fake_migrator_call()
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertEqual(observed[observed.index("--source-era")+1], "auto")
        self.assertEqual(observed[observed.index("--foundation")+1],
                         "knowledge/d1-d9-foundation.json")
        for opt in ("--unpaired-only", "--dry-run"):
            self.assertIn(opt, observed)
        self.assertTrue(report["gate"]["pass"])
        self.assertEqual(report["source_era"], "auto")
        self.assertEqual(report["foundation_path"], "knowledge/d1-d9-foundation.json")
        self.assertEqual(report["ratified_foundation_sha256"], "mock-ratified-sha256")
        self.assertEqual(report["migrator_summary"]["files_blocked"], 2)
        self.assertEqual(report["physical_outputs_created"], [])

    def test_new_mechanical_candidate_blocks_release_not_claim_success(self):
        _, fn = fake_migrator_call(newly_eligible=1)
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertFalse(report["gate"]["pass"])
        self.assertEqual(report["migrator_summary"]["files_would_write"], 1)
        self.assertEqual(report["physical_outputs_created"], [])
        self.assertEqual(report["migrator_summary"]["files_written"], 0)

    def test_same_original_set_scanned_in_all_three_eras_without_publish(self):
        observed, fn = fake_migrator_call(per_era_candidates={
            "legacy": ["tests/fixtures/core1-third-domain-canary/third.lisp"]
        })
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertEqual(observed.count("--source-era"), 3)
        self.assertEqual(report["candidate_queues"].get(
            "legacy-mechanical-needs-provenance-and-oracle"), 1)
        self.assertEqual(report["candidate_queues"].get(
            "blocked-in-all-eras-needs-semantic-or-nonprogram-triage"), 1)
        self.assertEqual(len(report["candidate_rows"]), 2)
        self.assertEqual(len(report["candidate_rows"][0]["source_sha256"]), 64)
        self.assertTrue(all(not row["semantic_oracle_admitted"] and
                            not row["physical_published"]
                            for row in report["candidate_rows"]))
        self.assertEqual(report["per_era_summary"]["legacy"]["files_would_write"], 1)
        self.assertEqual(report["blocker_by_era_reason_counts"]["legacy"].get(
            "ambiguous W8 executable head 00001001"), 1)
        self.assertTrue(report["top_blocker_transitions"])
        self.assertEqual(sum(x["files"] for x in report["top_blocker_transitions"]), 2)
        self.assertEqual(report["per_era_summary"]["auto"]["files_would_write"], 0)
        self.assertTrue(report["gate"]["pass"])

    def test_ambiguous_both_era_candidate_is_not_automatically_admitted(self):
        source = "tests/fixtures/core1-third-domain-canary/third.lisp"
        _, fn = fake_migrator_call(per_era_candidates={
            "legacy": [source], "current": [source]
        })
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertEqual(report["candidate_queues"].get(
            "both-eras-mechanical-needs-provenance-and-oracle"), 1)
        self.assertTrue(report["gate"]["pass"])
        self.assertEqual(report["physical_outputs_created"], [])

    def test_historical_archive_candidate_is_not_active_application(self):
        _, fn = fake_migrator_call(archived_auto=True)
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertTrue(report["gate"]["pass"])
        sc = report["source_scope"]
        self.assertEqual(sc["archived_benchmark_mechanical_only"], 1)
        self.assertEqual(sc["nonarchive_mechanical_unproved"], 0)
        self.assertEqual(sc["semantically_admitted_executable_originals"], 0)
        self.assertEqual(report["migrator_summary"]["files_would_write"], 1)
        self.assertFalse(report["physical_outputs_created"])
        archived = [row for row in report["candidate_rows"]
                    if row["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM"]
        self.assertEqual(len(archived), 1)
        self.assertFalse(archived[0]["semantic_oracle_admitted"])

    def test_missing_oracle_evidence_is_not_marked_as_executable(self):
        _, fn = fake_migrator_call()
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertIn("research-only", report["authority"])
        self.assertIn("BLOCKED", report["gate"]["rule"])
        self.assertNotIn("oracle_passed", report)


    def test_real_pinned_data_registry_covers_all_reviewed_cohorts(self):
        from report_original_migration_candidates import NONPROGRAM_MANIFESTS
        rows = REAL_REVIEWED_LOADER(ROOT)
        # Manifest SHAs/allowed cohorts are authority; do not freeze the
        # research inventory at 76/78 when additional DATA is proven.
        expected = {
            name: count for name, manifest, count in NONPROGRAM_MANIFESTS
            if (ROOT / manifest).is_file()
        }
        self.assertEqual(len(rows), sum(expected.values()))
        cohort_counts = {
            name: sum(item["cohort"] == name for item in rows.values())
            for name in expected
        }
        self.assertEqual(cohort_counts, expected)
        self.assertEqual(expected["comment-only-loader"], 2)
        self.assertEqual(expected["knowledge-record"], 14)
        self.assertNotIn("lib/machine/block.lisp", rows)
        self.assertEqual({p for p, item in rows.items() if item["cohort"] == "comment-only-loader"},
                         {"lib/core2.lisp", "lib/surface/ukr.lisp"})
        for path in ("lib/core2.lisp", "lib/surface/ukr.lisp"):
            self.assertFalse((ROOT / path).with_suffix(".sens").exists(),
                             "comment-only profile marker must not receive executable .sens")
        self.assertTrue(all(
            item["source_class"] == "NONPROGRAM_DATA_REVIEWED"
            and not item["semantic_oracle_admitted"]
            and not item["automatic_sens_companion"]
            for item in rows.values()
        ))

    def test_three_era_data_partition_never_reduces_raw_migration_blocks(self):
        observed, fn = fake_migrator_call()
        path = "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
        verified = {
            path: {
                "path": path,
                "source_git_blob_sha": census.git_blob_sha(ROOT / path),
                "source_class": "NONPROGRAM_DATA_REVIEWED",
                "cohort": "expr-record",
                "semantic_oracle_admitted": False,
                "automatic_sens_companion": False,
            }
        }
        with patch.object(census.subprocess, "run", side_effect=fn), patch.object(
            census, "load_nonprogram_classification", return_value=verified
        ):
            report = census.build_report()
        self.assertTrue(report["gate"]["pass"])
        self.assertEqual(report["migrator_summary"]["files_blocked"], 2)
        self.assertEqual(report["source_scope"]["reviewed_nonprogram_originals"], 1)
        self.assertEqual(report["source_scope"]["active_or_unknown_originals"], 1)
        self.assertEqual(sum(report["actionable_executable_unknown_queues"].values()), 1)
        self.assertEqual(report["physical_outputs_created"], [])
        self.assertEqual(next(r for r in report["candidate_rows"]
                              if r["path"] == path)["source_scope"],
                         "NONPROGRAM_DATA_REVIEWED")
        self.assertFalse(report["candidate_rows"][0]["semantic_oracle_admitted"])

    def test_nonprogram_manifest_mismatch_does_not_hide_any_failed_source(self):
        _, fn = fake_migrator_call()
        missing = {
            "fake.lisp": {
                "path": "fake.lisp", "source_git_blob_sha": "a"*40,
                "source_class": "NONPROGRAM_DATA_REVIEWED",
                "cohort": "isa", "semantic_oracle_admitted": False,
                "automatic_sens_companion": False
            }
        }
        with patch.object(census.subprocess, "run", side_effect=fn), patch.object(
            census, "load_nonprogram_classification", return_value=missing
        ):
            with self.assertRaisesRegex(RuntimeError, "missing from unpaired"):
                census.build_report()

    def test_nonprogram_drift_rejected_after_manifest_load(self):
        _, fn = fake_migrator_call()
        source = "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
        stale = {
            source: {
                "path": source, "source_git_blob_sha": "a"*40,
                "source_class": "NONPROGRAM_DATA_REVIEWED",
                "cohort": "expr-record", "semantic_oracle_admitted": False,
                "automatic_sens_companion": False
            }
        }
        with patch.object(census.subprocess, "run", side_effect=fn), patch.object(
            census, "load_nonprogram_classification", return_value=stale
        ):
            with self.assertRaisesRegex(RuntimeError, "SHA mismatch"):
                census.build_report()


if __name__ == "__main__":
    unittest.main()
