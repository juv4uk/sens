"""Contract 11.8 static regression for the migrated language-owned Guard module.

This gate checks syntax and exact D1 witness shapes, not full runtime semantics.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts/cond-modernize.py"
SPEC = importlib.util.spec_from_file_location("guard_d1_cond_parser", SCANNER)
assert SPEC and SPEC.loader
parser = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = parser
SPEC.loader.exec_module(parser)

SOURCE = (ROOT / "lib/guard.lisp").read_text(encoding="utf-8")


def sexpr(form):
    if form.atom is not None:
        return form.atom
    return tuple(sexpr(part) for part in form.children)


def walk(form):
    if form.opaque or parser.head(form) in parser.QUOTE_HEADS:
        return
    yield form
    for part in form.children:
        yield from walk(part)


def check_guard_cond(source):
    roots = parser.parse(source)
    conditionals = []
    for form in roots:
        for item in walk(form):
            if item.atom is not None and item.atom.lower() == "t":
                raise ValueError("historical T is not a D1 PredicateBit")
            if parser.head(item) in ("00000111", "110"):
                if len(item.children) < 2:
                    raise ValueError("COND needs clauses")
                for clause in item.children[1:]:
                    if clause.atom is not None or len(clause.children) != 2:
                        raise ValueError("retired three-field or malformed COND clause")
                conditionals.append(item)
    return roots, conditionals


class GuardD1MigrationTests(unittest.TestCase):
    YES = ("00000010", ("00000001", ()))
    NO = ("00000010", ("00000100", ("00000001", ()), ("00000001", ())))

    def test_all_guard_cond_clauses_are_exact_pairs(self):
        roots, conditionals = check_guard_cond(SOURCE)
        self.assertEqual(len(roots), 8)
        self.assertEqual(len(conditionals), 7)
        self.assertEqual(sum(len(c.children) - 1 for c in conditionals), 23)

    def test_decision_and_evidence_status_return_only_d1_yes_no(self):
        roots, _ = check_guard_cond(SOURCE)
        for name in ("guard-decision?", "guard-evidence-status?"):
            function = next(form for form in roots if sexpr(form.children[1]) == name)
            clauses = next(item for item in walk(function) if parser.head(item) == "00000111")
            self.assertEqual(len(clauses.children), 6)
            self.assertEqual([sexpr(c.children[1]) for c in clauses.children[1:5]], [self.YES] * 4)
            self.assertEqual(sexpr(clauses.children[5].children[0]), self.YES)
            self.assertEqual(sexpr(clauses.children[5].children[1]), self.NO)

    def test_reference_field_atom_case_never_uses_three_fields(self):
        roots, _ = check_guard_cond(SOURCE)
        function = next(form for form in roots if sexpr(form.children[1]) == "guard-reference-field")
        cond = next(item for item in walk(function) if parser.head(item) == "00000111")
        self.assertEqual(len(cond.children), 3)  # head + two exact-pair clauses
        self.assertEqual(sexpr(cond.children[1].children[0]), ("00000010", "entry"))
        self.assertEqual(sexpr(cond.children[1].children[1]), ("00000001", ()))
        self.assertEqual(sexpr(cond.children[2].children[0]), self.YES)

    def test_legacy_predicate_or_three_field_regression_is_rejected(self):
        self.assertIn("((00000010 entry) (00000001 ()))", SOURCE)
        changed = SOURCE.replace(
            "((00000010 entry) (00000001 ()))",
            "((00000010 entry) () (00000001 ()))",
            1,
        )
        with self.assertRaisesRegex(ValueError, "three-field"):
            check_guard_cond(changed)
        changed = SOURCE.replace(
            "((00000010 entry) (00000001 ()))",
            "(t (00000001 ()))",
            1,
        )
        with self.assertRaisesRegex(ValueError, "historical T"):
            check_guard_cond(changed)


if __name__ == "__main__":
    unittest.main()
