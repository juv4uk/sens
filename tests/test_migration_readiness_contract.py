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


def fake_migrator_call(*, newly_eligible=0, archived=False):
    """Write a report in the location selected by census; never touch lib/."""
    observed = []

    def run(argv, **kwargs):
        observed.extend(argv)
        assert kwargs["cwd"] == ROOT
        assert kwargs["timeout"] == 180
        out = Path(argv[argv.index("--report") + 1])
        blocked = 2 - newly_eligible
        archive_path = "benchmarks/sens-surface/results/20260925-icount-33bfb53a/programs/empty-en.lisp"
        state = {
            "schema": "sens-migration-three-pass/v1",
            "authority": {"foundation_sha256": "mock-ratified-sha256"},
            "summary": {
                "files_seen": 2,
                "files_written": 0,
                "files_would_write": newly_eligible,
                "files_blocked": blocked,
            },
            "skipped_paired_paths": ["tests/fixtures/core1-domain-canary/second.lisp"],
            "files": [
                {"path": "lib/old-1.lisp", "status": "blocked",
                 "reason": "ambiguous W8 executable head 00000001: choose source era"},
                {"path": "lib/old-2.lisp", "status": "blocked",
                 "reason": "legacy unmapped function: no current law"},
            ][:blocked] + ([
                {"path": archive_path if archived else "lib/admitted-unverified.lisp",
                 "status": "would-write", "bytes":4, "physical_sha256": "a"*64,
                 "typed_word_sha256": "b"*64, "semantic_word_count": 5}
            ] if newly_eligible else []),
        }
        out.write_text(json.dumps(state), encoding="utf-8")
        return SimpleNamespace(returncode=2, stdout="", stderr="")

    return observed, run


class ReadinessContractTests(unittest.TestCase):
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

    def test_only_archived_snapshot_mechanically_eligible_does_not_block_active_gate(self):
        _, fn = fake_migrator_call(newly_eligible=1, archived=True)
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertTrue(report["gate"]["pass"])
        self.assertEqual(report["source_scope"]["archived_benchmark_mechanically_eligible"], 1)
        self.assertEqual(report["source_scope"]["active_or_unclassified_mechanically_eligible"], 0)
        self.assertEqual(report["source_scope"]["executable_originals_semantically_certified"], 0)
        self.assertEqual(report["migrator_summary"]["files_would_write"], 1)
        self.assertEqual(report["physical_outputs_created"], [])

    def test_work_queue_assigns_unresolved_w8_to_provenance_not_d8(self):
        _, fn = fake_migrator_call()
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        work = {q["cohort"]: q for q in report["agent_work_queue"]}
        self.assertIn("W8_ERA_PROVENANCE", work)
        self.assertEqual(work["W8_ERA_PROVENANCE"]["blocked_count"], 1)
        self.assertEqual(work["W8_ERA_PROVENANCE"]["examples"][0]["path"], "lib/old-1.lisp")

    def test_missing_oracle_evidence_is_not_marked_as_executable(self):
        _, fn = fake_migrator_call()
        with patch.object(census.subprocess, "run", side_effect=fn):
            report = census.build_report()
        self.assertIn("research-only", report["authority"])
        self.assertIn("BLOCKED", report["gate"]["rule"])
        self.assertNotIn("oracle_passed", report)


if __name__ == "__main__":
    unittest.main()
