#!/usr/bin/env python3
"""Adversarial owner L1-L7 policy checks, independent of runtime oracle."""
import importlib.util
from pathlib import Path
import sys
import unittest

P = Path(__file__).with_name("normalize-legacy-l1-l7.py")
SPEC = importlib.util.spec_from_file_location("owner_l1_l7", P)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class OwnerDecision(unittest.TestCase):
    def run_case(self, source, path="lib/example.lisp", d8=None):
        return mod.analyze(source, path, d8 or {})

    def test_l2_explicit_true_clause(self):
        src = "(110 (t (001 ok)))"
        normalized, rows = self.run_case(src)
        self.assertEqual(normalized, "(110 (1 (001 ok)))")
        self.assertEqual(rows[0]["rule"], "L2")

    def test_l1_non_predicate_blocks_entire_source(self):
        src = "(110 (t yes) (other no))"
        normalized, rows = self.run_case(src)
        self.assertEqual(normalized, src)
        self.assertTrue(any(x["rule"] == "L1" and x["status"] == "BLOCK" for x in rows))

    def test_l1_legacy_truthiness(self):
        src = "(cond (t yes))"
        normalized, rows = self.run_case(src)
        self.assertEqual(normalized, src)
        self.assertTrue(any(x["rule"] == "L1" and x["status"] == "BLOCK" for x in rows))

    def test_quoted_and_string_are_unchanged(self):
        cases = ["'(110 (t yes))", "(001 (110 (t yes)))",
                 '"(110 (t yes))"', "#; (110 (t yes))"]
        for src in cases:
            with self.subTest(src=src):
                normalized, rows = self.run_case(src)
                self.assertEqual(normalized, src)
                self.assertFalse(rows)

    def test_l4_d8_from_registry_or_hold(self):
        normalized, rows = self.run_case("(equal? a b)", d8={"equal?": "11110111"})
        self.assertEqual(normalized, "(11110111 a b)")
        self.assertEqual(rows[0]["resident"], "D8:11110111")
        normalized, rows = self.run_case("(null a)")
        self.assertEqual(normalized, "(null a)")
        self.assertEqual(rows[0]["rule"], "L4")
        self.assertEqual(rows[0]["status"], "BLOCK")

    def test_l5_retirement_requires_archaeology(self):
        src = "(structural-kind a)"
        normalized, rows = self.run_case(src)
        self.assertEqual(normalized, src)
        self.assertEqual(rows[0]["rule"], "L5")

    def test_l6_fixture_requires_canonical_generator(self):
        src = "(110 (t x))"
        normalized, rows = self.run_case(src, "tests/fixtures/old.lisp")
        self.assertEqual(normalized, src)
        self.assertTrue(any(x["rule"] == "L6" and x["status"] == "BLOCK" for x in rows))

    def test_l7_bad_reader_input_is_untouched(self):
        for src in ["(", ")", '"unterminated']:
            with self.subTest(src=src):
                normalized, rows = self.run_case(src)
                self.assertEqual(normalized, src)
                self.assertEqual(rows[0]["rule"], "L7")

    def test_l3_original_w8_ambiguous(self):
        src = "(00100010 a b)"
        normalized, rows = self.run_case(src)
        self.assertEqual(normalized, src)
        self.assertTrue(any(x["rule"] == "L3" and x["status"] == "BLOCK" for x in rows))

    def test_literal_d1_clauses_keep_structure(self):
        src = "(110 (0 a) (1 b))"
        normalized, rows = self.run_case(src)
        self.assertEqual(normalized, src)
        self.assertFalse(any(x["status"] == "BLOCK" for x in rows))


if __name__ == "__main__":
    unittest.main()
