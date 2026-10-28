"""ENERGY-02 T07: check an independent C physical workload against the frozen corpus.

This tests output parity only; it is not a SENS semantic or energy oracle.
Run: python3 -m unittest -v benchmarks/language-energy-study/corpus/c/test_t07_matrices.py
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent.parent
sys.path.insert(0, str(STUDY))
import parity_check  # noqa: E402  (existing frozen ENERGY-02 oracle)


@unittest.skipUnless(shutil.which("cc"), "C compiler unavailable")
class T07IndependentCParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="sens-t07-c-")
        cls.binary = Path(cls.temp.name) / "t07"
        subprocess.run(
            ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
             str(HERE / "t07_matrices.c"), "-o", str(cls.binary)],
            check=True, capture_output=True, text=True, timeout=30,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def invoke(self, value: str | None, task: str | None = "T07-matrices") -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env.pop("TASK_ID", None)
        env.pop("TASK_N", None)
        if task is not None:
            env["TASK_ID"] = task
        if value is not None:
            env["TASK_N"] = value
        return subprocess.run([str(self.binary)], env=env, capture_output=True,
                              text=True, timeout=10)

    def test_python_reference_verify_and_measure(self) -> None:
        for n in (1, 2, 6, 120):
            with self.subTest(n=n):
                p = self.invoke(str(n))
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(len(p.stdout.splitlines()), 1)
                expected = parity_check.ref_T07(n)
                self.assertLessEqual(abs(float(p.stdout) - float(expected)), 1e-9)

    def test_existing_external_parity_gate_verify_size(self) -> None:
        task = next(t for t in parity_check.load_manifest()["tasks"]
                    if t["id"] == "T07-matrices")
        ok, verdict = parity_check.run_external(task, str(self.binary))
        self.assertTrue(ok, verdict)
        self.assertEqual(verdict, "PARITY_OK")

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_javascript_reference_verify_and_measure(self) -> None:
        js = STUDY / "corpus" / "javascript" / "t07_matrices.mjs"
        for n in (6, 120):
            with self.subTest(n=n):
                env = dict(os.environ, TASK_ID="T07-matrices", TASK_N=str(n))
                actual = self.invoke(str(n))
                external = subprocess.run(["node", str(js)], env=env,
                                          capture_output=True, text=True, timeout=15)
                self.assertEqual(external.returncode, 0, external.stderr)
                self.assertEqual(actual.returncode, 0, actual.stderr)
                self.assertLessEqual(abs(float(actual.stdout) - float(external.stdout)), 1e-9)

    def test_reject_missing_invalid_and_overlarge_dimensions(self) -> None:
        cases = (None, "", "0", "-1", "+6", " 6", "6 ", "\t6", "6.0",
                 "6x", "257", "184467440737095516160", "١٢")
        for value in cases:
            with self.subTest(value=value):
                proc = self.invoke(value)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")
                self.assertIn("T07_INVALID_INPUT", proc.stderr)

    def test_reject_missing_or_wrong_task_id(self) -> None:
        for task in (None, "", "T05-allocation-gc", " T07-matrices", "T07-matrices "):
            with self.subTest(task=task):
                proc = self.invoke("6", task)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
