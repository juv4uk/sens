#!/usr/bin/env python3
"""Read-only AST gate for the bounded Guard migration to D3:110 / exact D1."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "guard_cond_modernize_parser", ROOT / "scripts/cond-modernize.py"
)
assert SPEC is not None and SPEC.loader is not None
parser = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = parser
SPEC.loader.exec_module(parser)

MIGRATED = frozenset((
    "guard-decision?",
    "guard-evidence-status?",
    "make-guard-finding",
    "guard-sync-window",
    "guard-reference-field",
))


def walk(form):
    if form.opaque:
        return
    yield form
    # Lisp quote means its content is data, not executable code.
    if parser.head(form) in {"00000001", "001", "quote", "QUOTE"}:
        return
    for child in form.children:
        yield from walk(child)


class GuardExactD1Ast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / "lib/guard.lisp").read_text(encoding="utf-8")
        roots = parser.parse(source)
        cls.defs = {
            item.children[1].atom: item
            for item in roots
            if not item.opaque and parser.head(item) == "00001011"
            and len(item.children) >= 3 and item.children[1].atom is not None
        }

    def test_migrated_conditionals_are_two_field_exact_d3_only(self):
        count = 0
        for name in sorted(MIGRATED):
            with self.subTest(function=name):
                self.assertIn(name, self.defs)
                calls = list(walk(self.defs[name]))
                heads = [parser.head(node) for node in calls]
                self.assertNotIn("00000111", heads, "retired eight-bit COND head")
                self.assertNotIn("00100001", heads, "unproved legacy NOT")
                self.assertNotIn("t", heads, "legacy truthy condition")
                clauses = [node for node in calls if parser.head(node) == "110"]
                self.assertGreaterEqual(len(clauses), 1)
                for cond in clauses:
                    for clause in cond.children[1:]:
                        self.assertIsNone(clause.atom)
                        self.assertEqual(
                            len(clause.children), 2,
                            f"{name}: D3 COND clause must be (D1-test expression)",
                        )
                count += len(clauses)
        self.assertEqual(count, 6, "two classifier + two finding + sync + reference")

    def test_guard_exact_eq_requires_two_operands(self):
        for name in sorted(MIGRATED):
            for node in walk(self.defs[name]):
                if parser.head(node) == "00000011":
                    self.assertEqual(
                        len(node.children), 3,
                        f"{name}: D3 EQ needs exactly two atom operands",
                    )

    def test_structural_comparison_is_held_not_silently_downgraded_to_eq(self):
        # EQUAL? accepts structured observations. D3 EQ alone is atom-only.
        # Preserve this pending migration rather than changing comparison law.
        untouched = self.defs["guard-compare"]
        calls = list(walk(untouched))
        self.assertIn("00100010", [parser.head(node) for node in calls])
        self.assertIn("00000111", [parser.head(node) for node in calls])


if __name__ == "__main__":
    unittest.main()
