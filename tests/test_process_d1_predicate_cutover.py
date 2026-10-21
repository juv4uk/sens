#!/usr/bin/env python3
"""Структурний аудит прямих українських Д3-порівнянь у процесних функціях.

Перевіряє синтаксис, драбину доменів та захист від старих заперечень.
Семантику SENS тут не моделюємо мовою Python.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/process.lisp"
EXPECTED = {
    "процес-результат-текст": 1,
    "процес-публічний-вихід-код": 1,
    "процес-розгорнути-публічний-результат": 1,
}


def parse(source):
    tokens = [m.group(0) for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', source)
        if not m.group(0).startswith(";")]
    stack = [[]]
    for token in tokens:
        if token == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            if len(stack) == 1:
                raise ValueError("зайва закривальна дужка")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise ValueError("незакритий список")
    return stack[0]


def inspect(source):
    found = {}
    for form in parse(source):
        if not isinstance(form, list) or len(form) < 3 or form[0] != "визначити":
            continue
        count = 0

        def walk(node):
            nonlocal count
            if not isinstance(node, list):
                return
            if node and node[0] == "хибне?":
                raise ValueError("застаріле заперечення у прямій Д3-умові")
            if node and node[0] == "тотожне?":
                if len(node) != 3:
                    raise ValueError("Д3-тотожність мусить мати два аргументи")
                count += 1
            if node and node[0] == "за-умовою":
                for branch in node[1:]:
                    if not isinstance(branch, list) or len(branch) != 2:
                        raise ValueError("Д3-умова мусить містити двопольові гілки")
            for child in node:
                walk(child)

        walk(form)
        if count:
            found[form[1]] = count
    if found != EXPECTED:
        raise ValueError(f"три чинні Д3-порівняння (включно з D4 helper) порушено: {found}")
    return found


class ProcessD1Cutover(unittest.TestCase):
    def test_three_direct_domain_conditions(self):
        self.assertEqual(sum(inspect(SOURCE.read_text(encoding="utf-8")).values()), 3)

    def test_exact_domain_owners(self):
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        for bits, name in (("0", "NIL"), ("1", "T")):
            self.assertRegex(d1, rf"(?m)^\s*\({bits}\s+.*\(LISP {name}\)")
        self.assertRegex(d3, r"(?m)^\s*\(101\s+.*\(LISP EQ\)")
        self.assertRegex(d3, r"(?m)^\s*\(110\s+.*\(LISP COND\)")

    def test_process_result_contract_remains_data(self):
        source = SOURCE.read_text(encoding="utf-8")
        for datum in (
            "(як-є process-result)", "(як-є decoded-process)",
            "(як-є stdout-invalid-utf8)", "(як-є stderr-invalid-utf8)",
            "(як-є invalid-process-result)",
            "(отримати-сирий-код-виходу-процесу сирий-результат)",
            "(отримати-сирі-байти-помилок-процесу сирий-результат)",
            "((тотожне? код (як-є ())) -1)",
        ):
            with self.subTest(datum=datum):
                self.assertIn(datum, source)
        self.assertNotIn("(хибне? (тотожне?", source)

    def test_stale_inverse_and_wrong_identity_are_rejected(self):
        original = SOURCE.read_text(encoding="utf-8")
        for variant in (
            original.replace("(тотожне? код (як-є ()))",
                             "(хибне? (тотожне? код (як-є ())))", 1),
            original.replace("(тотожне? код (як-є ()))",
                             "(однакові? код (як-є ()))", 1),
        ):
            self.assertNotEqual(variant, original)
            with self.assertRaises(ValueError):
                inspect(variant)


if __name__ == "__main__":
    unittest.main()
