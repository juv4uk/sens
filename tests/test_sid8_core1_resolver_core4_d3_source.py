"""Pinned old-identity fixture and D3 two-field source cutover.

No physical .sens, no new branch; quoted historical SID data remain historical.
"""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-core1-compiler-sid-resolver.lisp"
RESOLVER = ROOT / "lib/core1-compiler-sid-resolver.lisp"
BOUNDARY = ROOT / "scripts/check-core4-predicate-answer-boundary.lisp"
OLD_RESOLVER_CHECKER_SHA = "1a6924534c1bc8b3f1176c0004f685b93c3599b7"
OLD_BOUNDARY_SHA = "197792988400fe2a0537a291fe1e3d978898416a"

def historical_source(blob):
    return subprocess.run(
        ["git", "cat-file", "blob", blob], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout

class Core1SourceSurfaceTests(unittest.TestCase):
    def test_reader_checker_matches_current_resolver_without_rewriting_historical_table(self):
        original = historical_source(OLD_RESOLVER_CHECKER_SHA)
        before = """(0011 c1r-expected-resolver-form
  (001
    (00001001 C1-COMPILER-SID-FOR-SURFACE
      (00001000 (NAME)
        (C1-PRIMITIVE-IDENTITY NAME)))))"""
        after = """(0011 c1r-expected-resolver-form
  (001
    (0011 C1-COMPILER-SID-FOR-SURFACE
      (0010 (NAME)
        (C1-PRIMITIVE-IDENTITY NAME)))))"""
        self.assertEqual(original.count(before), 1)
        actual = CHECKER.read_text()
        self.assertEqual(actual, original.replace(before, after))
        self.assertIn(after, actual)
        self.assertIn("(0011 C1-COMPILER-SID-FOR-SURFACE", RESOLVER.read_text())
        self.assertIn("(0010 (NAME)", RESOLVER.read_text())
        for legacy_datum in ("(ATOM 00000010)", "(EQ 00000011)", "(NOT 00100001)"):
            self.assertIn(legacy_datum, actual)

    def test_d3_boundary_has_no_extra_boolean_clause_and_explicit_d1_true(self):
        original = historical_source(OLD_BOUNDARY_SHA)
        before = """(110
  ((11110111 pab-observed pab-expected)
   (1)
   (001 (core4-predicate-answer-boundary-ok)))
  ((11110111 1 1) 1
   (1110 (001 core4-predicate-answer-boundary-mismatch)
         pab-expected
         pab-observed)))"""
        after = """(110
  ((11110111 pab-observed pab-expected)
   (001 (core4-predicate-answer-boundary-ok)))
  ((010 (001 ()))
   (1110 (001 core4-predicate-answer-boundary-mismatch)
         pab-expected
         pab-observed)))"""
        self.assertEqual(original.count(before), 1)
        current = BOUNDARY.read_text()
        self.assertEqual(current, original.replace(before, after))
        self.assertIn("((010 (001 ()))", current)
        self.assertNotIn("((11110111 1 1) 1", current)
        self.assertNotIn("(11110111 pab-observed pab-expected)\n   (1)", current)

if __name__ == "__main__":
    unittest.main()
