#!/usr/bin/env python3
"""Physical C T09 subprocess parity; does NOT adjudicate SENS semantics."""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("t09_popcount.c")
ROOT = Path(__file__).resolve().parents[2]
PARITY = ROOT / "parity_check.py"
spec = importlib.util.spec_from_file_location("t09_frozen_parity", PARITY)
assert spec is not None and spec.loader is not None
parity = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parity
spec.loader.exec_module(parity)
TASK = "T09-bit-operations"

class CPopcountParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cc = shutil.which("cc")
        if cls.cc is None:
            raise unittest.SkipTest("NO_C_COMPILER: C T09 parity not verified")
        cls.temp = tempfile.TemporaryDirectory(prefix="t09-c11-")
        cls.binary = Path(cls.temp.name) / "t09_popcount"
        proc = subprocess.run([cls.cc, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-o", str(cls.binary), str(SCRIPT)],
                              capture_output=True, text=True, timeout=30)
        if proc.returncode:
            raise AssertionError(f"C11 BUILD FAILED, stdout={proc.stdout}, stderr={proc.stderr}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def run_c(self, n: str | None, seed: str | None, task: str | None = TASK):
        env = dict(os.environ)
        for name in ("TASK_N", "TASK_SEED", "TASK_ID"):
            env.pop(name, None)
        for name, val in (("TASK_N", n), ("TASK_SEED", seed), ("TASK_ID", task)):
            if val is not None:
                env[name] = val
        return subprocess.run([str(self.binary)], capture_output=True, timeout=15, env=env)

    def test_verify_exact_output(self):
        frozen = parity.VERIFY_SIZE[TASK]
        got = self.run_c(str(frozen["n"]), str(frozen["seed"]))
        expected = (parity.ref_T09(**frozen) + "\n").encode("ascii")
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(got.stderr, b"")
        self.assertEqual(got.stdout, expected)

    def test_measure_exact_output(self):
        frozen = next(t["input"] for t in parity.load_manifest()["tasks"] if t["id"] == TASK)
        self.assertEqual(frozen, {"n": 1000000, "seed": 999})
        got = self.run_c(str(frozen["n"]), str(frozen["seed"]))
        expected = (parity.ref_T09(**frozen) + "\n").encode("ascii")
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(got.stderr, b"")
        self.assertEqual(got.stdout, expected)

    def test_missing_or_wrong_frozen_input_is_rejected(self):
        cases = [(None, "3", TASK), ("2000", None, TASK), ("2000", "3", None),
                 ("2000", "3", "T01-symbolic-recursion"),
                 ("2000", "999", TASK), ("1000000", "3", TASK),
                 ("2000", "03", TASK), ("+2000", "3", TASK),
                 ("2000 ", "3", TASK), ("18446744073709551616", "3", TASK),
                 ("0", "3", TASK)]
        for n, seed, task in cases:
            with self.subTest(n=n, seed=seed, task=task):
                proc = self.run_c(n, seed, task)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertIn(b"INVALID_TASK_INPUT", proc.stderr)

if __name__ == "__main__":
    unittest.main()
