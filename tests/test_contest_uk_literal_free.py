"""Лексичний свідок безлітеральної української проєкції конкурсних програм.

Семантику і результати обчислень перевіряє SENS; цей тест перевіряє
джерельний закон і не виконує програм засобами Python.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "contest_literal_guard", ROOT / "scripts/check_no_encoded_source_literals.py"
)
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)

PROGRAMS = (
    "benchmarks/contest-uk/четвертий-степінь-квадрат-квадрата.lisp",
    "benchmarks/contest-uk/шестикутне-один-добуток.lisp",
    "benchmarks/contest-uk/різниця-квадратів-добуток.lisp",
)


class ContestUkrLiteralFreeTests(unittest.TestCase):
    def test_contest_programs_use_no_numeric_source_tokens(self):
        for path in PROGRAMS:
            with self.subTest(program=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(GUARD.find_forbidden_literals(source, path=path), [])

    def test_literal_mutant_is_rejected(self):
        path = PROGRAMS[0]
        source = (ROOT / path).read_text(encoding="utf-8")
        exact_seven = "(довжина (як-є (а б в г ґ д е)))"
        self.assertEqual(source.count(exact_seven), 1)
        mutant = source.replace(exact_seven, "7", 1)
        self.assertNotEqual(GUARD.find_forbidden_literals(mutant, path=path), [])


if __name__ == "__main__":
    unittest.main()
