"""Точковий доказ міграції 11 макросів knowledge: W8 → D4×2.

Перевіряє без зміни семантики: AST-тіла, порядок параметрів, одноразове
визначення кожного макросу та негативні мутації. Source-level test;
Rust/T5 runtime parity перевіряється окремими обов'язковими воротами.
"""
from copy import deepcopy
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/knowledge.lisp"
# Незалежні fingerprints З ІСТОРИЧНИХ тіл до rewrite (Git blob
# a2c1d3a51a87ab9aa364dec8002dd5e50e1b408d): коментарі й
# форматування ігноруються, семантичне дерево залишається незмінним.
EXPECTED = [
    ("defmodule", ["name","rules"], "9399fa8ca0c8dbbe"),
    ("retract-knowledge", ["module-name","clause"], "9d0b1a36618b9fd9"),
    ("load-knowledge", ["module-name"], "17e8e6d33209644b"),
    ("tell-knowledge", ["module-name","rules"], "93ccbcfc509b0c00"),
    ("advise", ["module-name","clause"], "41e8d6f91e46db29"),
    ("advise-all", ["module-name","clauses"], "e03343a2ab959f1d"),
    ("import-knowledge-package", ["package"], "0820142d6f8d6c36"),
    ("import-knowledge-file", ["path"], "841d31f117d38323"),
    ("receive-knowledge-package", ["connection"], "a1893890d26ec081"),
    ("accept-knowledge-exchange", ["connection"], "a9ed129b79f319d3"),
    ("record-usage!", ["proof"], "b019e1e4eacfba0d"),
]
EXPECTED_BY_NAME = {name: (params, hash_) for name, params, hash_ in EXPECTED}
TOKENS = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
MASK = (1 << 64) - 1


def parse(source):
    tokens = [m.group() for m in TOKENS.finditer(source)
              if not m.group().startswith(";")]
    pos = 0

    def read():
        nonlocal pos
        if pos >= len(tokens):
            raise AssertionError("незавершене S-вираження")
        token = tokens[pos]
        pos += 1
        if token != "(":
            if token == ")":
                raise AssertionError("зайва закривна дужка")
            return token
        result = []
        while pos < len(tokens) and tokens[pos] != ")":
            result.append(read())
        if pos == len(tokens):
            raise AssertionError("незакрита дужка")
        pos += 1
        return result

    expressions = []
    while pos < len(tokens):
        expressions.append(read())
    return expressions


def render(node):
    if isinstance(node, list):
        return "(" + " ".join(map(render, node)) + ")"
    return node


def fnv64(ast):
    h = 0xCBF29CE484222325
    for char in render(ast):
        h = ((h ^ ord(char)) * 0x100000001B3) & MASK
    return f"{h:016x}"


def verify_macro_cutover(expressions):
    # Визначення старою W8 головою заборонене, навіть коли за payload
    # D8 існує окрема незалежна координата.
    for form in expressions:
        if isinstance(form, list) and form and form[0] == "00001010":
            raise AssertionError("застаріла W8 DEFMACRO head")

    found = {}
    for form in expressions:
        if not (isinstance(form, list) and len(form) >= 2
                and form[1] in EXPECTED_BY_NAME):
            continue
        name = form[1]
        if name in found:
            raise AssertionError("подвійне визначення макросу " + name)
        if len(form) != 3 or form[0] != "0011":
            raise AssertionError("потрібен D4:0011 DEFINE")
        constructor = form[2]
        if not (isinstance(constructor, list)
                and len(constructor) == 2
                and constructor[0] == "make-macro"):
            raise AssertionError("втрата явного host-конструктора Closure→Macro")
        lam = constructor[1]
        if not (isinstance(lam, list) and len(lam) == 3 and lam[0] == "0010"):
            raise AssertionError("потрібен D4:0010 LAMBDA з одним тілом")
        params, fingerprint = EXPECTED_BY_NAME[name]
        if lam[1] != params:
            raise AssertionError("порядок сирих макроаргументів змінено")
        if fnv64(lam[2]) != fingerprint:
            raise AssertionError("переписано тіло макросу " + name)
        found[name] = form

    if set(found) != set(EXPECTED_BY_NAME):
        raise AssertionError("макрос зник або був перейменований")
    return found


class KnowledgeMacroDomainCutover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.expressions = parse(cls.source)

    def test_all_11_macro_definitions_are_exact_compositions(self):
        self.assertEqual(len(verify_macro_cutover(self.expressions)), 11)

    def test_independent_old_body_ast_fingerprints(self):
        found = verify_macro_cutover(self.expressions)
        self.assertEqual(
            {name: fnv64(form[2][1][2]) for name, form in found.items()},
            {name: hash_ for name, _, hash_ in EXPECTED},
        )

    def test_exact_width_opcode_accounting(self):
        found = verify_macro_cutover(self.expressions)
        self.assertEqual(sum(len(form[0]) + len(form[2][1][0])
                             for form in found.values()), 88)
        self.assertEqual(11 * len("00001010"), 88)
        self.assertEqual(len("0011"), 4)  # D4 DEFINE
        self.assertEqual(len("0010"), 4)  # D4 LAMBDA
        self.assertEqual(len("00011"), 5)  # D5 MACRO ≠ W8 defmacro

    def test_reject_eight_bit_reintroduction(self):
        mutated = deepcopy(self.expressions)
        found = verify_macro_cutover(mutated)
        found["load-knowledge"][0] = "00001010"
        with self.assertRaisesRegex(AssertionError, "застаріла W8"):
            verify_macro_cutover(mutated)

    def test_reject_body_mutation(self):
        mutated = deepcopy(self.expressions)
        found = verify_macro_cutover(mutated)
        found["record-usage!"][2][1][2][0] = "1111"
        with self.assertRaisesRegex(AssertionError, "тіло макросу"):
            verify_macro_cutover(mutated)

    def test_reject_hidden_direct_d5_and_arity_drift(self):
        mutated = deepcopy(self.expressions)
        found = verify_macro_cutover(mutated)
        found["defmodule"][2][0] = "00011"
        with self.assertRaisesRegex(AssertionError, "host-конструктора"):
            verify_macro_cutover(mutated)
        mutated = deepcopy(self.expressions)
        found = verify_macro_cutover(mutated)
        found["advise"][2][1][1].reverse()
        with self.assertRaisesRegex(AssertionError, "порядок"):
            verify_macro_cutover(mutated)

    def test_all_current_tables_preserve_exact_d1_to_d10_widths(self):
        # Перевіряємо ТІЛЬКИ канонічні ключі таблиць. D7 keyboard/v2
        # 128/128 не є історичним owner-v1 occupancy 126/128.
        for width in range(1, 11):
            with self.subTest(domain=f"D{width}"):
                table = (ROOT / f"lib/domains/d{width}.lisp").read_text(
                    encoding="utf-8"
                )
                keys = re.findall(r"(?m)^  \(([01]+)\s", table)
                self.assertEqual(keys,
                                 [f"{value:0{width}b}"
                                  for value in range(1 << width)])


if __name__ == "__main__":
    unittest.main()
