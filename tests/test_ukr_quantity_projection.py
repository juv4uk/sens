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


# Точний кінцевий виклик виконує SENS, а не цей структурний тест.
# Його не слід плутати з DEFINE чи з доказом семантики в Python.
EXECUTION_WITNESS = ("науковий-список-правильний?", ("як-є", ("а", "б")))


def definitions(forms: tuple) -> dict[str, tuple]:
    result = {}
    witnesses = []
    for index, form in enumerate(forms):
        if form == EXECUTION_WITNESS:
            witnesses.append(index)
            continue
        if not isinstance(form, tuple) or len(form) != 3 or form[0] != "визначити":
            raise AssertionError("чинні верхньорівневі форми мають бути українськими DEFINE або точним кінцевим SENS-свідком")
        name = form[1]
        if not isinstance(name, str):
            raise AssertionError("некоректне ім'я визначення")
        if name in result:
            raise AssertionError(f"дубльоване визначення: {name}")
        result[name] = form[2]
    if witnesses != [len(forms) - 1]:
        raise AssertionError("відсутній або переміщений кінцевий виклик-свідок SENS")
    return result

def verify(source: str) -> dict[str, tuple]:
    forms = parse_forms(source)
    scope = definitions(forms)
    for required in (
        "науковий-внутрішній-символ?",
        "науковий-список-правильний?",
        "науковий-список-довжина-дорівнює?",
        "створити-розмірність",
        "розмірність?",
        "одиниця-виміру?",
        "науковий-всі-розмірності-коректні?",
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
    if "(символ? " in source:
        raise AssertionError("недопущений D9 symbol? не має виконуваного механізму")
    symbol_law = "(тотожне? значення (текст-у-символ (значення-у-текст значення)))"
    if source.count(symbol_law) != 1:
        raise AssertionError("втрачено D1 закон символу через реальні D8 механізми")
    if source.count("(науковий-внутрішній-символ? ") != 3:
        raise AssertionError("три перевірки полів мають застосовувати чинний SENS закон")
    # D8 WRITE не серіалізує D1, тому обидва бітові значення
    # обов'язково відхиляються до точного текстового маршруту.
    for d1_guard in (
        "((тотожне? значення (атом? (як-є ()))) (хибне? (атом? (як-є ()))))",
        "((тотожне? значення (хибне? (атом? (як-є ()))))\n       (хибне? (атом? (як-є ()))))",
    ):
        if source.count(d1_guard) != 1:
            raise AssertionError("D1 предикат перед D8 WRITE не відхилено: " + d1_guard)
    if "(тотожне? залишок 0)" in source:
        raise AssertionError("D3 EQ не є числовою рівністю D24+")
    # D1-предикати не порівнюємо із D3 NIL через EQ.
    # Це перевірка форми; значення має обчислити живий SENS.
    for guard in (
        "(порожній? (величина? (третє значення)))",
        "(порожній? (науковий-константа-стан-чинний? (четверте значення)))",
        "(порожній? (науковий-константа-вид-чинний? (п'ятий значення)))",
        "(порожній? (наука-джерело? (науковий-сьомий значення)))",
        "(порожній? (науковий-константа? константа))",
    ):
        if source.count(guard) != 1:
            raise AssertionError("нечинна перевірка D3 NIL поля наукової константи: " + guard)
    if source.count("(сполучити схема-одиниці-виміру розмірності)") != 1:
        raise AssertionError("конструктор одиниці більше не зберігає обернену структуру")
    # Тільки структурний guard; семантичний доказ належить живому SENS.
    if source.count("(науковий-всі-розмірності-коректні? (решта значення))") != 1:
        raise AssertionError("одиниця виміру не перевіряє кожну розмірність")
    if source.count("(порожній? (розмірність? (перше розмірності)))") != 1:
        raise AssertionError("розмірності одиниці не проходять чинний Lisp-предикат")
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

    def test_symbol_guards_use_current_sens_mechanism_not_unbound_d9(self):
        verify(self.source)
        current = "(науковий-внутрішній-символ? (друге значення))"
        self.assertIn(current, self.source)
        for broken in (
            self.source.replace(current, "(символ? (друге значення))", 1),
            self.source.replace(
                "(тотожне? значення (текст-у-символ (значення-у-текст значення)))",
                "(атом? значення)", 1),
        ):
            with self.assertRaises(AssertionError):
                verify(broken)

    def test_predicate_bits_are_rejected_before_d8_writer(self):
        verify(self.source)
        for guarded in (
            "((тотожне? значення (атом? (як-є ()))) (хибне? (атом? (як-є ()))))",
            "((тотожне? значення (хибне? (атом? (як-є ()))))\n       (хибне? (атом? (як-є ()))))",
        ):
            broken = self.source.replace(guarded, "; видалений захист D1", 1)
            with self.assertRaisesRegex(AssertionError, "D1 предикат"):
                verify(broken)

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

    def test_nil_guard_does_not_apply_d1_not_to_structural_empty(self):
        # NOT вимагає D1, а недопущений валідатор повертає D3 NIL.
        current = "(порожній? (величина? (третє значення)))"
        legacy = "(хибне? (величина? (третє значення)))"
        self.assertEqual(self.source.count(current), 1)
        mutated = self.source.replace(current, legacy, 1)
        self.assertNotEqual(mutated, self.source)
        with self.assertRaisesRegex(AssertionError, "D3 NIL поля"):
            verify(mutated)

    def test_unit_constructor_shape_and_old_nested_list_mutation(self):
        current = "(сполучити схема-одиниці-виміру розмірності)"
        obsolete = "(список схема-одиниці-виміру розмірності)"
        self.assertEqual(self.source.count(current), 1)
        self.assertNotIn(obsolete, self.source)
        mutated = self.source.replace(current, obsolete, 1)
        with self.assertRaisesRegex(AssertionError, "конструктор одиниці"):
            verify(mutated)

    def test_unit_requires_real_dimension_predicate_not_just_proper_list(self):
        current = "(науковий-всі-розмірності-коректні? (решта значення))"
        obsolete = "(науковий-список-правильний? (решта значення))"
        self.assertEqual(self.source.count(current), 1)
        wrong = self.source.replace(current, obsolete, 1)
        with self.assertRaisesRegex(AssertionError, "кожну розмірність"):
            verify(wrong)

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
            "dimension-1", "unit-1", "quantity-1",
            "science-source-1", "scientific-constant-1",
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
        # D9 каталог утримує ратифіковане ім’я, але не надає викличності.
        # Виконувана бібліотека мусить користуватися локальним D1-законом.
        self.assertNotIn("(символ?", self.source)
        self.assertIn("(науковий-внутрішній-символ?", self.source)
        self.assertIn("(п'ятий", self.source)


if __name__ == "__main__":
    unittest.main()
