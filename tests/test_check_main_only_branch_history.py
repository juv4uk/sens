#!/usr/bin/env python3
"""Positive and negative policy witnesses for the historical branch census."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_main_only_branch_history.py"
SPEC = importlib.util.spec_from_file_location("_main_only_branch_history", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Не вдалося завантажити аудитор гілок")
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class BranchHistoryPolicyTests(unittest.TestCase):
    def test_new_short_lived_branch_is_a_triage_notice_not_a_gate_failure(self):
        report = {
            "branches_created": ["fix/atomic-change"],
            "results": [],
        }
        self.assertEqual(audit.exit_status(report, classify_requested=False), 0)

    def test_new_branch_does_not_hide_historical_content_review(self):
        report = {
            "branches_created": ["fix/atomic-change"],
            "results": [{"status": "NEEDS_CONTENT_REVIEW"}],
        }
        # A content difference remains visible for human review; it is not a
        # missing evidence object and is not silently labeled as a merge.
        self.assertEqual(audit.exit_status(report, classify_requested=True), 0)

    def test_missing_historical_source_object_stays_blocked(self):
        report = {
            "branches_created": ["fix/atomic-change"],
            "results": [{"status": "MISSING_SOURCE_OBJECT"}],
        }
        self.assertEqual(audit.exit_status(report, classify_requested=True), 2)

    def test_git_comparison_error_stays_blocked(self):
        report = {
            "branches_created": [],
            "results": [{"status": "DIFF_ERROR"}],
        }
        self.assertEqual(audit.exit_status(report, classify_requested=True), 2)

    def test_new_branch_without_classification_is_not_mistaken_for_evidence_loss(self):
        report = {
            "branches_created": ["fix/atomic-change"],
            "results": [],
        }
        self.assertEqual(audit.exit_status(report, classify_requested=False), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
