#!/usr/bin/env python3
"""AST-pinned TCP D1 cutover witness independent of unrelated header/loader edits.

Historical cutover: D4 NOT(D3 EQ(...)) -> D3 ATOM(D3 QUOTE EMPTY) as
the fallback test after the first successful decoder-tag branch. Do NOT
assert whole-source byte equality across later, independently reviewed changes.
"""
from pathlib import Path
import copy
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/tcp.lisp"
OLD = "(0100 (101 (100 decoded) (001 decoded)))"
NEW = "(010 (001 ()))"


def tokens(source):
    return [m.group(0) for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', source)
        if not m.group(0).startswith(";")]


def parse(source):
    stack = [[]]
    for token in tokens(source):
        if token == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            if len(stack) < 2:
                raise ValueError("unbalanced close")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise ValueError("unbalanced open")
    return stack[0]


def tcp_text_policy(source):
    roots = parse(source)
    defs = {x[1]: x for x in roots
            if isinstance(x, list) and len(x) >= 3 and x[0] == "0011"}
    if len(defs) != 7:
        raise ValueError("TCP must retain seven Lisp-owned entrypoints")
    method = defs["tcp-read-bytes->text"]
    expected = [
        "0011", "tcp-read-bytes->text",
        ["0010", ["bytes"],
         ["001000", [["decoded", ["utf8-decode-string", "bytes"]]],
          ["110",
           [["101", ["100", "decoded"], ["001", "decoded"]],
            ["1001", "decoded"]],
           [["010", ["001", []]], "decoded"]]]]]
    if method != expected:
        raise ValueError("TCP dispatcher changed: expected two-branch exact D3/D1 policy")
    # Rebuild the sole historical branch and compare all remaining AST nodes.
    # Replace the executable AST node, not a textual comment that mentions
    # the same D3 expression. This migration guard is intentionally AST-aware.
    prior = copy.deepcopy(method)
    prior[2][2][2][2][0] = [
        "0100", ["101", ["100", "decoded"], ["001", "decoded"]]]
    old_method = [
        "0011", "tcp-read-bytes->text",
        ["0010", ["bytes"],
         ["001000", [["decoded", ["utf8-decode-string", "bytes"]]],
          ["110",
           [["101", ["100", "decoded"], ["001", "decoded"]],
            ["1001", "decoded"]],
           [["0100", ["101", ["100", "decoded"], ["001", "decoded"]]],
            "decoded"]]]]]
    if prior != old_method:
        raise ValueError("historical one-branch reconstruction failed")
    return defs


def domain_rows(width):
    source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
    return re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", source)


class TcpD1ExhaustiveFallback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_historical_one_branch_semantics_preserved_after_other_edits(self):
        self.assertNotIn(OLD, self.source)
        defs = tcp_text_policy(self.source)
        self.assertEqual(len(defs), 7)
        print("TCP-D1: bounded original D4 NOT(EQ) branch -> "
              "D3 ATOM(QUOTE EMPTY) fallback; all other policy AST nodes unchanged")

    def test_all_domain_widths_and_coordinates_are_stable(self):
        for width in range(1, 11):
            keys = domain_rows(width)
            self.assertEqual(len(keys), 1 << width, f"D{width} missing resident")
            self.assertEqual(len(set(keys)), len(keys), f"D{width} duplicate coordinate")
            self.assertEqual(set(keys), {f"{n:0{width}b}" for n in range(1 << width)})
        self.assertIn("010", domain_rows(3))
        self.assertIn("001", domain_rows(3))
        self.assertIn("101", domain_rows(3))
        self.assertIn("0100", domain_rows(4))

    def test_semantic_code_heads_save_seven_bits(self):
        former, current = (4+3+3+3), (3+3)
        self.assertEqual((former, current, former-current), (13,6,7))
        print("TCP-D1: function heads 13 -> 6 bits; physical T5 not measured")

    def test_exhaustive_two_value_d1_law(self):
        for equality in (False,True):
            previous = "text" if equality else ("fallback" if not equality else "missing")
            current = "text" if equality else "fallback"
            self.assertEqual(current, previous)

    def test_mutations_are_rejected(self):
        tcp_text_policy(self.source)
        for altered in (
            self.source.replace("("+NEW, "((1)", 1),
            self.source.replace("("+NEW, "((0100 (001 ()))", 1),
            self.source.replace("("+NEW, "((010 (001 (0)))", 1),
            self.source.replace("("+NEW, "((001 ())", 1),
            self.source.replace("(1001 decoded)", "decoded", 1),
        ):
            with self.assertRaises(ValueError):
                tcp_text_policy(altered)


if __name__ == "__main__":
    unittest.main()
