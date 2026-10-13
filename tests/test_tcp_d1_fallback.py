#!/usr/bin/env python3
"""Лише механічні координати/AST; SENS-твердження живуть у binary fixture.

Не оцінює логіку TCP, не задає truth table, не визначає семантику D1.
Уся семантика: tests/fixtures/semantic/tcp-exact-selftest.bits.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/tcp.lisp"
WITNESS = ROOT / "tests/fixtures/semantic/tcp-exact-selftest.bits"
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+')


def forms(source: str):
    stack = [[]]
    for match in TOKEN.finditer(source):
        value = match.group()
        if value.startswith(";"):
            continue
        if value == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif value == ")":
            if len(stack) == 1:
                raise ValueError("надлишкова закривальна дужка")
            stack.pop()
        else:
            stack[-1].append(value)
    if len(stack) != 1:
        raise ValueError("незавершена форма")
    return stack[0]


def exact_domains():
    rows = []
    for width in range(1, 11):
        path = ROOT / "lib/domains" / f"d{width}.lisp"
        keys = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", path.read_text(encoding="utf-8"))
        rows.append((width, keys))
    return rows


class TcpMechanicalDomainCensus(unittest.TestCase):
    def test_all_2046_coordinates_retain_exact_domain_width(self):
        total, meaningful_bits = 0, 0
        for width, words in exact_domains():
            self.assertEqual(len(words), 1 << width, f"D{width} resident count")
            self.assertEqual(len(set(words)), 1 << width, f"D{width} uniqueness")
            self.assertEqual(
                set(words),
                {format(value, f"0{width}b") for value in range(1 << width)},
                f"D{width} leading zeros/width",
            )
            total += len(words)
            meaningful_bits += width * len(words)
        self.assertEqual((total, meaningful_bits), (2046, 18434))

    def test_two_tcp_bindings_use_unambiguous_d4_heads(self):
        source = SOURCE.read_text(encoding="utf-8")
        tree = forms(source)
        self.assertEqual(len(tree), 7)
        defs = {definition[1]: definition for definition in tree}
        self.assertEqual(len(defs), 7)
        for name in ("tcp-read-bytes->text", "tcp-write-via-raw"):
            outer = defs[name]
            self.assertEqual(outer[0], "0011")
            self.assertEqual(outer[2][0], "0010")
            application = outer[2][2]
            self.assertEqual(len(application), 2)
            closure = application[0]
            self.assertEqual(closure[0], "0010")
            self.assertEqual(len(closure[1]), 1)
            self.assertEqual(len(closure), 3)
        self.assertNotIn("(001000 ", source)
        self.assertNotIn("(00001000 ", source)

    def test_sens_fixture_is_full_binary_d2_with_exact_nine_bit_calls(self):
        words = WITNESS.read_text(encoding="ascii").split()
        self.assertEqual(len(words), 51)
        self.assertEqual(sum(map(len, words)), 127)
        self.assertTrue(all(set(word) <= {"0", "1"} for word in words))
        self.assertTrue(all(len(word) in (1, 2, 3, 9) for word in words))
        self.assertEqual(words.count("001101001"), 2)
        self.assertEqual(words.count("110011100"), 1)
        self.assertNotIn("11110111", words)  # W8 не вгадуємо як D8

    def test_width_mutation_never_becomes_valid_same_domain_code(self):
        words = {width: set(rows) for width, rows in exact_domains()}
        self.assertIn("001101001", words[9])
        self.assertNotIn("001101001"[:-1], words[9])
        self.assertIn("0010", words[4])
        self.assertNotIn("0010"[:-1], words[4])


if __name__ == "__main__":
    unittest.main()
