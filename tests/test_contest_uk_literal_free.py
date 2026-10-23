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
    "benchmarks/contest-uk/добуток-сусідів-д6.lisp",
    "benchmarks/contest-uk/довжина-списку-одинарна.lisp",
    "benchmarks/contest-uk/квадрат-унарний.lisp",
    "benchmarks/contest-uk/куб-унарний.lisp",
    "benchmarks/contest-uk/кількість-атомів-однопараметрова.lisp",
    "benchmarks/contest-uk/лише-атоми-однопараметровий.lisp",
    "benchmarks/contest-uk/перевернути-д5.lisp",
    "benchmarks/contest-uk/розгорнути-один-компакт.lisp",
    "benchmarks/contest-uk/пентагональне-формула.lisp",
    "benchmarks/contest-uk/подвійний-факторіал-рекурсивний.lisp",
    "benchmarks/contest-uk/поліном-кубічний-горнер.lisp",
    "benchmarks/contest-uk/різниця-кубів-пряма.lisp",
    "benchmarks/contest-uk/семикутне-формула.lisp",
    "benchmarks/contest-uk/степінь-двійки-одинарний.lisp",
    "benchmarks/contest-uk/сума-до-n-одинарна.lisp",
    "benchmarks/contest-uk/сума-квадратів-без-одиниць.lisp",
    "benchmarks/contest-uk/сума-кубів-без-замикання.lisp",
    "benchmarks/contest-uk/сума-непарних-квадрат.lisp",
    "benchmarks/contest-uk/сума-непарних-квадратів-різниця-квадратів.lisp",
    "benchmarks/contest-uk/сума-парних-формула.lisp",
    "benchmarks/contest-uk/сума-трикутних-два-прирости.lisp",
    "benchmarks/contest-uk/сума-четвертих-степенів-без-лямбди.lisp",
    "benchmarks/contest-uk/трикутне-добуток.lisp",
    "benchmarks/contest-uk/факторіал-д6-стислий.lisp",
    "benchmarks/contest-uk/фібоначчі-компакт.lisp",
    "benchmarks/contest-uk/центроване-квадратне-д6.lisp",
    "benchmarks/contest-uk/центроване-трикутне-д6.lisp",
    "benchmarks/contest-uk/центроване-шестикутне-д6.lisp",
    "benchmarks/contest-uk/кількість-пар-формула.lisp",
    "benchmarks/contest-uk/кількість-трійок-формула.lisp",
    "benchmarks/contest-uk/максимум-дзеркальний.lisp",
    "benchmarks/contest-uk/модуль-д6.lisp",
    "benchmarks/contest-uk/мінімум-прямий.lisp",
    "benchmarks/contest-uk/нсд-евклід-компакт.lisp",
    "benchmarks/contest-uk/акерман-малий.lisp",
    "benchmarks/contest-uk/восьмикутне-добуток.lisp",
    "benchmarks/contest-uk/відстань-пряма.lisp",
    "benchmarks/contest-uk/збільшити-всі-компакт.lisp",
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
