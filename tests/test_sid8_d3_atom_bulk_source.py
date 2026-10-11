"""Pinned in-place D3 ATOM normalization over five original Lisp sources.

This is a source-level cutover witness. Runtime behavioral parity is a separate
release gate. Historical donor blobs and arbitrary 8-bit values are unchanged.
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "benchmarks/lists.lisp": (
        "3a9bb2118f188a932073667f2b6329d46760f675",
        [("      ((010 values) () 0)\n"
          "      ((010 values) (1) 0)\n"
          "      (t ",
          "      ((010 values) 0)\n"
          "      ((010 (001 ())) ")],
    ),
    "benchmarks/recursion.lisp": (
        "b575417e8782c933f4821997858b88f4ecff91b2",
        [("      ((010 values) () (001 done))\n"
          "      ((010 values) (1) (001 done))\n"
          "      (t ",
          "      ((010 values) (001 done))\n"
          "      ((010 (001 ())) ")],
    ),
    "scripts/gen-functions.lisp": (
        "a5d3638af1d3f3615a4c3a53b9d9dded0f882584",
        [("      ((010 lst) () (001 ()))\n"
          "      ((010 lst) (1) (001 ()))\n"
          "      (t ",
          "      ((010 lst) (001 ()))\n"
          "      ((010 (001 ())) ")],
    ),
    "scripts/build-constitution.lisp": (
        "48dbfbe91d67212026b8fed6799a9f3ac233eaa4",
        [("      ((010 remaining) () (001 ()))\n"
          "      ((010 remaining) (1) (001 ()))\n"
          "      (t ",
          "      ((010 remaining) (001 ()))\n"
          "      ((010 (001 ())) ")],
    ),
    "scripts/fixtures-for-tier.lisp": (
        "472a07a625bd81af3f4b4bb99e6f0ef39a1e53a7",
        [
          ("    ((010 *argv*) () (missing-tier-argument))\n"
           "    ((010 *argv*) (1) (missing-tier-argument))\n"
           "    (t ",
           "    ((010 *argv*) (missing-tier-argument))\n"
           "    ((010 (001 ())) "),
          ("      ((010 remaining) () (001 ()))\n"
           "      ((010 remaining) (1) (001 ()))\n"
           "      (t ",
           "      ((010 remaining) (001 ()))\n"
           "      ((010 (001 ())) "),
          ("              (t (001 ())))",
           "              ((010 (001 ())) (001 ())))"),
        ],
    ),
}

def pinned_blob(sha):
    return subprocess.run(
        ["git", "cat-file", "blob", sha], cwd=ROOT,
        check=True, text=True, capture_output=True,
    ).stdout

class SourceLevelD3AtomCutover(unittest.TestCase):
    def test_exactly_seven_source_specific_cutovers(self):
        self.assertEqual(sum(len(changes) for _, changes in CASES.values()), 7)
        for path, (old_sha, changes) in CASES.items():
            with self.subTest(file=path):
                old = pinned_blob(old_sha)
                new = (ROOT / path).read_text(encoding="utf-8")
                expected = old
                for before, after in changes:
                    self.assertEqual(expected.count(before), 1,
                                     f"{path}: expected one immutable source template")
                    expected = expected.replace(before, after)
                self.assertEqual(new, expected,
                                 f"{path}: unrelated source changes or omitted rewrite")
                self.assertIn("(010 (001 ()))", new)
                # No touched ATOM call can still be a three-field legacy
                # branch. Do not reject historical text inside comments.
                self.assertNotRegex(new, re.compile(
                    r"\(\(010 (?:values|lst|remaining|\*argv\*)\) \(\) "))

    def test_historical_data_and_benchmark_payloads_unchanged(self):
        original = pinned_blob(CASES["benchmarks/lists.lisp"][0])
        current = (ROOT / "benchmarks/lists.lisp").read_text()
        witness = "(radio antenna signal battery display encoder speaker microphone cable clock)"
        self.assertIn(witness, original)
        self.assertIn(witness, current)
        original = pinned_blob(CASES["benchmarks/recursion.lisp"][0])
        current = (ROOT / "benchmarks/recursion.lisp").read_text()
        self.assertIn("(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)", original)
        self.assertIn("(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)", current)

    def test_negative_control_catches_legacy_three_field_guard(self):
        path = ROOT / "benchmarks/lists.lisp"
        current = path.read_text()
        self.assertIn("((010 values) 0)", current)
        corrupted = current.replace("((010 values) 0)", "((010 values) () 0)")
        self.assertRegex(corrupted, re.compile(r"\(\(010 values\) \(\) 0\)"))
        self.assertNotEqual(corrupted, current)

if __name__ == "__main__":
    unittest.main()
