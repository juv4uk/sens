#!/usr/bin/env python3
"""Physical C T05 output parity; this does not adjudicate SENS semantics."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

CORPUS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CORPUS))
import parity_check  # noqa: E402

SOURCE = Path(__file__).with_name("t05_alloc.c")
TASK = "T05-allocation-gc"


class T05PhysicalOutputParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = shutil.which("cc")
        if cls.compiler is None:
            raise unittest.SkipTest("NO_C_COMPILER: T05 C parity not verified")
        cls.temp = tempfile.TemporaryDirectory(prefix="sens-t05-c-")
        cls.binary = Path(cls.temp.name) / "t05_alloc"
        result = subprocess.run(
            [cls.compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             "-pedantic", str(SOURCE), "-o", str(cls.binary)],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if result.returncode != 0:
            cls.temp.cleanup()
            raise AssertionError(
                f"C11 BUILD FAILED (exit={result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def execute(self, n=None, k=None, task=TASK):
        env = dict(os.environ)
        for key in ("TASK_ID", "TASK_N", "TASK_K"):
            env.pop(key, None)
        if task is not None:
            env["TASK_ID"] = task
        if n is not None:
            env["TASK_N"] = str(n)
        if k is not None:
            env["TASK_K"] = str(k)
        return subprocess.run(
            [str(self.binary)], env=env, text=True, capture_output=True,
            timeout=20, check=False,
        )

    def test_verify_size_exact_parity(self):
        args = parity_check.VERIFY_SIZE[TASK]
        result = self.execute(**args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, parity_check.ref_T05(**args) + "\n")
        self.assertEqual(result.stderr, "")

    def test_variable_shapes_match_frozen_reference(self):
        for n, k in ((1, 1), (3, 7), (200, 4)):
            with self.subTest(n=n, k=k):
                result = self.execute(n, k)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, parity_check.ref_T05(n, k) + "\n")

    def test_invalid_parameters_fail_closed(self):
        cases = (
            ("abc", "4", TASK), ("-1", "4", TASK), ("2", "0", TASK),
            ("2", "4.0", TASK), ("2", "4", "T06-io"),
            ("1000001", "4", TASK), ("500000", "4096", TASK),
        )
        for n, k, task in cases:
            with self.subTest(n=n, k=k, task=task):
                result = self.execute(n, k, task)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("T05_INVALID_INPUT", result.stderr)

    def test_missing_required_input_fails_closed(self):
        result = self.execute(n="2", k=None)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("T05_INVALID_INPUT", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
