#!/usr/bin/env python3
"""Physical corpus parity only; NOT a source of SENS semantic laws.

The frozen Python reference owns the expected T03 output. This test compiles
only the independent C implementation and checks the same declared input.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

RESEARCH_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RESEARCH_ROOT))
import parity_check  # noqa: E402

SOURCE = Path(__file__).with_name("t03_parse.c")
TASK = "T03-parsing-text"


def golden(lines: int) -> str:
    """Reuse the frozen corpus reference; do not create a second oracle."""
    return parity_check.ref_T03(lines)


class CParserParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which(os.environ.get("CC", "cc"))
        if compiler is None:
            raise unittest.SkipTest("NO_C_COMPILER: T03 C parity not verified")
        cls.work = tempfile.TemporaryDirectory(prefix="sens-t03-c-")
        cls.binary = Path(cls.work.name) / "t03_parse"
        result = subprocess.run(
            [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             str(SOURCE), "-lcrypto", "-o", str(cls.binary)],
            check=False, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            cls.work.cleanup()
            raise AssertionError(
                f"C11 BUILD FAILED (exit={result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "work"):
            cls.work.cleanup()

    def execute(self, lines=None, task=TASK):
        env = dict(os.environ)
        env.pop("TASK_ID", None)
        env.pop("TASK_LINES", None)
        if task is not None:
            env["TASK_ID"] = task
        if lines is not None:
            env["TASK_LINES"] = str(lines)
        return subprocess.run(
            [str(self.binary)], env=env, capture_output=True,
            text=True, timeout=15, check=False,
        )

    def test_verify_size_exact_parity(self):
        lines = parity_check.VERIFY_SIZE[TASK]["lines"]
        result = self.execute(lines)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, golden(lines) + "\n")
        self.assertEqual(result.stderr, "")

    def test_frozen_measure_size_exact_output(self):
        task = next(item for item in parity_check.load_manifest()["tasks"]
                    if item["id"] == TASK)
        lines = task["input"]["lines"]
        result = self.execute(lines)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, golden(lines) + "\n")
        self.assertEqual(result.stderr, "")

    def test_one_row(self):
        self.assertEqual(self.execute(1).stdout, golden(1) + "\n")

    def test_duplicate_keys_preserved(self):
        lines = 1001
        result = self.execute(lines)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, golden(lines) + "\n")
        deduplicated = sorted(set(f"k{(i * 7919) % 1000}" for i in range(lines)))
        wrong = parity_check.hashlib.sha256("\n".join(deduplicated).encode()).hexdigest()
        self.assertNotEqual(result.stdout.strip(), wrong)

    def test_negative_wrong_generator_is_detected(self):
        lines = parity_check.VERIFY_SIZE[TASK]["lines"]
        result = self.execute(lines)
        corrupted_keys = sorted(f"k{(i * 7920) % 1000}" for i in range(lines))
        wrong = parity_check.hashlib.sha256("\n".join(corrupted_keys).encode()).hexdigest()
        self.assertEqual(result.stdout.strip(), golden(lines))
        self.assertNotEqual(result.stdout.strip(), wrong)

    def test_invalid_inputs_fail_closed(self):
        cases = (
            (None, TASK), (50, None), (50, "T05-allocation-gc"),
            ("", TASK), ("0", TASK), ("-1", TASK), ("50oops", TASK),
            ("1.5", TASK), ("1000001", TASK), ("18446744073709551616", TASK),
        )
        for lines, task in cases:
            with self.subTest(lines=lines, task=task):
                result = self.execute(lines, task)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("T03_INPUT_INVALID", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
