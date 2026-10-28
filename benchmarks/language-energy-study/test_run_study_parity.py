#!/usr/bin/env python3
"""Bounded regression controls for #6287 measured-output parity.

Only physical workload equivalence is checked; SENS language laws remain
exclusively under native SENS witnesses. No physical energy is inferred.
Run: python3 -m unittest -v benchmarks/language-energy-study/test_run_study_parity.py
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_study as study  # noqa: E402


TASK = {"id": "T01-symbolic-recursion", "check": "exact"}


class MeasuredParity(unittest.TestCase):
    def setUp(self):
        study.SIZES["mode"] = "verify"

    def tearDown(self):
        study.SIZES["mode"] = "verify"

    def pairs(self, returns, processes=1, per_process=1):
        with patch.object(study, "run_once", side_effect=returns) as simulated:
            result = study.build_pairs(TASK, ["javascript"], processes, per_process, 5227)
        self.assertEqual(simulated.call_count, 2 * processes * per_process)
        return result

    def test_verified_144_passes(self):
        result = self.pairs([(101, 20, "144"), (202, 22, "144")])
        self.assertTrue(result["parity"]["passed"])
        self.assertEqual(result["parity"]["ok_pairs"], 1)
        self.assertEqual(len(result["pairs"]), 1)
        self.assertTrue(result["pairs"][0]["parity_checked"])
        self.assertEqual(result["rejected"], [])

    def test_wrong_candidate_is_rejected_not_measured(self):
        result = self.pairs([(101, 20, "144"), (202, 22, "145")])
        self.assertFalse(result["parity"]["passed"])
        self.assertEqual(len(result["pairs"]), 0)
        self.assertEqual(result["parity"]["failed_attempts"], 1)
        self.assertIn("candidate=PARITY_FAILED", result["rejected"][0]["reason"])

    def test_wrong_baseline_is_rejected(self):
        result = self.pairs([(101, 20, "145"), (202, 22, "144")])
        self.assertFalse(result["parity"]["passed"])
        self.assertEqual(len(result["pairs"]), 0)
        self.assertIn("baseline=PARITY_FAILED", result["rejected"][0]["reason"])

    def test_failed_process_is_rejected(self):
        result = self.pairs([(None, None, "EXIT_1"), (202, 22, "144")])
        self.assertFalse(result["parity"]["passed"])
        self.assertEqual(result["pairs"], [])
        self.assertIn("run_fail", result["rejected"][0]["reason"])

    def test_mixed_good_and_bad_attempt_is_not_global_pass(self):
        result = self.pairs([
            (101, 20, "144"), (202, 22, "144"),
            (103, 20, "144"), (204, 22, "145"),
        ], per_process=2)
        self.assertFalse(result["parity"]["passed"])
        self.assertEqual(result["parity"]["ok_pairs"], 1)
        self.assertEqual(result["parity"]["failed_attempts"], 1)
        self.assertEqual(len(result["rejected"]), 1)

    def test_zero_attempts_cannot_pass(self):
        result = self.pairs([], processes=0)
        self.assertFalse(result["parity"]["passed"])
        self.assertEqual(result["pairs"], [])
        self.assertEqual(result["parity"]["checked_attempts"], 0)

    def test_measure_mode_compares_against_46368_not_144(self):
        study.SIZES["mode"] = "measure"
        verified = self.pairs([(101, 20, "46368"), (202, 22, "46368")])
        self.assertTrue(verified["parity"]["passed"])
        wrong = self.pairs([(101, 20, "144"), (202, 22, "144")])
        self.assertFalse(wrong["parity"]["passed"])
        self.assertEqual(wrong["pairs"], [])

    @unittest.skipUnless(hasattr(os, "wait4"), "Linux-only per-process RSS collector")
    def test_real_process_output_and_exit(self):
        command = f"{sys.executable} -c 'print(144)'"
        ns, rss, output = study.run_once(command, os.environ.copy(), timeout_s=2)
        self.assertIsInstance(ns, float)
        self.assertGreater(ns, 0)
        self.assertGreaterEqual(rss, 0)
        self.assertEqual(output, "144")
        bad = f"{sys.executable} -c 'import sys;sys.exit(7)'"
        ns, rss, error = study.run_once(bad, os.environ.copy(), timeout_s=2)
        self.assertIsNone(ns)
        self.assertIn("EXIT_", error)

    @unittest.skipUnless(hasattr(os, "wait4"), "Linux-only per-process RSS collector")
    def test_real_timeout_fails_closed(self):
        command = f"{sys.executable} -c 'import time;time.sleep(0.3)'"
        ns, rss, error = study.run_once(command, os.environ.copy(), timeout_s=0.03)
        self.assertIsNone(ns)
        self.assertIn("TIMEOUT_", error)

    def test_main_exits_nonzero_with_rejected_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.json"
            failed = {
                "schema": "sens-paired-physical/v1",
                "parity": {"passed": False},
                "rejected": [{"reason": "candidate=PARITY_FAILED"}],
                "pairs": [],
            }
            argv = ["run_study.py", "--tasks", TASK["id"], "--languages",
                    "javascript", "--processes", "1", "--per-process", "1",
                    "--out", str(out)]
            with patch.object(sys, "argv", argv), \
                 patch.object(study.shutil, "which", return_value="/usr/bin/node"), \
                 patch.object(study, "build_pairs", return_value=failed):
                rc = study.main()
            self.assertEqual(rc, 1)
            self.assertTrue(out.exists())
            self.assertIn('"passed": false', out.read_text(encoding="utf-8"))
            self.assertIn("ENERGY_NOT_MEASURED", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
