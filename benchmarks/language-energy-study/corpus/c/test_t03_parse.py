#!/usr/bin/env python3
"""Physical corpus parity only; NOT a source of SENS semantic laws.

Run: python3 -m unittest -v test_t03_parse.py
A C compiler and OpenSSL libcrypto development headers are required.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name("t03_parse.c")
TASK = "T03-parsing-text"


def golden(lines: int) -> str:
    """Frozen T03 input/algorithm from parity_check.ref_T03, not new semantics."""
    rows = [f"k{(i * 7919) % 1000}=v{i}" for i in range(lines)]
    keys = sorted(row.split("=", 1)[0] for row in rows)
    return hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest()


class CParserParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix="sens-t03-c-")
        cls.binary = Path(cls.work.name) / "t03_parse"
        cc = os.environ.get("CC", "cc")
        subprocess.run(
            [cc, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
             str(SOURCE), "-lcrypto", "-o", str(cls.binary)],
            check=True, capture_output=True, text=True, timeout=30,
        )

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def execute(self, lines=None, task=TASK):
        env = dict(os.environ)
        env.pop("TASK_ID", None)
        env.pop("TASK_LINES", None)
        if task is not None:
            env["TASK_ID"] = task
        if lines is not None:
            env["TASK_LINES"] = str(lines)
        return subprocess.run([str(self.binary)], env=env, capture_output=True,
                              text=True, timeout=15)

    def test_verify_size_50(self):
        p = self.execute(50)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, golden(50) + "\n")
        self.assertEqual(p.stderr, "")

    def test_frozen_measure_size_5000(self):
        p = self.execute(5000)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, golden(5000) + "\n")

    def test_one_row(self):
        self.assertEqual(self.execute(1).stdout, golden(1) + "\n")

    def test_duplicate_keys_preserved(self):
        p = self.execute(1001)
        self.assertEqual(p.stdout, golden(1001) + "\n")
        deduplicated = sorted(set(f"k{(i * 7919) % 1000}" for i in range(1001)))
        wrongly_deduped = hashlib.sha256("\n".join(deduplicated).encode()).hexdigest()
        self.assertNotEqual(p.stdout.strip(), wrongly_deduped)

    def test_negative_wrong_generator_is_detected(self):
        p = self.execute(50)
        corrupted_keys = sorted(f"k{(i * 7920) % 1000}" for i in range(50))
        wrong = hashlib.sha256("\n".join(corrupted_keys).encode()).hexdigest()
        self.assertEqual(p.stdout.strip(), golden(50))
        self.assertNotEqual(p.stdout.strip(), wrong)

    def test_invalid_inputs_fail_closed(self):
        for lines, task in [(None, TASK), (50, None), (50, "T05-allocation-gc"),
                            ("", TASK), ("0", TASK), ("-1", TASK),
                            ("50oops", TASK), ("1.5", TASK),
                            ("1000001", TASK), ("18446744073709551616", TASK)]:
            with self.subTest(lines=lines, task=task):
                p = self.execute(lines, task)
                self.assertEqual(p.returncode, 2, p.stderr)
                self.assertEqual(p.stdout, "")
                self.assertIn("T03_INPUT_INVALID", p.stderr)


if __name__ == "__main__":
    unittest.main()
