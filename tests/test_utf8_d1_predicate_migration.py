#!/usr/bin/env python3
"""Виконавчі D1-предикати UTF-8: AST-позиції, арність, ратифіковані біти, мутації."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/utf8.lisp"
YES = ["010", ["001", []]]
NO = ["101", ["001", ["0"]], ["001", ["1"]]]
EXPECTED = {
    "utf8-in-range?": [0, 1, 0],
    "utf8-continuation-byte?": [1, 0],
    "utf8-byte?": [0, 1, 0],
    "utf8-all-bytes?": [1, 0, 0],
    "utf8-two-continuations?": [0, 1, 0],
}


def parse_forms(source):
    scanner = r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()]+'
    words = [m.group(0) for m in re.finditer(scanner, source)
             if not m.group(0).startswith(";")]
    stack = [[]]
    for word in words:
        if word == "(":
            group = []
            stack[-1].append(group)
            stack.append(group)
        elif word == ")":
            if len(stack) < 2:
                raise ValueError("extra close")
            stack.pop()
        else:
            stack[-1].append(word)
    if len(stack) != 1:
        raise ValueError("unclosed form")
    return stack[0]


def audit(source):
    functions = {
        form[1]: form for form in parse_forms(source)
        if isinstance(form, list) and len(form) >= 3 and form[0] == "0011"
    }
    findings = {}
    for name, expected in EXPECTED.items():
        if name not in functions:
            raise ValueError(f"missing {name}")
        actual = []

        def walk(n):
            if not isinstance(n, list):
                return
            if n and n[0] == "110":
                for clause in n[1:]:
                    if not isinstance(clause, list) or len(clause) != 2:
                        raise ValueError(f"{name}: malformed 2-field COND")
                    value = clause[1]
                    if value in ("0", "1"):
                        raise ValueError(f"{name}: unqualified Number in D1 result")
                    if value == YES:
                        actual.append(1)
                    elif value == NO:
                        actual.append(0)
            for child in n:
                walk(child)

        walk(functions[name])
        if actual != expected:
            raise ValueError(f"{name}: branch positions changed: {actual}")
        findings[name] = actual
    return findings


class Utf8PredicateD1Cutover(unittest.TestCase):
    def test_14_precise_arity_checked_control_results(self):
        result = audit(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(sum(len(values) for values in result.values()), 14)

    def test_numeric_operands_and_domain_codes_remain_data(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("(11110111 (00101100 b 1) 0)", source)
        self.assertIn("(utf8-in-range? b 0 255)", source)
        self.assertIn("(utf8-in-range? b 128 191)", source)
        self.assertIn("(110011100 text)", source)

    def test_exact_domain_authority_not_flat_byte(self):
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        d8 = (ROOT / "lib/domains/d8.lisp").read_text(encoding="utf-8")
        self.assertRegex(d1, r"(?m)^\s*\(0\s+\(ук ні\)")
        self.assertRegex(d1, r"(?m)^\s*\(1\s+\(ук так\)")
        for bits, name in (("001", "QUOTE"), ("010", "ATOM"),
                           ("101", "EQ"), ("110", "COND")):
            self.assertRegex(d3, rf"(?m)^\s*\({bits}\s+.*\(LISP {name}\)")
        self.assertRegex(d8, r"(?m)^\s*\(11110111\s+.*\(LISP EQUAL\)")

    def test_two_negative_mutations_are_rejected(self):
        source = SOURCE.read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            audit(source.replace("(010 (001 ()))", "1", 1))
        with self.assertRaises(ValueError):
            audit(source.replace("(101 (001 (0)) (001 (1)))", "0", 1))


if __name__ == "__main__":
    unittest.main()
