#!/usr/bin/env python3
"""ENERGY-02 T04: independently test C byte-output parity, not SENS semantics.

Only small explicit workloads and the frozen manifest workload are run.
No host energy values or rankings are inferred.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from parity_check import VERIFY_SIZE, load_manifest, ref_T04  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "t04_sort.c"
JAVASCRIPT = HERE.parent / "javascript" / "t04_sort.mjs"
TASK = "T04-sorting"


class CSortingCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("cc")
        if compiler is None:
            raise unittest.SkipTest("C compiler absent (not a PASS)")
        cls.temp = tempfile.TemporaryDirectory(prefix="sens-t04-c-")
        cls.binary = Path(cls.temp.name) / "t04_sort"
        result = subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra",
             "-Werror", str(SOURCE), "-lcrypto", "-o", str(cls.binary)],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if result.returncode:
            cls.temp.cleanup()
            raise AssertionError("C compile failed: " + result.stderr)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def run_c(self, n, seed, *, task=TASK):
        env = os.environ.copy()
        env.update(TASK_ID=task, TASK_N=str(n), TASK_SEED=str(seed))
        return subprocess.run([str(self.binary)], env=env, capture_output=True,
                              text=True, check=False, timeout=25)

    def test_verify_size_exact_parity(self):
        inputs = VERIFY_SIZE[TASK]
        got = self.run_c(**inputs)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(got.stdout, ref_T04(**inputs) + "\n")
        self.assertEqual(got.stderr, "")

    def test_frozen_measure_size_exact_parity(self):
        task = next(task for task in load_manifest()["tasks"] if task["id"] == TASK)
        inputs = task["input"]
        got = self.run_c(**inputs)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(got.stdout, ref_T04(**inputs) + "\n")

    def test_unsigned_64bit_wrap_and_sort(self):
        inputs = {"n": 101, "seed": (1 << 64) - 1}
        got = self.run_c(**inputs)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(got.stdout, ref_T04(**inputs) + "\n")

    def test_repeatability(self):
        first = self.run_c(500, 7)
        second = self.run_c(500, 7)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)

    def test_javascript_small_parity(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node absent (C/Python parity still exercised)")
        inputs = VERIFY_SIZE[TASK]
        env = os.environ.copy()
        env.update(TASK_ID=TASK, TASK_N=str(inputs["n"]),
                   TASK_SEED=str(inputs["seed"]))
        js = subprocess.run([node, str(JAVASCRIPT)], env=env, capture_output=True,
                            text=True, timeout=25, check=False)
        self.assertEqual(js.returncode, 0, js.stderr)
        self.assertEqual(self.run_c(**inputs).stdout, js.stdout)

    def test_reject_bad_inputs_without_output(self):
        bad = [
            ("T99", "500", "7"), (TASK, "0", "7"),
            (TASK, "-1", "7"), (TASK, "1e2", "7"),
            (TASK, "1000001", "7"), (TASK, "500", "-3"),
            (TASK, "500", "18446744073709551616"),
            (TASK, "500", "7 "), (TASK, "500", ""),
        ]
        for task, n, seed in bad:
            with self.subTest(task=task, n=n, seed=seed):
                env = os.environ.copy()
                env.update(TASK_ID=task, TASK_N=n, TASK_SEED=seed)
                result = subprocess.run([str(self.binary)], env=env,
                                        capture_output=True, text=True,
                                        timeout=10, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("T04_INPUT_INVALID", result.stderr)

    def test_missing_variables_fail_closed(self):
        env = os.environ.copy()
        for key in ("TASK_ID", "TASK_N", "TASK_SEED"):
            env.pop(key, None)
        result = subprocess.run([str(self.binary)], env=env,
                                capture_output=True, text=True,
                                timeout=10, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
