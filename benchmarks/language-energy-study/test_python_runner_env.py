#!/usr/bin/env python3
"""Контролі Python baseline на однаковий VERIFY/MEASURE TASK_* вхід."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "corpus" / "python" / "run.py"


class PythonBaselineInputTests(unittest.TestCase):
    def run_case(self, tid="T01-symbolic-recursion", **values):
        env = {k: v for k, v in os.environ.items()
               if k != "TASK_ID" and not k.startswith("TASK_")}
        env["TASK_ID"] = tid
        for key, value in values.items():
            env["TASK_" + key.upper()] = str(value)
        return subprocess.run([sys.executable, str(RUNNER)], env=env,
                              text=True, capture_output=True, timeout=20)

    def test_t01_verify_n12(self):
        p = self.run_case(n=12)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "144"), p.stderr)

    def test_t01_measure_n24(self):
        p = self.run_case(n=24)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "46368"), p.stderr)

    def test_t01_measure_is_not_verify(self):
        a = self.run_case(n=12)
        b = self.run_case(n=24)
        self.assertNotEqual(a.stdout, b.stdout)

    def test_other_task_verified(self):
        p = self.run_case("T05-allocation-gc", n=200, k=4)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "800"), p.stderr)

    def test_other_task_measure(self):
        p = self.run_case("T05-allocation-gc", n=200000, k=16)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, "3200000"), p.stderr)

    def test_missing_number_fail_closed(self):
        p = self.run_case()
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("INVALID_TASK_INPUT", p.stderr)

    def test_unfrozen_n_fail_closed(self):
        p = self.run_case(n=23)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("neither frozen", p.stderr)

    def test_malformed_and_noncanonical_fail_closed(self):
        for bad in ("24.0", " 24", "+24", "-1", "024", "abc", "1e3"):
            with self.subTest(bad=bad):
                p = self.run_case(n=bad)
                self.assertEqual(p.returncode, 2)
                self.assertEqual(p.stdout, "")

    def test_unknown_task_fail_closed(self):
        p = self.run_case("TXX-unknown", n=24)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")

    def test_seed_is_not_ignored(self):
        p = self.run_case("T04-sorting", n=500, seed=8)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")


if __name__ == "__main__":
    unittest.main()
