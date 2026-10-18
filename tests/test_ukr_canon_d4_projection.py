"""Точкові source-свідки D3/D4 → повна укр для lib/canon.lisp.

Жодного Python-eval семантики SENS: перевіряємо ратифіковану identity,
структуру законів та byte-exact зворотність дозволених змін.
Фізичний SENS-виклик і транспорт тут не доказуються.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/canon.lisp"
D3 = ROOT / "lib/domains/d3.lisp"
D4 = ROOT / "lib/domains/d4.lisp"

ORIGINAL_SOURCE_BLOB = "905513fdba37248fe7ac214e678869e08af5ae74"
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


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def restored_source(source: str) -> str:
    # Повертаємо лише ратифіковані D3-голови в точне старе написання.
    # Ураховуємо будь-який пробіл або перенесення рядка після голови.
    for code, peer, _en, _lisp, _count in D3_MAPPING:
        source = re.sub(r"\\(" + re.escape(peer) + r"(?=\\s|\\))", "(" + code, source)
    for code, peer, _en, _lisp, _count in D4_MAPPING:
        source = source.replace(f"({peer} ", f"({code} ")
    return source


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
                pattern = r"\\(" + re.escape(peer) + r"(?=\\s|\\))"
                expected = count + (1 if bits == "001" else 0)
                self.assertEqual(len(re.findall(pattern, code)), expected)
                self.assertNotRegex(code, r"\\(" + bits + r"(?=\\s|\\))")

    def test_canon_empty_list_uses_exact_d3_quote_without_wire_literal(self):
        self.assertIn("(визначити canon-empty-list (як-є ()))", self.source)
        self.assertNotIn("(визначити canon-empty-list (001 ()))", self.source)
        for token in ("(як-є x)", "(як-є y)", "(як-є ())"):
            self.assertIn(token, self.source)
        for old_head in ("(001 x)", "(001 y)", "(001 ())"):
            self.assertNotIn(old_head, runnable_text(self.source))

    def test_every_unrelated_byte_is_unchanged(self):
        raw = restored_source(self.source).encode("utf-8")
        self.assertEqual(git_blob(raw), ORIGINAL_SOURCE_BLOB)

    def test_mutation_of_a_quoted_law_fails_byte_exact_witness(self):
        restored = restored_source(self.source)
        changed = restored.replace("(001 x)", "(001 z)", 1)
        self.assertNotEqual(git_blob(changed.encode("utf-8")), ORIGINAL_SOURCE_BLOB)

    def test_wrong_d3_peer_fails_exact_original_blob_witness(self):
        mutated = self.source.replace("(тотожне? ", "(решта ", 1)
        self.assertNotEqual(mutated, self.source)
        restored = restored_source(mutated).encode("utf-8")
        self.assertNotEqual(git_blob(restored), ORIGINAL_SOURCE_BLOB)

    def test_canon_public_entrypoints_survive(self):
        for name in ("canon-empty-list", "canon-law-result",
                     "canon-law-satisfied", "canon-law-violated",
                     "canon-law-status", "canon-conformance-result"):
            self.assertIn(f"(визначити {name}", self.source)

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
