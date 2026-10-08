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
