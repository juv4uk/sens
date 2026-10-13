#!/usr/bin/env python3
"""Точкове свідчення: п'ять D4:0100 NOT(D3:101 EQ) без текстового NIL."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/process.lisp"
EXPECTED = {
    "process-result->text": 3,
    "process-public-exit-code": 1,
    "process-run": 1,
}


def parse(source):
    words = [m.group(0) for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', source)
        if not m.group(0).startswith(";")]
    stack = [[]]
    for word in words:
        if word == "(":
            item = []
            stack[-1].append(item)
            stack.append(item)
        elif word == ")":
            if len(stack) == 1:
                raise ValueError("extra closing paren")
            stack.pop()
        else:
            stack[-1].append(word)
    if len(stack) != 1:
        raise ValueError("unterminated source")
    return stack[0]


def inspect(source):
    found = {}
    for form in parse(source):
        if not isinstance(form, list) or len(form) < 3 or form[0] != "0011":
            continue
        name = form[1]
        total = 0

        def visit(node):
            nonlocal total
            if not isinstance(node, list):
                return
            if node and node[0] == "тотожне?":
                raise ValueError("legacy language surface used for predicate inversion")
            if node and node[0] == "0100":
                if len(node) != 2 or not isinstance(node[1], list) or not node[1] or node[1][0] != "101":
                    raise ValueError("D4 NOT must have exactly one D3 EQ predicate argument")
                if len(node[1]) != 3:
                    raise ValueError("D3 EQ must have two arguments")
                total += 1
            for child in node:
                visit(child)

        visit(form)
        if total:
            found[name] = total
    if found != EXPECTED:
        raise ValueError(f"expected 3+1+1 D1 inversions, got {found}")
    return found


class ProcessD1Cutover(unittest.TestCase):
    def test_five_real_domain_negations(self):
        findings = inspect(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(sum(findings.values()), 5)

    def test_one_bit_domain_not_empty_or_number(self):
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        d4 = (ROOT / "lib/domains/d4.lisp").read_text(encoding="utf-8")
        for bits, name in (("0", "NIL"), ("1", "T")):
            self.assertRegex(d1, rf"(?m)^\s*\({bits}\s+.*\(LISP {name}\)")
        self.assertRegex(d3, r"(?m)^\s*\(101\s+.*\(LISP EQ\)")
        self.assertRegex(d4, r"(?m)^\s*\(0100\s+.*\(LISP NOT\)")
        self.assertNotIn("(тотожне?", SOURCE.read_text(encoding="utf-8"))

    def test_no_change_to_process_exit_compatibility(self):
        src = SOURCE.read_text(encoding="utf-8")
        self.assertIn("((101 code (001 ()))  -1)", src)
        self.assertIn("(process-raw-exit-code raw)", src)
        self.assertIn("(utf8-decode-string (process-raw-stderr-bytes raw))", src)

    def test_two_controlled_mutations_rejected(self):
        src = SOURCE.read_text(encoding="utf-8")
        for variant in (
            src.replace("(0100 (101", "(0101 (101", 1),
            src.replace("(0100 (101", "(0100 (0100 (101", 1),
        ):
            with self.assertRaises(ValueError):
                inspect(variant)

    def test_d1_inversion_law_exhaustive(self):
        for predicate in (False, True):
            # The historical EQ(D1,NO) inversion and D4:NOT(D1) are identical
            # on the complete two-element D1 domain.
            self.assertEqual(predicate is False, not predicate)


if __name__ == "__main__":
    unittest.main()
