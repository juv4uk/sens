"""Точкові source-свідки D3/D4 → повна укр для lib/canon.lisp.

Жодного Python-eval семантики SENS: перевіряємо ратифіковану identity,
структуру законів та byte-exact зворотність дозволених змін.
Фізичний SENS-виклик і транспорт тут не доказуються.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/canon.lisp"
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"

D3_MAPPING = (
    ("001", "як-є", "quote", "QUOTE", 65),
    ("010", "атом?", "atom?", "ATOM", 4),
    ("011", "решта", "cdr", "CDR", 15),
    ("100", "перше", "car", "CAR", 7),
    ("101", "тотожне?", "eq?", "EQ", 16),
    ("110", "за-умовою", "cond", "COND", 21),
    ("111", "сполучити", "cons", "CONS", 22),
)

D4_MAPPING = (
    ("0011", "визначити", "define", "DEFINE", 19),
    ("0010", "функція", "lambda", "LAMBDA", 18),
)


def runnable_text(source: str) -> str:
    """Пропускаємо коментарі/рядки, щоб не вважати їх викличними головами."""
    lines = []
    for line in source.splitlines():
        clean, quoted, escape = [], False, False
        for ch in line:
            if quoted:
                clean.append(" ")
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    quoted = False
            elif ch == '"':
                quoted = True
                clean.append(" ")
            elif ch == ";":
                break
            else:
                clean.append(ch)
        lines.append("".join(clean))
    return "\n".join(lines)


class CanonD4FullUkrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.d3 = D3.read_text(encoding="utf-8")
        cls.d4 = D4.read_text(encoding="utf-8")

    def test_exact_ratified_domain_authority_for_all_three_heads(self):
        for width, bits, ukr, en, lisp, table in (
            (3, "001", "як-є", "quote", "QUOTE", self.d3),
            (3, "010", "атом?", "atom?", "ATOM", self.d3),
            (3, "011", "решта", "cdr", "CDR", self.d3),
            (3, "100", "перше", "car", "CAR", self.d3),
            (3, "101", "тотожне?", "eq?", "EQ", self.d3),
            (3, "110", "за-умовою", "cond", "COND", self.d3),
            (3, "111", "сполучити", "cons", "CONS", self.d3),
            (4, "0010", "функція", "lambda", "LAMBDA", self.d4),
            (4, "0011", "визначити", "define", "DEFINE", self.d4),
        ):
            records = [line for line in table.splitlines()
                       if line.lstrip().startswith(f"({bits} ")]
            self.assertEqual(len(bits), width)
            self.assertEqual(len(records), 1, f"D{width}:{bits}")
            for item in (f"(укр {ukr})", f"(en {en})", f"(LISP {lisp})"):
                self.assertIn(item, records[0])

    def test_all_d4_define_lambda_heads_are_full_ukrainian(self):
        code = runnable_text(self.source)
        for bits, ukr, _en, _lisp, count in D4_MAPPING:
            self.assertEqual(code.count(f"({ukr} "), count)
            self.assertEqual(code.count(f"({bits} "), 0)

    def test_all_d3_executable_heads_are_full_ukrainian(self):
        code = runnable_text(self.source)
        for bits, peer, _en, _lisp, count in D3_MAPPING:
            with self.subTest(bits=bits):
                pattern = r"\(" + re.escape(peer) + r"(?=\s|\))"
                expected = count + (1 if bits == "001" else 0)
                self.assertEqual(len(re.findall(pattern, code)), expected)
                self.assertNotRegex(code, r"\(" + bits + r"(?=\s|\))")

    def test_canon_empty_list_uses_exact_d3_quote_without_wire_literal(self):
        self.assertIn("(визначити канон-порожній-список (як-є ()))", self.source)
        self.assertNotRegex(self.source, r"\(визначити canon-empty-list\b")
        for token in ("(як-є x)", "(як-є y)", "(як-є ())"):
            self.assertIn(token, self.source)
        for old_head in ("(001 x)", "(001 y)", "(001 ())"):
            self.assertNotIn(old_head, runnable_text(self.source))

        # Цитовані десяткові дані зберігають числове значення:
        # їх не можна перетворювати на предикат D1 «так».
        for datum in ("(як-є (1 2 3))", "(як-є (1 2 . 3))"):
            self.assertIn(datum, self.source)
        for corrupted in ("(як-є (так 2 3))", "(як-є (так 2 . 3))"):
            self.assertNotIn(corrupted, self.source)

    def test_canon_public_entrypoints_survive(self):
        for name in ("канон-порожній-список", "канон-закон-результат",
                     "канон-закон-виконаний", "канон-закон-порушений",
                     "канон-закон-стан", "канон-відповідність-результат"):
            self.assertIn(f"(визначити {name}", self.source)
        self.assertNotRegex(self.source, r"\(визначити canon-[a-z-]+\b")

    def test_parentheses_balance_excluding_comments_and_strings(self):
        level = 0
        for char in runnable_text(self.source):
            if char == "(":
                level += 1
            elif char == ")":
                level -= 1
                self.assertGreaterEqual(level, 0)
        self.assertEqual(level, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
