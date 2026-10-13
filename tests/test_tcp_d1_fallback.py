#!/usr/bin/env python3
"""Лише механічні координати/AST; SENS-твердження живуть у binary fixture.

Не оцінює логіку TCP, не задає truth table, не визначає семантику D1.
Уся семантика: tests/fixtures/semantic/tcp-exact-selftest.lisp.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/tcp.lisp"
WITNESS = ROOT / "tests/fixtures/semantic/tcp-exact-selftest.lisp"
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

    def test_sens_fixture_heads_preserve_exact_width_and_no_named_calls(self):
        source = WITNESS.read_text(encoding="utf-8")
        tree = forms(source)
        self.assertEqual(len(tree), 1)
        heads = []

        def visit(node, quoted=False):
            if not isinstance(node, list) or not node:
                return
            head = node[0]
            if not quoted:
                if isinstance(head, str) and set(head) <= {"0", "1"}:
                    heads.append(head)
                elif isinstance(head, list):
                    visit(head)
                else:
                    raise AssertionError(f"небінарна виконувана голова: {head!r}")
            quote = head == "001"
            for arg in node[1:]:
                if isinstance(arg, list):
                    visit(arg, quoted or quote)

        visit(tree[0])
        self.assertIn("110", heads)
        self.assertIn("0010", heads)
        self.assertIn("11110111", heads)
        self.assertIn("001101001", heads)
        self.assertTrue(all(1 <= len(h) <= 9 for h in heads))

    def test_width_mutation_never_becomes_valid_same_domain_code(self):
        words = {width: set(rows) for width, rows in exact_domains()}
        self.assertIn("001101001", words[9])
        self.assertNotIn("001101001"[:-1], words[9])
        self.assertIn("0010", words[4])
        self.assertNotIn("0010"[:-1], words[4])


if __name__ == "__main__":
    unittest.main()
