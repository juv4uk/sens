#!/usr/bin/env python3
"""Pinned original Git history against contemporary W8 ambiguity; no translation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_w8_source_era.py"
spec = importlib.util.spec_from_file_location("w8_origin_proof", SCRIPT)
assert spec and spec.loader
proof = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proof
spec.loader.exec_module(proof)

OLD = "a" * 40
NEW = "b" * 40


def cohort(*sources):
    return {
        "exact_blocker_cohorts": [{
            "family": "w8-provenance", "coordinate": "00001001",
            "original_sources": [
                {"path": p, "source_git_blob_sha": sha} for p, sha in sources
            ],
        }],
    }


class W8ProvenanceTests(unittest.TestCase):
    def test_immutable_historical_snapshot_is_a_real_pre_d8_commit(self):
        tree = proof.tree_blobs(ROOT, proof.BASELINE)
        self.assertGreater(len(tree), 200)
        self.assertEqual(tree["lib/core1.lisp"], "a2f184373428bc516a0b03491dfabfb3255d07ef")
        self.assertIn("lib/core1.lisp", proof.current_tracked_blobs(ROOT))

    def test_equal_git_blob_means_only_chronological_evidence(self):
        src = cohort(("old.lisp", OLD), ("new.lisp", NEW), ("changed.lisp", NEW))
        historical = {"old.lisp": OLD, "changed.lisp": OLD}
        current = {"old.lisp": OLD, "new.lisp": NEW, "changed.lisp": NEW}
        result = proof.report(ROOT, src, historical, current)
        self.assertEqual(result["summary"]["w8_first_blocked_originals"], 3)
        self.assertEqual(result["summary"]["SAME_BLOB_BEFORE_D8_RATIFICATION"], 1)
        self.assertEqual(result["summary"]["NOT_PRESENT_IN_PRE_D8_SNAPSHOT"], 1)
        self.assertEqual(result["summary"]["CHANGED_SINCE_PRE_D8_SNAPSHOT"], 1)
        self.assertEqual(result["summary"]["current_semantic_admissions"], 0)
        self.assertEqual(result["summary"]["published_sens"], 0)
        self.assertEqual(result["by_w8_first_blocker"]["00001001"],
                         {"total": 3, "same_blob": 1})
        self.assertTrue(all(not r["permission_to_choose_legacy"] for r in result["sources"]))
        self.assertTrue(all(r["historical_legacy_semantics"] == "NOT_PROVEN" for r in result["sources"]))

    def test_distinct_w8_words_remain_distinct_provenance_queues(self):
        src = cohort(("first.lisp", OLD))
        src["exact_blocker_cohorts"].append({
            "family": "w8-provenance", "coordinate": "00001011",
            "original_sources": [{"path": "next.lisp", "source_git_blob_sha": NEW}],
        })
        out = proof.report(ROOT, src, {"first.lisp": OLD}, {
            "first.lisp": OLD, "next.lisp": NEW,
        })
        self.assertEqual([x["w8_first_blocker"] for x in out["sources"]],
                         ["00001001", "00001011"])
        self.assertEqual(out["by_w8_first_blocker"]["00001011"]["same_blob"], 0)

    def test_non_w8_cohorts_are_excluded_without_losing_w8(self):
        src = cohort(("old.lisp", OLD))
        src["exact_blocker_cohorts"].append({
            "family": "host-effect", "coordinate": "other",
            "original_sources": [{"path": "print.lisp", "source_git_blob_sha": NEW}],
        })
        r = proof.report(ROOT, src, {"old.lisp": OLD}, {"old.lisp": OLD})
        self.assertEqual([m["path"] for m in r["sources"]], ["old.lisp"])

    def test_missing_or_dirty_git_index_proof_is_rejected(self):
        src = cohort(("old.lisp", OLD))
        with self.assertRaisesRegex(proof.EvidenceError, "tracked stage-0"):
            proof.report(ROOT, src, {"old.lisp": OLD}, {"old.lisp": NEW})
        with self.assertRaisesRegex(proof.EvidenceError, "tracked stage-0 Git blob"):
            proof.report(ROOT, cohort(("old.lisp", "0"*39)),
                         {"old.lisp": OLD}, {"old.lisp": "0"*39})

    def test_duplicate_or_untrusted_source_path_blocks(self):
        bad = cohort(("old.lisp", OLD), ("old.lisp", OLD))
        with self.assertRaisesRegex(proof.EvidenceError, "duplicate"):
            proof.report(ROOT, bad, {}, {"old.lisp": OLD})
        for p in ("/tmp/a.lisp", "../escape.lisp", "fake.sens"):
            with self.subTest(p=p), self.assertRaisesRegex(proof.EvidenceError, "untrusted"):
                proof.report(ROOT, cohort((p, OLD)), {}, {p: OLD})

    def test_untrusted_unknown_binary_coordinate_blocks(self):
        src = cohort(("old.lisp", OLD))
        src["exact_blocker_cohorts"][0]["coordinate"] = "0000100X"
        with self.assertRaisesRegex(proof.EvidenceError, "exact binary"):
            proof.report(ROOT, src, {}, {"old.lisp": OLD})

    def test_no_source_era_authorized_on_empty_original_queue(self):
        r = proof.report(ROOT, {"exact_blocker_cohorts": []}, {}, {})
        self.assertEqual(r["sources"], [])
        self.assertEqual(r["summary"]["current_semantic_admissions"], 0)
        self.assertIn("No automatic legacy", r["interpretation"])

    def test_baseline_rejects_any_arbitrary_or_future_commit(self):
        with self.assertRaisesRegex(proof.EvidenceError, "full immutable"):
            proof.tree_blobs(ROOT, "main")
        current = proof.git(ROOT, "rev-parse", "HEAD")
        with self.assertRaisesRegex(proof.EvidenceError, "pre-D8 cutoff"):
            proof.tree_blobs(ROOT, current)


if __name__ == "__main__":
    unittest.main()
