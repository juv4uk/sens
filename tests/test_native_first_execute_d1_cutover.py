#!/usr/bin/env python3
"""Атомарний доказ D1-переходу мосту native-first: 18 констант та 2046 точних адрес."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/dispatch/native-first-execute.lisp"
HISTORIC_GIT_BLOB = "65a2437e5a15c1edec81be75adf92620e26631ad"
OLD_YES = "(native-first-domain-true ())"
OLD_NO = "(native-first-domain-false ())"


def forms(source: str):
    tokens = [m.group(0) for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', source
    ) if not m.group(0).startswith(";")]
    stack = [[]]
    for token in tokens:
        if token == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            if len(stack) == 1:
                raise ValueError("unexpected close")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise ValueError("unclosed form")
    return stack[0]


def prove_source(source: str):
    if (source.count("#d1:1"), source.count("#d1:0")) != (11, 7):
        raise ValueError("D1 direct-predicate census changed")
    if OLD_YES in source or OLD_NO in source:
        raise ValueError("named call remains")
    historical = source.replace("#d1:1", OLD_YES).replace("#d1:0", OLD_NO).encode("utf-8")
    blob = hashlib.sha1(b"blob " + str(len(historical)).encode() + b"\0" + historical).hexdigest()
    if blob != HISTORIC_GIT_BLOB:
        raise ValueError("unexpected non-D1 historical AST/text drift")
    definitions = forms(source)
    if len(definitions) != 13 or any(not isinstance(row, list) or row[0] != "0011"
                                     for row in definitions):
        raise ValueError("13 machine bridge definitions not preserved")
    names = [row[1] for row in definitions]
    if len(set(names)) != 13:
        raise ValueError("duplicate function definition")
    return historical, definitions


class DirectD1Bridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_exact_18_replacements_and_all_13_definitions(self):
        old, roots = prove_source(self.source)
        self.assertEqual(len(roots), 13)
        print(f"native-first-execute: UTF-8 source bytes {len(old)} -> "
              f"{len(self.source.encode('utf-8'))}")

    def test_whole_ladder_2046_exact_width_unique_addresses(self):
        total = 0
        for width in range(1, 11):
            s = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            coordinates = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", s)
            self.assertEqual(len(coordinates), 1 << width)
            self.assertEqual(set(coordinates),
                             {format(n, f"0{width}b") for n in range(1 << width)})
            total += len(coordinates)
        self.assertEqual(total, 2046)

    def test_one_bit_direct_values_remove_118_constructor_head_bits(self):
        # A W1 D1 value is 1 bit, not a function-call head.
        # YES: D3 ATOM + D3 QUOTE = 6 head bits.
        # NO: D4 NOT + D3 ATOM + D3 QUOTE = 10 head bits.
        before = 11 * (3 + 3) + 7 * (4 + 3 + 3)
        self.assertEqual(before, 136)
        self.assertEqual(before - 18, 118)
        self.assertIn("(010 (ук атом?)", (ROOT / "lib/domains/d3.lisp").read_text())
        self.assertIn("(0100 (ук хибне?)", (ROOT / "lib/domains/d4.lisp").read_text())
        print("D1 direct identity bit ledger: 136 old constructor-head bits; "
              "18 ideal value bits; 118 overhead bits eliminated at AST level. "
              "Physical T5 size NOT measured.")

    def test_five_adversarial_mutations_are_caught(self):
        variants = [
            self.source.replace("#d1:1", "1", 1),
            self.source.replace("#d1:0", "0", 1),
            self.source.replace("#d1:0", "#d1:1", 1),
            self.source.replace("#d1:1", "(001 ())", 1),
            self.source.replace("#d1:1", "#d1:01", 1),
        ]
        for mutation in variants:
            with self.assertRaises(ValueError):
                prove_source(mutation)

    def test_no_unadmitted_d7_d10_callability_is_assumed(self):
        self.assertNotRegex(self.source, r"(?m)^\s*\([01]{7}\s")
        self.assertNotRegex(self.source, r"(?m)^\s*\([01]{10}\s")


if __name__ == "__main__":
    unittest.main()
