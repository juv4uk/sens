"""Tests for fail-closed historical branch triage. No repository writes."""
from __future__ import annotations
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_branch_sweep_triage import build


def row(status: str, branch: str, *, ahead: int = 1, recent: bool = False, research: bool = False):
    return {"branch": branch, "head": "a"*40, "status": status,
            "ahead": ahead, "behind": 2, "recent_72h": recent, "research": research,
            "examples": []}


def source(*rows):
    return {"schema": "historical-merge-census/v1", "base_sha": "f"*40,
            "branches_count": len(rows), "branches": list(rows)}


class SweepTriageTests(unittest.TestCase):
    def test_mergeable_without_oracle_is_hold(self):
        r = build(source(row("MERGEABLE_NEEDS_CI", "research/old-truth", research=True)), {})
        self.assertEqual(r["rows"][0]["verdict"], "HOLD")
        self.assertTrue(r["rows"][0]["semantic_risk"])
        self.assertFalse(r["ready_for_final_review"])

    def test_ancestor_is_merged_in(self):
        r = build(source(row("ALREADY_INCLUDED", "old/merged", ahead=0, recent=True)), {})
        self.assertEqual(r["rows"][0]["verdict"], "MERGED-IN")

    def test_conflict_is_not_admitted(self):
        r = build(source(row("CONFLICT_REBASE", "research/broken", research=True)), {})
        self.assertEqual(r["rows"][0]["verdict"], "CONFLICT")
        self.assertFalse(r["ready_for_final_review"])

    def test_old_mergeable_is_selected(self):
        r = build(source(row("MERGEABLE_NEEDS_CI", "old/clean")), {})
        self.assertTrue(r["rows"][0]["candidate"])
        self.assertEqual(r["rows"][0]["verdict"], "HOLD")

    def test_alive_requires_proof_and_exact_head(self):
        item = row("MERGEABLE_NEEDS_CI", "research/new", research=True)
        proof = {"verdict":"ALIVE", "head_sha":"a"*40,
                 "reason":"Independent proof preserves all current canonical D1-D9 semantics",
                 "evidence_url":"https://github.com/juv4uk/sens/issues/5131",
                 "semantic_contract_reviewed":True, "oracle_reviewed":True,
                 "current_head_ci_green":True,
                 "ci_url":"https://github.com/juv4uk/sens/actions/runs/999"}
        r = build(source(item), {"research/new":proof})
        self.assertEqual(r["rows"][0]["verdict"], "ALIVE")
        self.assertTrue(r["ready_for_final_review"])
        self.assertFalse(r["main_merge_authorized"])
        proof["head_sha"]="b"*40
        with self.assertRaises(ValueError):
            build(source(item), {"research/new":proof})

    def test_duplicate_ref_is_fatal(self):
        item = row("ALREADY_INCLUDED","dup",ahead=0)
        with self.assertRaises(ValueError): build(source(item,item),{})

    def test_extra_override_is_fatal(self):
        with self.assertRaises(ValueError):
            build(source(row("ALREADY_INCLUDED","ok",ahead=0)),{"missing":{}})

    def test_bad_census_count_is_fatal(self):
        d = source(row("ALREADY_INCLUDED","ok",ahead=0))
        d["branches_count"] += 1
        with self.assertRaises(ValueError): build(d,{})


if __name__ == "__main__":
    unittest.main()
