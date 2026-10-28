"""ENERGY-02: independent C11 T08 physical-work parity, NOT SENS semantics.

GCC/Clang compile O0 and O2, then compare exact output with the frozen
Python reference for VERIFY_SIZE and MEASURE_SIZE. Invalid TASK_* inputs must
fail before producing any result. Energy is not measured by this test.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "corpus" / "c" / "t08_persistent.c"


def reference(n):
    spec = importlib.util.spec_from_file_location("sens_t08_parity_check", HERE / "parity_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ref_T08(n)


class T08CParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="sens-t08-c-")
        cls.binaries = []
        cc = shutil.which("cc")
        if not cc:
            raise RuntimeError("C compiler absent: T08 parity must not be marked PASS")
        for opt in ("-O0", "-O2"):
            binary = Path(cls.tmp.name) / ("t08_" + opt[1:])
            subprocess.run([cc, "-std=c11", opt, "-Wall", "-Wextra", "-Werror",
                            str(SOURCE), "-o", str(binary)],
                           check=True, capture_output=True, text=True, timeout=25)
            cls.binaries.append(binary)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def execute(self, binary, *, task="T08-persistent-structures", n="500"):
        env = os.environ.copy()
        env.pop("TASK_ID", None)
        env.pop("TASK_N", None)
        if task is not None:
            env["TASK_ID"] = task
        if n is not None:
            env["TASK_N"] = n
        return subprocess.run([str(binary)], capture_output=True, text=True,
                              env=env, timeout=15)

    def test_frozen_verify_and_measure_parity(self):
        for binary in self.binaries:
            for n in (500, 20000):
                with self.subTest(binary=binary.name, n=n):
                    p = self.execute(binary, n=str(n))
                    self.assertEqual(p.returncode, 0, p.stderr)
                    self.assertEqual(p.stderr, "")
                    self.assertEqual(p.stdout, reference(n) + "\n")
                    self.assertEqual(len(p.stdout.splitlines()), 1)

    def test_invalid_inputs_fail_closed(self):
        invalid = [
            (None, "500"), ("T09-bit-operations", "500"),
            ("T08-persistent-structures", None),
            ("T08-persistent-structures", "0"),
            ("T08-persistent-structures", "499"),
            ("T08-persistent-structures", "20001"),
            ("T08-persistent-structures", "0500"),
            ("T08-persistent-structures", "-500"),
            ("T08-persistent-structures", "500x"),
            ("T08-persistent-structures", " 500"),
        ]
        for binary in self.binaries:
            for task, n in invalid:
                with self.subTest(binary=binary.name, task=task, n=n):
                    p = self.execute(binary, task=task, n=n)
                    self.assertEqual(p.returncode, 2)
                    self.assertEqual(p.stdout, "")
                    self.assertIn("T08_INVALID_INPUT", p.stderr)


if __name__ == "__main__":
    unittest.main()
