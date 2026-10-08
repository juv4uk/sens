#!/usr/bin/env python3
"""Proof that SECOND W8 blockers are a safe no-write observation, never approval."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/triage_w8_legacy_successors.py"
spec = importlib.util.spec_from_file_location("w8_next_barriers", SCRIPT)
assert spec is not None and spec.loader is not None
triage = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = triage
spec.loader.exec_module(triage)


class W8SecondBarrierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="w8-next-test-")
        self.root = Path(self.tmp.name)
        for name in ("old.lisp", "later.lisp", "changed.lisp"):
            (self.root / name).write_text("(historical ())\n", encoding="utf-8")
        self.sha = triage.source_git_blob(self.root / "old.lisp")
        self.proof = {
            "schema": triage.origin.SCHEMA,
            "baseline_pre_d8_commit": triage.origin.BASELINE,
            "summary": {"SAME_BLOB_BEFORE_D8_RATIFICATION": 1},
            "sources": [
                {"path":"old.lisp", "source_git_blob_sha":self.sha,
                 "provenance":"SAME_BLOB_BEFORE_D8_RATIFICATION",
                 "w8_first_blocker":"00001001"},
                {"path":"later.lisp", "source_git_blob_sha":self.sha,
                 "provenance":"NOT_PRESENT_IN_PRE_D8_SNAPSHOT",
                 "w8_first_blocker":"00001011"},
            ],
        }
        self.replay = {
            "mode":"dry-run","source_era":"legacy","only_unpaired":True,
            "summary":{"files_written":0,"files_seen":2},
            "files":[
                {"path":"old.lisp","status":"blocked",
                 "reason":"legacy-unmapped SID8/Sens8 00100010: no current resident"},
                {"path":"later.lisp","status":"blocked",
                 "reason":"word 2: non-bit token"},
            ],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_join(self):
        return triage.join_provenance_and_legacy(self.proof,self.replay,self.root)

    def test_full_current_repo_has_frozen_pre_d8_source_tree(self):
        tree = triage.origin.tree_blobs(ROOT, triage.origin.BASELINE)
        self.assertEqual(tree.get("lib/core1.lisp"),
                         "a2f184373428bc516a0b03491dfabfb3255d07ef")

    def test_only_exact_same_blob_enters_second_barrier(self):
        result=self.run_join()
        self.assertEqual(result["summary"]["w8_first_blocked_originals"],2)
        self.assertEqual(result["summary"]["chronology_proven_same_blob"],1)
        self.assertEqual(result["summary"]["hypothetical_second_blocked"],1)
        self.assertEqual(result["summary"]["physical_outputs_created"],0)
        self.assertEqual(result["summary"]["current_semantic_admissions"],0)
        self.assertEqual(result["next_barrier_cohorts"][0]["family"],"UNMAPPED_LEGACY_SID8")
        self.assertEqual(result["next_barrier_cohorts"][0]["coordinate"],"00100010")
        self.assertEqual([r["path"] for r in result["sources"]],["old.lisp"])
        self.assertFalse(result["sources"][0]["current_source_era_permission"])

    def test_hypothetical_candidate_is_never_original_admission(self):
        self.replay["files"][0]={"path":"old.lisp","status":"would-write",
                                  "physical_sha256":"0"*64}
        r=self.run_join()
        self.assertEqual(r["summary"]["hypothetical_mechanical_candidates_only"],1)
        self.assertEqual(r["summary"]["current_semantic_admissions"],0)
        self.assertEqual(r["sources"][0]["next_family"],"MECHANICAL_CANDIDATE_ONLY")
        self.assertEqual(r["sources"][0]["current_semantic_oracle"],"NOT_VERIFIED")

    def test_wrong_original_sha_blocks_even_if_legacy_report_is_valid(self):
        self.proof["sources"][0]["source_git_blob_sha"]="e"*40
        with self.assertRaisesRegex(triage.TriageError,"source SHA drift"):
            self.run_join()

    def test_missing_or_duplicate_canonical_replay_blocks(self):
        self.replay["files"]=[self.replay["files"][1]]
        self.replay["summary"]["files_seen"]=1
        with self.assertRaisesRegex(triage.TriageError,"missing from legacy dry-run"):
            self.run_join()
        self.replay["files"]=[{"path":"old.lisp","status":"blocked","reason":"x"}]*2
        self.replay["summary"]["files_seen"]=2
        with self.assertRaisesRegex(triage.TriageError,"duplicate"):
            self.run_join()

    def test_invalid_replay_mode_or_write_blocks(self):
        self.replay["mode"]="write-new-only"
        with self.assertRaisesRegex(triage.TriageError,"LEGACY dry-run"):
            self.run_join()
        self.replay["mode"]="dry-run"
        self.replay["summary"]["files_written"]=1
        with self.assertRaisesRegex(triage.TriageError,"never publish"):
            self.run_join()

    def test_missing_reason_or_unsafe_path_blocks(self):
        self.replay["files"][0]["reason"]=""
        with self.assertRaisesRegex(triage.TriageError,"no auditable next reason"):
            self.run_join()
        self.replay["files"][0]["reason"]="bad"
        self.proof["sources"][0]["path"]="../old.lisp"
        with self.assertRaisesRegex(triage.TriageError,"unsafe or unpinned"):
            self.run_join()

    def test_nonbinary_next_barrier_by_word_position(self):
        for value,expected in (
            ("word 2: non-bit",("NON_BINARY_OR_UNTYPED","word2")),
            ("word 3: non-bit",("NON_BINARY_OR_UNTYPED","word3")),
            ("legacy-unmapped SID8/Sens8 00100010",("UNMAPPED_LEGACY_SID8","00100010")),
            ("D2 word 10 structural control",("D2_STRUCTURE_UNPROVED","D2")),
        ):
            self.assertEqual(triage.next_barrier(value),expected)


    def scoped_census(self, kind="UNCLASSIFIED_NEEDS_SOURCE_PROOF"):
        row = {
            "path": "old.lisp", "source_git_blob_sha": self.sha,
            "status": "BLOCKED",
            "same_stem_sens_already_exists": False,
            "independent_semantic_oracle_passed": False,
            "source_is_executable_proven": False,
            "source_scope": kind, "reason": "ambiguous W8 executable head 00001001",
        }
        return {
            "source_era": "auto",
            "summary": {
                "blocked": 1, "physical_outputs_created": 0,
                "original_unpaired_executables_migrated_by_this_tool": 0,
                "classified_nonprogram": int(kind == "NONPROGRAM_DATA_REVIEWED"),
                "archived_benchmark_data_sources": int(kind == "ARCHIVED_BENCHMARK_NONPROGRAM"),
            },
            "blocked_sources": [row],
            "reviewed_nonprogram_sources": (
                [{
                    "path": "old.lisp", "source_git_blob_sha": self.sha,
                    "source_class": "NONPROGRAM_DATA_REVIEWED",
                    "automatic_sens_companion": False,
                    "semantic_oracle_admitted": False,
                }] if kind == "NONPROGRAM_DATA_REVIEWED" else []
            ),
        }

    def test_real_candidate_scope_remains_unproved_not_executable(self):
        result = triage.add_owner_reviewed_source_scope(
            self.run_join(), self.scoped_census()
        )
        self.assertEqual(result["summary"]["chronology_proven_same_blob"], 1)
        self.assertEqual(result["summary"]["executable_or_unclassified_next_barrier_originals"], 1)
        self.assertEqual(result["summary"]["data_only_next_barrier_originals"], 0)
        self.assertEqual(result["sources"][0]["work_lane"],
                         "EXECUTABLE_OR_UNCLASSIFIED_NEEDS_ORACLE")
        self.assertFalse(result["sources"][0]["release_admitted"])
        self.assertEqual(result["summary"]["physical_outputs_created"], 0)
        self.assertEqual(result["summary"]["current_semantic_admissions"], 0)

    def test_owner_reviewed_data_never_enqueued_for_executable_conversion(self):
        result = triage.add_owner_reviewed_source_scope(
            self.run_join(), self.scoped_census("NONPROGRAM_DATA_REVIEWED")
        )
        self.assertEqual(result["summary"]["data_only_next_barrier_originals"], 1)
        self.assertEqual(result["summary"]["executable_or_unclassified_next_barrier_originals"], 0)
        self.assertEqual(result["sources"][0]["work_lane"], "DATA_CONTRACT_NO_EXECUTABLE_T5")
        self.assertEqual(result["source_scope_next_barrier_cohorts"][0]["count"], 1)
        self.assertFalse(result["sources"][0]["current_source_era_permission"])

    def test_archived_benchmark_scope_requires_actual_owner_path_law(self):
        from migration_source_scope import archived_benchmark_source
        correct = ("benchmarks/sens-surface/results/"
                   "20260925-icount-33bfb53a/programs/old.lisp")
        self.assertTrue(archived_benchmark_source(correct))
        result = self.run_join()
        result["sources"][0]["path"] = correct
        census = self.scoped_census("ARCHIVED_BENCHMARK_NONPROGRAM")
        census["blocked_sources"][0]["path"] = correct
        scoped = triage.add_owner_reviewed_source_scope(result, census)
        self.assertEqual(scoped["summary"]["data_only_next_barrier_originals"], 1)
        with self.assertRaisesRegex(triage.TriageError, "archive source-scope"):
            triage.add_owner_reviewed_source_scope(
                self.run_join(),
                self.scoped_census("ARCHIVED_BENCHMARK_NONPROGRAM")
            )

    def _append_mechanical_candidate(self, census, path, kind, sha="b"*40):
        census.setdefault("mechanical_candidates", []).append({
            "path": path, "source_git_blob_sha": sha,
            "status": "CANDIDATE_NOT_ADMITTED",
            "same_stem_sens_already_exists": False,
            "independent_semantic_oracle_passed": False,
            "source_is_executable_proven": False,
            "source_scope": kind,
        })
        census["summary"]["mechanical_candidates"] = len(census["mechanical_candidates"])
        census["summary"]["scanned"] = (len(census["blocked_sources"])
                                         + len(census["mechanical_candidates"]))
        return census["mechanical_candidates"][-1]

    def test_archive_mechanical_candidate_is_still_data_not_a_false_total_drift(self):
        # Audited successor laws may mechanically admit a frozen measurement,
        # but it must stay DATA and not invalidate 197 W8 blocked originals.
        archive = ("benchmarks/sens-surface/results/"
                   "20260925-icount-33bfb53a/programs/empty-en.lisp")
        census = self.scoped_census()
        self._append_mechanical_candidate(
            census, archive, "ARCHIVED_BENCHMARK_NONPROGRAM")
        census["summary"]["archived_benchmark_data_sources"] = 1
        result = triage.add_owner_reviewed_source_scope(self.run_join(), census)
        self.assertEqual(result["summary"]["chronology_proven_same_blob"], 1)
        self.assertEqual(result["summary"]["data_only_next_barrier_originals"], 0)
        self.assertEqual(result["summary"]["executable_or_unclassified_next_barrier_originals"], 1)
        self.assertEqual(result["sources"][0]["path"], "old.lisp")
        self.assertFalse(result["sources"][0]["release_admitted"])
        self.assertEqual(result["summary"]["physical_outputs_created"], 0)

    def test_forged_archive_candidate_and_counts_fail_closed(self):
        archive = ("benchmarks/sens-surface/results/"
                   "20260925-icount-33bfb53a/programs/empty-en.lisp")
        census = self.scoped_census()
        row = self._append_mechanical_candidate(
            census, archive, "ARCHIVED_BENCHMARK_NONPROGRAM")
        census["summary"]["archived_benchmark_data_sources"] = 1
        row["source_scope"] = "UNCLASSIFIED_NEEDS_SOURCE_PROOF"
        with self.assertRaisesRegex(triage.TriageError, "archive source-scope"):
            triage.add_owner_reviewed_source_scope(self.run_join(), census)
        row["source_scope"] = "ARCHIVED_BENCHMARK_NONPROGRAM"
        row["status"] = "BLOCKED"
        with self.assertRaisesRegex(triage.TriageError, "unapproved original"):
            triage.add_owner_reviewed_source_scope(self.run_join(), census)
        row["status"] = "CANDIDATE_NOT_ADMITTED"
        row["source_is_executable_proven"] = True
        with self.assertRaisesRegex(triage.TriageError, "unapproved original"):
            triage.add_owner_reviewed_source_scope(self.run_join(), census)
        row["source_is_executable_proven"] = False
        census["summary"]["mechanical_candidates"] = 0
        with self.assertRaisesRegex(triage.TriageError, "candidate total changed"):
            triage.add_owner_reviewed_source_scope(self.run_join(), census)
        census["summary"]["mechanical_candidates"] = 1
        census["summary"]["scanned"] = 1
        with self.assertRaisesRegex(triage.TriageError, "total includes"):
            triage.add_owner_reviewed_source_scope(self.run_join(), census)
        census["summary"]["scanned"] = 2
        census["mechanical_candidates"].append(dict(row))
        census["summary"]["mechanical_candidates"] = 2
        census["summary"]["scanned"] = 3
        with self.assertRaisesRegex(triage.TriageError, "duplicate"):
            triage.add_owner_reviewed_source_scope(self.run_join(), census)

    def test_reviewed_nonprogram_candidate_keeps_pinned_data_policy(self):
        census = self.scoped_census()
        name = "lib/machine/isa/adx.lisp"
        sha = "c"*40
        row = self._append_mechanical_candidate(
            census, name, "NONPROGRAM_DATA_REVIEWED", sha)
        census["summary"]["classified_nonprogram"] = 1
        census["reviewed_nonprogram_sources"] = [{
            "path": name, "source_git_blob_sha": sha,
            "source_class": "NONPROGRAM_DATA_REVIEWED",
            "automatic_sens_companion": False,
            "semantic_oracle_admitted": False,
        }]
        result = triage.add_owner_reviewed_source_scope(self.run_join(), census)
        self.assertEqual(result["summary"]["current_semantic_admissions"], 0)
        row["source_git_blob_sha"] = "d"*40
        with self.assertRaisesRegex(triage.TriageError, "Git SHA differs"):
            triage.add_owner_reviewed_source_scope(self.run_join(), census)

    def test_fake_data_classification_or_stale_source_sha_fails_closed(self):
        report = self.run_join()
        forged = self.scoped_census("NONPROGRAM_DATA_REVIEWED")
        forged["reviewed_nonprogram_sources"] = []
        with self.assertRaisesRegex(triage.TriageError, "manifest total|owner-reviewed"):
            triage.add_owner_reviewed_source_scope(report, forged)
        stale = self.scoped_census()
        stale["blocked_sources"][0]["source_git_blob_sha"] = "0"*40
        with self.assertRaisesRegex(triage.TriageError, "Git SHA differs"):
            triage.add_owner_reviewed_source_scope(report, stale)
        doubled = self.scoped_census()
        doubled["blocked_sources"].append(dict(doubled["blocked_sources"][0]))
        doubled["summary"]["blocked"] = 2
        with self.assertRaisesRegex(triage.TriageError, "duplicate"):
            triage.add_owner_reviewed_source_scope(report, doubled)

    def test_source_scope_cannot_override_canonical_auto_or_oracle(self):
        report = self.run_join()
        malformed = self.scoped_census()
        malformed["source_era"] = "legacy"
        with self.assertRaisesRegex(triage.TriageError, "source-era auto"):
            triage.add_owner_reviewed_source_scope(report, malformed)
        malformed = self.scoped_census()
        malformed["blocked_sources"][0]["source_is_executable_proven"] = True
        with self.assertRaisesRegex(triage.TriageError, "unapproved original"):
            triage.add_owner_reviewed_source_scope(report, malformed)

    def test_canonical_legacy_replay_cannot_mint_output(self):
        source = (self.root / "scripts")
        source.mkdir()
        (source / "migrate-three-pass.py").write_text("raise SystemExit(2)\n")
        with patch.object(triage.subprocess,"run",return_value=subprocess.CompletedProcess(
            ["python"], 2, "", "failed input")):
            with self.assertRaisesRegex(triage.TriageError,"missing/crashed"):
                triage.canonical_legacy_replay(self.root,self.root)


if __name__=="__main__":
    unittest.main()
