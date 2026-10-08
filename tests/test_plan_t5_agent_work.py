#!/usr/bin/env python3
"""Safety/coverage regressions for read-only agent migration shard planner."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "plan_t5_agent_work.py"
spec = importlib.util.spec_from_file_location("t5_agent_plan", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture() -> dict:
    pin = "a" * 40
    blocked = [
        {"path": f"lib/old{i}.lisp", "source_git_blob_sha": f"{i+1:040x}",
         "first_blocker": "ambiguous W8: unknown source era"}
        for i in range(3)
    ]
    return {
        "schema": mod.SOURCE_SCHEMA,
        "mode": "read-only canonical migrator dry-run",
        "source_era": "auto",
        "summary": {
            "scanned": 4, "original_unpaired_sources_scanned": 4,
            "blocked": 3, "mechanical_candidates": 1,
            "unpaired_candidates_needing_original_oracle": 1,
            "already_paired_candidates": 0,
            "physical_outputs_created": 0,
            "original_unpaired_executables_migrated_by_this_tool": 0,
        },
        "blocked_sources": [
            {"path": row["path"], "source_git_blob_sha": row["source_git_blob_sha"],
             "reason": row["first_blocker"], "status": "BLOCKED",
             "same_stem_sens_already_exists": False,
             "source_is_executable_proven": False,
             "independent_semantic_oracle_passed": False}
            for row in blocked
        ],
        "blocker_cohorts": [{
            "family": "w8-provenance", "status": "BLOCKED_NOT_ORACLE_ADMITTED",
            "count": 3, "next_action": "Pin historic source-era Git witness",
            "original_sources": blocked,
        }],
        "mechanical_candidates": [{
            "path": "test/ready.lisp", "source_git_blob_sha": pin,
            "same_stem_sens_already_exists": False,
            "source_is_executable_proven": False,
            "independent_semantic_oracle_passed": False,
            "status": "CANDIDATE_NOT_ADMITTED",
        }],
    }


class PlanT5AgentWorkTests(unittest.TestCase):
    def test_all_sources_exactly_once_and_exclusive_family_shards(self):
        r = mod.build_plan(fixture(), 2)
        self.assertEqual(r["schema"], mod.OUTPUT_SCHEMA)
        self.assertEqual(r["summary"]["original_unpaired"], 4)
        self.assertEqual(r["summary"]["blocked"], 3)
        self.assertEqual(r["summary"]["mechanical_pending_oracle"], 1)
        self.assertEqual(r["summary"]["archived_mechanical_nonprogram_originals"], 0)
        self.assertEqual(r["summary"]["claimed"], 0)
        self.assertEqual(r["summary"]["admitted"], 0)
        shards = r["shards"]
        self.assertEqual(len(shards), 3)
        self.assertEqual([s["source_count"] for s in shards], [2, 1, 1])
        self.assertEqual([s["shard_id"] for s in shards],
                         ["w8-provenance-001", "w8-provenance-002", "oracle-pending-001"])
        flattened = [row["path"] for s in shards for row in s["sources"]]
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(set(flattened),
                         {"lib/old0.lisp","lib/old1.lisp","lib/old2.lisp","test/ready.lisp"})
        self.assertTrue(all(s["claimed_by"] is None for s in shards))
        self.assertTrue(all(s["status"] == mod.SHARD_STATUS for s in shards))
        self.assertTrue(all(s["release_gate"] == "NO_OUTPUT_UNTIL_INDEPENDENT_SEMANTIC_ORACLE"
                            for s in shards))

    def test_output_is_deterministic_independent_of_input_row_order(self):
        a = fixture()
        b = fixture()
        b["blocker_cohorts"][0]["original_sources"].reverse()
        self.assertEqual(mod.build_plan(a, 2), mod.build_plan(b, 2))

    def test_reviewed_nonprogram_original_gets_separate_no_t5_data_shard(self):
        a = fixture()
        src = a["blocked_sources"][0]
        src["source_scope"] = "NONPROGRAM_DATA_REVIEWED"
        src["automatic_sens_companion"] = False
        a["reviewed_nonprogram_sources"] = [{
            "path": src["path"],
            "source_git_blob_sha": src["source_git_blob_sha"],
            "source_class": "NONPROGRAM_DATA_REVIEWED",
            "automatic_sens_companion": False,
            "semantic_oracle_admitted": False,
        }]
        a["summary"]["classified_nonprogram"] = 1
        plan = mod.build_plan(a, 2)
        self.assertEqual(plan["summary"]["original_unpaired"], 4)
        self.assertEqual(plan["summary"]["reviewed_nonprogram_originals"], 1)
        self.assertEqual(plan["summary"]["executable_or_unclassified_originals"], 3)
        data = [x for x in plan["shards"] if x["family"] == "reviewed-nonprogram-data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["source_count"], 1)
        self.assertEqual(data[0]["sources"][0]["path"], src["path"])
        self.assertEqual(data[0]["release_gate"], "DATA_CONTRACT_NO_EXECUTABLE_T5")
        self.assertEqual(data[0]["status"], "UNCLAIMED__NONPROGRAM_DATA_ONLY")
        other = [x for x in plan["shards"] if x["family"] != "reviewed-nonprogram-data"]
        self.assertTrue(all(x["release_gate"] == "NO_OUTPUT_UNTIL_INDEPENDENT_SEMANTIC_ORACLE"
                            for x in other))
        seen = [x["path"] for shard in plan["shards"] for x in shard["sources"]]
        self.assertEqual(len(seen), 4)
        self.assertEqual(len(set(seen)), 4)

    def test_nonprogram_classification_must_equal_canonical_sha_and_policy(self):
        variants = ("wrong-pin", "wrong-source", "duplicate", "unreviewed",
                    "automatic-publish", "oracle-claim", "missing-canonical-label",
                    "incorrect-count", "missing-records", "candidate-reclassified")
        for variant in variants:
            a = fixture()
            src = a["blocked_sources"][0]
            src["source_scope"] = "NONPROGRAM_DATA_REVIEWED"
            src["automatic_sens_companion"] = False
            row = {
                "path": src["path"],
                "source_git_blob_sha": src["source_git_blob_sha"],
                "source_class": "NONPROGRAM_DATA_REVIEWED",
                "automatic_sens_companion": False,
                "semantic_oracle_admitted": False,
            }
            a["reviewed_nonprogram_sources"] = [row]
            a["summary"]["classified_nonprogram"] = 1
            if variant == "wrong-pin":
                row["source_git_blob_sha"] = "f" * 40
            elif variant == "wrong-source":
                row["path"] = "lib/not-canonical.lisp"
            elif variant == "duplicate":
                a["reviewed_nonprogram_sources"].append(dict(row))
                a["summary"]["classified_nonprogram"] = 2
            elif variant == "unreviewed":
                row["source_class"] = "EXECUTABLE"
            elif variant == "automatic-publish":
                row["automatic_sens_companion"] = True
            elif variant == "oracle-claim":
                row["semantic_oracle_admitted"] = True
            elif variant == "missing-canonical-label":
                src.pop("source_scope")
            elif variant == "incorrect-count":
                a["summary"]["classified_nonprogram"] = 2
            elif variant == "missing-records":
                a.pop("reviewed_nonprogram_sources")
            else:
                row["path"] = "test/ready.lisp"
                row["source_git_blob_sha"] = "a" * 40
            with self.subTest(variant=variant), self.assertRaises(mod.PlanError):
                mod.build_plan(a, 2)

    def test_simultaneous_conflicting_old_and_current_classifications_fail_closed(self):
        a = fixture()
        src = a["blocked_sources"][0]
        src["source_scope"] = "NONPROGRAM_DATA_REVIEWED"
        src["automatic_sens_companion"] = False
        reviewed = [{
            "path": src["path"],
            "source_git_blob_sha": src["source_git_blob_sha"],
            "source_class": "NONPROGRAM_DATA_REVIEWED",
            "automatic_sens_companion": False,
            "semantic_oracle_admitted": False,
        }]
        a["reviewed_nonprogram_sources"] = reviewed
        a["nonprogram_classification"] = [dict(reviewed[0],
                                               source_git_blob_sha="f" * 40)]
        a["summary"]["classified_nonprogram"] = 1
        with self.assertRaisesRegex(mod.PlanError, "conflicting"):
            mod.build_plan(a, 2)

    def test_sha_pinned_archived_benchmark_gets_data_only_shard(self):
        a = fixture()
        archived = ("benchmarks/sens-surface/results/"
                    "20260925-icount-33bfb53a/programs/empty-en.lisp")
        a["blocked_sources"][0]["path"] = archived
        a["blocked_sources"][0]["source_git_blob_sha"] = "6e30e07f9a44391fb341f5e0ff21ba1e682b5d0f"
        a["blocked_sources"][0]["source_scope"] = "ARCHIVED_BENCHMARK_NONPROGRAM"
        a["blocker_cohorts"][0]["original_sources"][0]["path"] = archived
        a["blocker_cohorts"][0]["original_sources"][0]["source_git_blob_sha"] = "6e30e07f9a44391fb341f5e0ff21ba1e682b5d0f"
        a["summary"]["archived_benchmark_data_sources"] = 1
        result = mod.build_plan(a, 2)
        archive = [shard for shard in result["shards"]
                   if shard["family"] == "archived-benchmark-data"]
        self.assertEqual(len(archive), 1)
        self.assertEqual(archive[0]["status"], "UNCLAIMED__NONPROGRAM_DATA_ONLY")
        self.assertEqual(archive[0]["release_gate"], "DATA_CONTRACT_NO_EXECUTABLE_T5")
        self.assertEqual(archive[0]["sources"][0]["path"], archived)
        self.assertEqual(result["summary"]["archived_benchmark_nonprogram_originals"], 1)
        self.assertEqual(result["summary"]["executable_or_unclassified_originals"], 3)
        self.assertEqual(result["summary"]["original_unpaired"], 4)

    def test_mechanically_convertible_archive_does_not_enter_oracle_worker(self):
        a = fixture()
        archived = ("benchmarks/sens-surface/results/"
                    "20260925-icount-33bfb53a/programs/empty-en.lisp")
        a["mechanical_candidates"][0]["path"] = archived
        a["mechanical_candidates"][0]["source_git_blob_sha"] = "6e30e07f9a44391fb341f5e0ff21ba1e682b5d0f"
        a["mechanical_candidates"][0]["source_scope"] = "ARCHIVED_BENCHMARK_NONPROGRAM"
        a["summary"]["archived_benchmark_data_sources"] = 1
        a["summary"]["unpaired_candidates_needing_original_oracle"] = 0
        result = mod.build_plan(a, 2)
        self.assertEqual(result["summary"]["mechanical_pending_oracle"], 0)
        self.assertEqual(result["summary"]["archived_mechanical_nonprogram_originals"], 1)
        self.assertEqual(result["summary"]["original_unpaired"], (
            result["summary"]["blocked"]
            + result["summary"]["mechanical_pending_oracle"]
            + result["summary"]["archived_mechanical_nonprogram_originals"]))
        self.assertFalse(any(x["family"] == "oracle-pending" for x in result["shards"]))
        self.assertEqual(result["summary"]["archived_benchmark_nonprogram_originals"], 1)
        self.assertTrue(any(shard["family"] == "archived-benchmark-data"
                            and shard["sources"][0]["path"] == archived
                            for shard in result["shards"]))

    def test_archived_scope_cannot_be_forged_from_active_source(self):
        a = fixture()
        a["blocked_sources"][0]["source_scope"] = "ARCHIVED_BENCHMARK_NONPROGRAM"
        with self.assertRaisesRegex(mod.PlanError, "forged archive"):
            mod.build_plan(a, 2)

    def test_no_paired_source_or_duplicate_can_enter_plan(self):
        a = fixture()
        a["blocker_cohorts"][0]["original_sources"][0]["path"] = "test/ready.lisp"
        with self.assertRaisesRegex(mod.PlanError, "canonical ledger"):
            mod.build_plan(a, 2)
        a = fixture()
        a["mechanical_candidates"][0]["same_stem_sens_already_exists"] = True
        with self.assertRaisesRegex(mod.PlanError, "paired"):
            mod.build_plan(a, 2)

    def test_invalid_status_or_missing_authority_is_blocked(self):
        a = fixture()
        a["source_era"] = "legacy"
        with self.assertRaisesRegex(mod.PlanError, "auto"):
            mod.build_plan(a)
        a = fixture()
        a["summary"]["physical_outputs_created"] = 1
        with self.assertRaisesRegex(mod.PlanError, "physical output"):
            mod.build_plan(a)
        a = fixture()
        a["mechanical_candidates"][0]["independent_semantic_oracle_passed"] = True
        with self.assertRaisesRegex(mod.PlanError, "unauthorized"):
            mod.build_plan(a)

    def test_counts_and_paths_fail_closed(self):
        for change in ("counts", "dotdot", "bytepin", "badstatus"):
            a = fixture()
            if change == "counts":
                a["summary"]["scanned"] = 0
            elif change == "dotdot":
                a["blocker_cohorts"][0]["original_sources"][0]["path"] = "../escape.lisp"
            elif change == "bytepin":
                a["mechanical_candidates"][0]["source_git_blob_sha"] = "bad"
            else:
                a["blocker_cohorts"][0]["status"] = "ORACLE_ADMITTED"
            with self.subTest(change=change), self.assertRaises(mod.PlanError):
                mod.build_plan(a, 2)
        for n in [0, 101]:
            with self.assertRaises(mod.PlanError):
                mod.build_plan(fixture(), n)

    def test_cohort_shas_and_first_blockers_must_match_original_ledger(self):
        cases = ("sha-swap", "reason-swap", "extra-cohort", "missing-original",
                 "duplicate-original", "missing-ledger", "status-forgery",
                 "wrong-original-sha")
        for case in cases:
            state = fixture()
            cohort_rows = state["blocker_cohorts"][0]["original_sources"]
            original_rows = state["blocked_sources"]
            if case == "sha-swap":
                cohort_rows[0]["source_git_blob_sha"] = "0" * 40
            elif case == "reason-swap":
                cohort_rows[0]["first_blocker"] = "unknown PRINT host effect"
            elif case == "extra-cohort":
                cohort_rows[0]["path"] = "lib/forged.lisp"
            elif case == "missing-original":
                original_rows.pop()
            elif case == "duplicate-original":
                original_rows[1] = dict(original_rows[0])
            elif case == "missing-ledger":
                del state["blocked_sources"]
            elif case == "status-forgery":
                original_rows[0]["status"] = "CANDIDATE_NOT_ADMITTED"
            elif case == "wrong-original-sha":
                original_rows[0]["source_git_blob_sha"] = "f" * 40
            with self.subTest(case=case), self.assertRaises(mod.PlanError):
                mod.build_plan(state, 2)

    def test_git_head_source_identity_is_not_forgeable_by_consistent_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"],
                           cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test Runner"],
                           cwd=root, check=True)
            state = fixture()
            paths = state["blocked_sources"] + state["mechanical_candidates"]
            for row in paths:
                source = root / row["path"]
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("(001 ())\n", encoding="utf-8")
                row["source_git_blob_sha"] = git_blob = mod.hashlib.sha1(
                    b"blob 9\0(001 ())\n").hexdigest()
                for cohort in state["blocker_cohorts"]:
                    for member in cohort["original_sources"]:
                        if member["path"] == row["path"]:
                            member["source_git_blob_sha"] = git_blob
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "source originals"], cwd=root,
                           check=True)
            self.assertIsNone(mod.assert_original_git_head_parity(root, state))

            # Both report sections forged together: previous JSON-only planner
            # accepted the claim. The Git-backed CLI MUST reject it.
            forged = json.loads(json.dumps(state))
            forged["blocked_sources"][0]["source_git_blob_sha"] = "f"*40
            forged["blocker_cohorts"][0]["original_sources"][0]["source_git_blob_sha"] = "f"*40
            mod.build_plan(forged, 2)
            with self.assertRaisesRegex(mod.PlanError, "HEAD/index blob"):
                mod.assert_original_git_head_parity(root, forged)

            # Dirty worktree with unchanged original Git HEAD and index.
            dirty = root / state["blocked_sources"][0]["path"]
            dirty.write_text("(111 ())\n", encoding="utf-8")
            with self.assertRaisesRegex(mod.PlanError, "worktree drift"):
                mod.assert_original_git_head_parity(root, state)
            subprocess.run(["git", "checkout", "--", str(dirty.relative_to(root))],
                           cwd=root, check=True, capture_output=True)

            # Staging a source change still cannot forge the old source.
            dirty.write_text("(111 ())\n", encoding="utf-8")
            subprocess.run(["git", "add", str(dirty.relative_to(root))], cwd=root,
                           check=True)
            with self.assertRaisesRegex(mod.PlanError, "HEAD/index blob"):
                mod.assert_original_git_head_parity(root, state)

    def test_cli_write_once_is_read_only_input_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "candidates.json"
            output = root / "agent-shards.json"
            source.write_text(json.dumps(fixture()), encoding="utf-8")
            # CLI requires an exact Git HEAD source inventory. Build a
            # committed fixture checkout rather than weakening that default.
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"],
                           cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test Runner"],
                           cwd=root, check=True)
            state = fixture()
            for row in state["blocked_sources"] + state["mechanical_candidates"]:
                file = root / row["path"]
                file.parent.mkdir(parents=True, exist_ok=True)
                payload = b"(001 ())\n"
                file.write_bytes(payload)
                pin = mod.hashlib.sha1(b"blob " + str(len(payload)).encode() +
                                      b"\0" + payload).hexdigest()
                row["source_git_blob_sha"] = pin
                for group in state["blocker_cohorts"]:
                    for member in group["original_sources"]:
                        if member["path"] == row["path"]:
                            member["source_git_blob_sha"] = pin
            source.write_text(json.dumps(state), encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "test originals"], cwd=root,
                           check=True)
            pinned = source.read_bytes()
            self.assertEqual(mod.main(["--candidates", str(source),
                                       "--repo-root", str(root),
                                       "--out", str(output), "--max-files", "2"]), 0)
            self.assertTrue(output.is_file())
            self.assertEqual(source.read_bytes(), pinned)
            state = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["shards"], 3)
            self.assertEqual(mod.main(["--candidates", str(source), "--repo-root", str(root), "--out", str(output)]), 2)
            self.assertEqual(source.read_bytes(), pinned)
            self.assertEqual(mod.main(["--candidates", str(source), "--repo-root", str(root), "--out", str(source)]), 2)

    def test_zero_candidates_all_blocked_still_creates_work_queue(self):
        a = fixture()
        a["mechanical_candidates"] = []
        a["summary"]["scanned"] = 3
        a["summary"]["original_unpaired_sources_scanned"] = 3
        a["summary"]["mechanical_candidates"] = 0
        a["summary"]["unpaired_candidates_needing_original_oracle"] = 0
        r = mod.build_plan(a, 1)
        self.assertEqual(r["summary"]["blocked"], 3)
        self.assertEqual(r["summary"]["mechanical_pending_oracle"], 0)
        self.assertEqual(r["summary"]["shards"], 3)


if __name__ == "__main__":
    unittest.main()
