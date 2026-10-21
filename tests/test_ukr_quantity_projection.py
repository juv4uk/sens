#!/usr/bin/env python3
"""Чинна українська AST-проєкція quantity.lisp без історичних Git SHA/SID8.

Це *структурний* тест. Значення обчислює тільки SENS у
crates/sens/tests/quantity_d1_direct_cutover.rs та quantity_length_d24_current.rs.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/quantity.lisp"
TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')


def tokens(source: str) -> list[str]:
    return [s for s in TOKEN.findall(source) if not s.startswith(";")]


def parse_forms(source: str) -> tuple:
    items = tokens(source)
    offset = 0

    def expression():
        nonlocal offset
        if offset >= len(items):
            raise AssertionError("незакрита форма")
        token = items[offset]
        offset += 1
        if token == ")":
            raise AssertionError("зайва дужка")
        if token != "(":
            return token
        result = []
        while offset < len(items) and items[offset] != ")":
            result.append(expression())
        if offset >= len(items):
            raise AssertionError("незакрита дужка")
        offset += 1
        return tuple(result)

    forms = []
    while offset < len(items):
        forms.append(expression())
    return tuple(forms)


def definitions(forms: tuple) -> dict[str, tuple]:
    result = {}
    for form in forms:
        if not isinstance(form, tuple) or len(form) != 3 or form[0] != "визначити":
            raise AssertionError("чинні верхньорівневі форми мають бути українськими DEFINE")
        name = form[1]
        if not isinstance(name, str):
            raise AssertionError("некоректне ім'я визначення")
        if name in result:
            raise AssertionError(f"дубльоване визначення: {name}")
        result[name] = form[2]
    return result


def verify(source: str) -> dict[str, tuple]:
    forms = parse_forms(source)
    scope = definitions(forms)
    for required in (
        "науковий-список-правильний?",
        "науковий-список-довжина-дорівнює?",
        "створити-розмірність",
        "розмірність?",
        "одиниця-виміру?",
        "величина?",
        "наука-джерело?",
        "науковий-константа-стан-чинний?",
        "науковий-константа-вид-чинний?",
        "науковий-константа?",
        "науковий-константа-клаузи",
    ):
        if required not in scope:
            raise AssertionError("відсутній чинний закон: " + required)
    if len(scope) < 30:
        raise AssertionError("втрачено більшість функцій наукової бібліотеки")
    if any(re.fullmatch(r"[01]{3,10}", name) for name in scope):
        raise AssertionError("сирі доменні DEFINE не є українською проєкцією")
    lexical = tokens(source)
    if "так" in lexical or "ні" in lexical:
        raise AssertionError("незв'язані так/ні замість виконуваного D1")
    if any(token.startswith(("#d1:", "#d3:", "#d24:", "#sid8:")) for token in lexical):
        raise AssertionError("застарілий текстовий тег домену")
    if "(тотожне? залишок 0)" in source:
        raise AssertionError("D3 EQ не є числовою рівністю D24+")
    length = scope["науковий-список-довжина-дорівнює?"]
    if not all(
        phrase in source for phrase in (
            "(менше? залишок 0)",
            "(більше? залишок 0)",
            "(менше? залишок 1)",
            "(хибне? (порожній? елементи))",
            "(хибне? (науковий-список-довжина-дорівнює? значення 3))",
            "(хибне? (науковий-список-довжина-дорівнює? значення 7))",
        )
    ):
        raise AssertionError("зміна чинного D24+/D1 Lisp-закону")
    if not isinstance(length, tuple) or length[0] != "функція":
        raise AssertionError("виконувана D4 функція довжини відсутня")
    return scope


class CurrentQuantityUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_current_ukrainian_library_has_unique_live_definitions(self):
        scope = verify(self.source)
        self.assertEqual(len(scope), len(set(scope)))
        self.assertIn("науковий-константа-клаузи", scope)

    def test_d24_count_is_not_d3_eq_and_returns_predicate_d1(self):
        self.assertIn("(хибне? (порожній? елементи))", self.source)
        self.assertIn("(хибне? (атом? (як-є ())))", self.source)
        verify(self.source)
        mutant = self.source.replace(
            "(менше? залишок 0)", "(тотожне? залишок 0)", 1,
        )
        self.assertNotEqual(mutant, self.source)
        with self.assertRaisesRegex(AssertionError, "D3 EQ"):
            verify(mutant)

    def test_unbound_truth_mutation_rejected(self):
        modified = self.source.replace("(атом? (як-є ()))", "так", 1)
        self.assertNotEqual(modified, self.source)
        with self.assertRaisesRegex(AssertionError, "D1"):
            verify(modified)

    def test_duplicate_ukrainian_definition_rejected(self):
        mutant = self.source + "\n(визначити науковий-список-правильний? (як-є ()))\n"
        with self.assertRaisesRegex(AssertionError, "дубльоване"):
            verify(mutant)

    def test_comment_whitespace_does_not_change_ast(self):
        amended = (
            "; Декорація не змінює синтаксис.\n"
            + self.source.replace("(визначити ", "(визначити    ", 1)
            + "\n; Підсумковий коментар.\n"
        )
        self.assertEqual(parse_forms(self.source), parse_forms(amended))

    def test_unbalanced_program_rejected(self):
        with self.assertRaisesRegex(AssertionError, "незакрита"):
            parse_forms(self.source[:-2] + "(")

    def test_schema_names_are_quoted_data_not_english_call_heads(self):
        for schema in (
            "dimension/1", "unit/1", "quantity/1",
            "science-source/1", "scientific-constant/1",
        ):
            self.assertIn("(як-є " + schema + ")", self.source)
        verify(self.source)

    def test_current_d9_selector_spellings_match_ratified_domain(self):
        d9 = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        core = (ROOT / "lib/core4.lisp").read_text(encoding="utf-8")
        for bits, name in (("110101100", "символ?"), ("110110101", "п'ятий")):
            self.assertRegex(
                d9,
                re.compile(
                    r"(?m)^\s*\(" + bits +
                    r"\s+\(ук\s+[^\s()]+\)\s+\(укр\s+" +
                    re.escape(name) + r"\)"
                ),
            )
            self.assertIn(name, core)
        self.assertIn("(символ?", self.source)
        self.assertIn("(п'ятий", self.source)


if __name__ == "__main__":
    unittest.main()
