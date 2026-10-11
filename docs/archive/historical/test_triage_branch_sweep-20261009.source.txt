#!/usr/bin/env python3
"""Regression tests: sweep census is not semantic authority or merge admission."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "triage_branch_sweep", ROOT / "scripts/triage_branch_sweep.py")
triage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triage)

MAIN = "a" * 40
HEAD = "b" * 40


def census(status, ahead=0, unique=0):
    return {
        "schema": "historical-merge-census/v1",
        "generated_utc": "2026-10-09T15:38:46+00:00",
        "base_sha": MAIN, "branches_count": 1,
        "branches": [{"branch": "research/old", "head": HEAD,
                      "status": status, "ahead": ahead, "behind": 2,
                      "unique_content_paths": unique, "recent_72h": True,
                      "research": True}]
    }


class SweepTriageTests(unittest.TestCase):
    def test_ancestor_is_not_merged_twice(self):
        row = triage.make_catalog(census("ALREADY_INCLUDED"))["branches"][0]
        self.assertEqual(row["verdict"], "MERGED-IN")
        self.assertTrue(row["reviewed"])

    def test_matching_blobs_are_not_merged_twice(self):
        row = triage.make_catalog(census("CONTENT_EQUIVALENT", 3))["branches"][0]
        self.assertEqual(row["verdict"], "MERGED-IN")

    def test_clean_git_merge_is_not_admitted(self):
        report = triage.make_catalog(census("MERGEABLE_NEEDS_CI", 2, 2))
        self.assertEqual(report["branches"][0]["verdict"], "CONFLICT")
        self.assertEqual(report["manual_review_pending"], 1)
        self.assertFalse(report["admission_authorized"])

    def test_retired_is_not_inferred_from_branch_name(self):
        row = triage.make_catalog(census("CONFLICT_REBASE", 3, 2))["branches"][0]
        self.assertNotEqual(row["verdict"], "OBSOLETE")

    def test_stale_manual_verdict_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "stale decision"):
            triage.make_catalog(census("MERGEABLE_NEEDS_CI", 2, 2),
                {"research/old": {"head": HEAD, "main_sha": "c"*40,
                                  "verdict": "ALIVE", "evidence_url": "x",
                                  "reviewer": "r", "ci": "SUCCESS", "oracle_url": "x"}})

    def test_alive_without_oracle_rejected(self):
        with self.assertRaisesRegex(ValueError, "ALIVE without"):
            triage.make_catalog(census("MERGEABLE_NEEDS_CI", 2, 2),
                {"research/old": {"head": HEAD, "main_sha": MAIN,
                                  "verdict": "ALIVE", "evidence_url": "x",
                                  "reviewer": "r", "ci": "SUCCESS"}})

    def test_missing_row_fails(self):
        payload = census("ALREADY_INCLUDED")
        payload["branches_count"] = 2
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            triage.make_catalog(payload)

    def test_duplicate_branch_fails(self):
        payload = census("ALREADY_INCLUDED")
        payload["branches"].append(dict(payload["branches"][0]))
        payload["branches_count"] = 2
        with self.assertRaisesRegex(ValueError, "duplicate branch"):
            triage.make_catalog(payload)


if __name__ == "__main__":
    unittest.main()
