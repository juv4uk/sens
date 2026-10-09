#!/usr/bin/env python3
"""L1-L7 decision gate: AST-only normalization, never guessed semantics."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("three_pass_l1l7", ROOT / "scripts/migrate-three-pass.py")
assert SPEC and SPEC.loader
migrate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migrate
SPEC.loader.exec_module(migrate)

# Synthetic mapping of EXISTING ratified coordinates: never serves as an
# admission map for the repository. Production imports actual foundation rows.
KNOWN = {
    "cond": ("110", "D3"),
    "atom": ("010", "D3"),
    "eq": ("101", "D3"),
    "not?": ("0100", "D4"),
    "null?": ("0101", "D4"),
    "quote": ("001", "D3"),
    "lambda": ("0010", "D4"),
}


class CanonicalL1L7Tests(unittest.TestCase):
    def resolver(self):
        return migrate.Resolver({}, KNOWN, {}, source_era="legacy", strict_decisions=True)

    def convert(self, source):
        return migrate.migrate_file(source, self.resolver(), {})

    def normalize(self, source, resolver=None):
        parsed = migrate.Parser(migrate.tokenize(migrate.strip_comments(source))).parse_program()
        return migrate.normalize_l1_l7(parsed, resolver or self.resolver())

    def test_l2_literal_t_becomes_exact_d1_one_only_in_cond(self):
        self.assertEqual(self.convert("(cond (t 000))\n"),
                         "10 110 00 10 1 00 000 01 01\n")
        self.assertEqual(self.convert("(110 (1 000))\n"),
                         "10 110 00 10 1 00 000 01 01\n")

    def test_l1_known_exact_d1_producers_are_admitted(self):
        code = self.convert("(cond ((atom 000) 000) ((eq 000 000) 000))")
        self.assertIn("10 010 00 000 01", code)
        self.assertIn("10 101 00 000 00 000 01", code)

    def test_l1_unproved_truthiness_is_never_coerced(self):
        for test in ("23", "()", "nil", "maybe", "(unregistered 000)", "(quote 1)"):
            with self.subTest(test=test):
                with self.assertRaisesRegex(migrate.MigrationError, "L1 BLOCK"):
                    self.convert(f"(cond ({test} 000))")

    def test_l1_requires_two_fields_and_proper_list(self):
        for source in ("(cond ((atom 000) 1 000))", "(cond (1))",
                       "(cond (1 000 000))", "(cond (1 . 000))"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(migrate.MigrationError, "L1 BLOCK"):
                    self.convert(source)

    def test_l3_unknown_call_requires_d10_proposal_not_passthrough(self):
        with self.assertRaisesRegex(migrate.MigrationError, r"L3 BLOCK \+ D10-PROPOSAL"):
            self.convert("(unknown-op 000)")
        with self.assertRaisesRegex(migrate.MigrationError, "L3 BLOCK"):
            self.convert("(000 000)")  # D3 structural empty is not callable

    def test_l4_helpers_without_verifiable_d8_block(self):
        for helper in ("equal?", "null"):
            with self.subTest(helper=helper):
                with self.assertRaisesRegex(migrate.MigrationError, "L4 BLOCK"):
                    self.convert(f"({helper} 000)")

    def test_l5_retired_executable_forms_block(self):
        for source in ("(structural-kind 000)", "(identity-relation 000)"):
            with self.assertRaisesRegex(migrate.MigrationError, "L5 BLOCK"):
                self.convert(source)

    def test_quote_is_data_not_subject_to_l5_rewrite(self):
        self.normalize("'(identity-relation (t 000))")
        self.normalize("(quote (identity-relation 000))")

    def test_l2_bound_t_is_not_rewritten_without_proof(self):
        resolver = self.resolver()
        resolver.global_binding_words["t"] = ["10", "0000001", "01"]
        with self.assertRaisesRegex(migrate.MigrationError, "L2 BLOCK"):
            self.normalize("(cond (t 000))", resolver)

    def test_l7_parser_error_never_emits(self):
        for source in ("(cond (t 000)", "(cond (t 000)))"):
            with self.subTest(source=source):
                with self.assertRaises(migrate.MigrationError):
                    self.convert(source)

    def test_plain_legacy_path_is_not_misrepresented_as_strict(self):
        legacy = migrate.Resolver({}, KNOWN, {}, source_era="legacy")
        output = migrate.migrate_file("(unknown-op 000)", legacy, {})
        self.assertIn("unknown-op", output)
        self.assertFalse(legacy.strict_decisions)


if __name__ == "__main__":
    unittest.main()
