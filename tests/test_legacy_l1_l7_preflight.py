#!/usr/bin/env python3
"""Read-only and fail-closed witnesses for owner-ratified migration L1–L7."""
from __future__ import annotations

import runpy
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = runpy.run_path(str(ROOT / "scripts/legacy-l1-l7-preflight.py"),
                           run_name="legacy_l1_l7_tests")
analyze = PREFLIGHT["analyze"]


class L1L7Preflight(unittest.TestCase):
    def test_l2_explicit_d1_positive_staging_only(self):
        src = "(110 ((010 x) good) (t fallback))"
        r = analyze(src)
        self.assertEqual(r["status"], "STAGE_ONLY")
        self.assertIn("(1 fallback)", r["normalized"])
        self.assertEqual([x["law"] for x in r["findings"]], ["L2"])
        self.assertEqual(r["oracle_status"], "UNVERIFIED")

    def test_l1_partial_eq_needs_independent_proof(self):
        r = analyze("(110 ((101 x y) yes) (t fallback))")
        self.assertEqual(r["status"], "BLOCK")
        self.assertIsNone(r["normalized"])
        self.assertIn("L1", [x["law"] for x in r["findings"]])

    def test_l1_arbitrary_truthiness_is_not_d1(self):
        r = analyze("(110 ((mystery x) yes) (0 no))")
        self.assertEqual(r["status"], "BLOCK")
        self.assertEqual(r["findings"][0]["law"], "L1")

    def test_l2_legacy_cond_held(self):
        r = analyze("(COND (t answer))")
        self.assertEqual(r["status"], "BLOCK")
        self.assertEqual(r["findings"][0]["law"], "L2")

    def test_quote_data_never_edited(self):
        s = "(001 (110 (t literal)))"
        r = analyze(s)
        self.assertEqual(r["findings"], [])
        self.assertEqual(r["normalized"], s)

    def test_shorthand_quote_data_never_edited(self):
        s = "'(110 (t literal))"
        r = analyze(s)
        self.assertEqual(r["findings"], [])
        self.assertEqual(r["normalized"], s)

    def test_l4_requires_resident_proof(self):
        r = analyze("(equal? x y)")
        self.assertEqual(r["status"], "BLOCK")
        self.assertEqual(r["findings"][0]["law"], "L4")

    def test_l5_retired_is_not_reanimated(self):
        r = analyze("(structural-kind x)")
        self.assertEqual(r["status"], "BLOCK")
        self.assertEqual(r["findings"][0]["law"], "L5")

    def test_l7_unparseable_is_owner_review(self):
        r = analyze("(110 (t broken)")
        self.assertEqual(r["status"], "BLOCK")
        self.assertEqual(r["findings"][0]["law"], "L7")
        self.assertIsNone(r["normalized"])

    def test_no_guess_from_t_inside_unrelated_call(self):
        s = "(list t)"
        r = analyze(s)
        self.assertEqual(r["normalized"], s)
        self.assertEqual(r["findings"], [])

    def test_comment_only_is_not_executed(self):
        s = "; (110 (t ignored))\n(110 (1 accepted))"
        r = analyze(s)
        self.assertEqual(r["status"], "STAGE_ONLY")
        self.assertEqual(r["findings"], [])
        self.assertIn("(110 (1 accepted))", r["normalized"])


if __name__ == "__main__":
    unittest.main()
