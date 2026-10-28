#!/usr/bin/env python3
"""Bounded T05 external-result parity and negative I/O tests; NOT a SENS oracle.

Usage: python3 benchmarks/language-energy-study/corpus/c/test_t05_alloc.py /path/to/t05
Requires only Python stdlib; uses the existing T05 reference, never redefines it.
"""
import os
from pathlib import Path
import subprocess
import sys
import unittest

CORPUS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CORPUS))
import parity_check  # noqa: E402


class T05PhysicalOutputParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if len(sys.argv) != 2:
            raise RuntimeError("usage: test_t05_alloc.py /path/to/compiled/t05")
        cls.binary = str(Path(sys.argv[1]).resolve())

    def execute(self, n: str, k: str, task: str = "T05-allocation-gc"):
        env = dict(os.environ, TASK_ID=task, TASK_N=n, TASK_K=k)
        return subprocess.run([self.binary], env=env, text=True,
                              capture_output=True, timeout=20, check=False)

    def test_verify_size_exact_parity(self):
        doc = next(t for t in parity_check.load_manifest()["tasks"]
                   if t["id"] == "T05-allocation-gc")
        args = parity_check.VERIFY_SIZE[doc["id"]]
        p = self.execute(str(args["n"]), str(args["k"]))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(p.stdout.splitlines()), 1)
        self.assertEqual(parity_check.compare(doc, p.stdout.strip()), (True, "PARITY_OK"))

    def test_no_allocation_elision_shortcut_at_variable_shape(self):
        for n, k in [(1, 1), (3, 7), (200, 4)]:
            with self.subTest(n=n, k=k):
                p = self.execute(str(n), str(k))
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(p.stdout, parity_check.ref_T05(n, k) + "\n")

    def test_negative_parameters_fail_closed(self):
        for n, k, task in [("abc", "4", "T05-allocation-gc"),
                           ("-1", "4", "T05-allocation-gc"),
                           ("2", "0", "T05-allocation-gc"),
                           ("2", "4.0", "T05-allocation-gc"),
                           ("2", "4", "T06-io"),
                           ("1000001", "4", "T05-allocation-gc"),
                           ("500000", "4096", "T05-allocation-gc")]:
            with self.subTest(n=n, k=k, task=task):
                p = self.execute(n, k, task)
                self.assertNotEqual(p.returncode, 0)
                self.assertEqual(p.stdout, "")
                self.assertIn("T05_INVALID_INPUT", p.stderr)

    def test_missing_required_env_fails_closed(self):
        env = dict(os.environ)
        env.pop("TASK_K", None)
        env["TASK_ID"] = "T05-allocation-gc"
        env["TASK_N"] = "2"
        p = subprocess.run([self.binary], env=env, text=True,
                           capture_output=True, timeout=20, check=False)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_t05_alloc.py /path/to/compiled/t05")
    unittest.main(argv=[sys.argv[0]], verbosity=2)
