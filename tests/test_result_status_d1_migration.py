"""Executable bounded oracle for Contract 11.8 D1/D3 result shape migration.

The mini-interpreter intentionally supports only ratified D3 forms used in the
five migrated definitions. It does not admit any wider domain or host truthiness.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "cond-modernize.py"
SPEC = importlib.util.spec_from_file_location("result_migration_sexpr", SCRIPTS)
assert SPEC and SPEC.loader
reader = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reader
SPEC.loader.exec_module(reader)

SOURCE = (ROOT / "lib" / "result-status.lisp").read_text(encoding="utf-8")
NAMES = (
    "result-tagged?",
    "result-status",
    "result-payload",
    "result-proper-list?",
    "result-not-head?",
)


def tree(node):
    if node.atom is not None:
        return node.atom
    return [tree(c) for c in node.children]


@dataclass(frozen=True)
class Pair:
    car: object
    cdr: object


def chain(*values, tail=None):
    for value in reversed(values):
        tail = Pair(value, tail)
    return tail


def quoted(ast):
    if isinstance(ast, str):
        return ast
    return chain(*(quoted(item) for item in ast))


class BoundedD3Oracle:
    def __init__(self, source):
        self.defs = {}
        for form in reader.parse(source):
            f = tree(form)
            if isinstance(f, list) and len(f) == 3 and f[0] == "00001001" and f[1] in NAMES:
                lam = f[2]
                assert lam[0] == "00001000" and len(lam) == 3
                self.defs[f[1]] = (lam[1], lam[2])
        assert set(self.defs) == set(NAMES)

    def apply(self, name, args):
        params, body = self.defs[name]
        assert len(params) == len(args), (name, params, args)
        return self.eval(body, dict(zip(params, args)))

    def eval(self, e, env):
        if isinstance(e, str):
            if e in env:
                return env[e]
            raise ValueError(f"unbound atom: {e}")
        if not e:
            return None
        op = e[0]
        if op == "00000001":  # D3 QUOTE
            assert len(e) == 2
            return quoted(e[1])
        if op == "00000010":  # D3 ATOM -> exact D1
            assert len(e) == 2
            return 0 if isinstance(self.eval(e[1], env), Pair) else 1
        if op == "00000011":  # D3 EQ -> exact D1; never compare pairs
            assert len(e) == 3
            left, right = (self.eval(x, env) for x in e[1:])
            if isinstance(left, Pair) or isinstance(right, Pair):
                raise TypeError("D3 EQ refuses pair arguments")
            return int(type(left) is type(right) and left == right)
        if op == "00000100":  # D3 CONS
            assert len(e) == 3
            return Pair(self.eval(e[1], env), self.eval(e[2], env))
        if op == "00000101":  # D3 CAR
            arg = self.eval(e[1], env)
            if not isinstance(arg, Pair):
                raise TypeError("CAR requires pair")
            return arg.car
        if op == "00000110":  # D3 CDR
            arg = self.eval(e[1], env)
            if not isinstance(arg, Pair):
                raise TypeError("CDR requires pair")
            return arg.cdr
        if op == "00000111":  # strict D3 COND
            for clause in e[1:]:
                if not isinstance(clause, list) or len(clause) != 2:
                    raise ValueError("retired three-field COND clause")
                test = self.eval(clause[0], env)
                if type(test) is not int or test not in (0, 1):
                    raise TypeError("COND requires exact D1 predicate")
                if test == 1:
                    return self.eval(clause[1], env)
            return None  # structural EMPTY, not D1 0
        if op in self.defs:
            return self.apply(op, [self.eval(x, env) for x in e[1:]])
        raise ValueError(f"nonadmitted form in bounded D3 oracle: {op}")


class ResultStatusMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = BoundedD3Oracle(SOURCE)

    def assertD1(self, value, expected):
        self.assertIs(type(value), int)
        self.assertEqual(value, expected)
        self.assertIsNotNone(value)

    def test_all_six_status_tags_and_non_tags(self):
        for tag in ("proved", "unknown", "partial", "blocked", "disputed", "invalid"):
            rec = chain(tag, "payload")
            self.assertD1(self.oracle.apply("result-tagged?", [rec]), 1)
            self.assertEqual(self.oracle.apply("result-status", [rec]), tag)
            self.assertEqual(self.oracle.apply("result-payload", [rec]), chain("payload"))
        for other in (None, "proved", "not-tagged", 0, chain("unexpected", "payload")):
            self.assertD1(self.oracle.apply("result-tagged?", [other]), 0)
            self.assertIsNone(self.oracle.apply("result-status", [other]))
            self.assertIsNone(self.oracle.apply("result-payload", [other]))

    def test_proper_list_distinguishes_structural_empty_from_d1_zero(self):
        for proper in (None, chain("a"), chain("a", "b", "c")):
            self.assertD1(self.oracle.apply("result-proper-list?", [proper]), 1)
        for improper in ("a", 0, 1, Pair("a", "tail"), Pair("a", Pair("b", "tail"))):
            self.assertD1(self.oracle.apply("result-proper-list?", [improper]), 0)

    def test_not_head_returns_exact_predicate_and_does_not_reinterpret_nil(self):
        for value in ("not?", "not"):
            self.assertD1(self.oracle.apply("result-not-head?", [value]), 1)
        for value in (None, "eq", "negative", 0):
            self.assertD1(self.oracle.apply("result-not-head?", [value]), 0)

    def test_all_migrated_cond_clauses_are_two_field_and_have_no_t(self):
        all_cond = 0
        for form in reader.parse(SOURCE):
            f = tree(form)
            if not isinstance(f, list) or len(f) < 3 or f[1] not in NAMES:
                continue
            def inspect(node):
                nonlocal all_cond
                if isinstance(node, str):
                    self.assertNotEqual(node.lower(), "t")
                    return
                if node and node[0] == "00000111":
                    all_cond += 1
                    for clause in node[1:]:
                        self.assertEqual(len(clause), 2)
                for child in node:
                    inspect(child)
            inspect(f)
        self.assertEqual(all_cond, 5)

    def test_retired_third_expected_field_is_rejected(self):
        changed = SOURCE.replace(
            "((00000010 result) (00000010",
            "((00000010 result) () (00000010",
            1,
        )
        with self.assertRaisesRegex(ValueError, "three-field"):
            BoundedD3Oracle(changed).apply("result-tagged?", [None])


if __name__ == "__main__":
    unittest.main()
