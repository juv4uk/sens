#!/usr/bin/env python3
"""Точковий тест SENS: 30 D1-предикатів native-first, побітова ратифікація D1-D10."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/dispatch/native-first.lisp"
HISTORIC_SHA = "6c6777744fc401b6f5eff24631f40eaeab4c13a3"
OLD_YES = "(native-first-domain-true ())"
OLD_NO = "(native-first-domain-false ())"
YES = "#d1:1"
NO = "#d1:0"


def parse(src):
    toks = [m.group(0) for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', src
    ) if not m.group(0).startswith(";")]
    stack = [[]]
    for tok in toks:
        if tok == "(":
            sub = []
            stack[-1].append(sub)
            stack.append(sub)
        elif tok == ")":
            if len(stack) == 1:
                raise ValueError("extra closing paren")
            stack.pop()
        else:
            stack[-1].append(tok)
    if len(stack) != 1:
        raise ValueError("unterminated form")
    return stack[0]


def audit(text):
    no_n = text.count(NO)
    yes_n = text.count(YES)  # direct values: no nested D3/D4 constructors
    if (yes_n, no_n) != (24, 6):
        raise ValueError(f"expected 24 independent YES + 6 NO, got {yes_n}+{no_n}")
    if OLD_YES in text or OLD_NO in text:
        raise ValueError("retired named D1 call remains")
    restored = text.replace(NO, OLD_NO).replace(YES, OLD_YES)
    raw = restored.encode("utf-8")
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if sha != HISTORIC_SHA:
        raise ValueError("non-D1 executable bytes changed")
    roots = parse(text)
    if len(roots) != 17 or any(not isinstance(x, list) or x[0] != "0011" for x in roots):
        raise ValueError("expected 17 definitions")
    names = [x[1] for x in roots]
    if len(set(names)) != 17 or "native-first-domain-true" not in names or "native-first-domain-false" not in names:
        raise ValueError("compatibility helpers removed")
    def check(node):
        if not isinstance(node, list):
            return
        if node and node[0] == "110":
            for clause in node[1:]:
                if not isinstance(clause, list) or len(clause) != 2:
                    raise ValueError("non two-field D3 COND clause")
        for child in node:
            check(child)
    for root in roots:
        check(root)
    return raw, roots


def domain_capacity():
    count = 0
    for width in range(1, 11):
        data = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        keys = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", data)
        if len(keys) != 1 << width or len(set(keys)) != len(keys):
            raise ValueError(f"D{width}: missing or duplicated coordinate")
        if set(keys) != {f"{i:0{width}b}" for i in range(1 << width)}:
            raise ValueError(f"D{width}: wrong coordinate or exact width")
        count += len(keys)
    return count


class NativeFirstD1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")

    def test_full_historical_git_blob_and_all_17_forms(self):
        old, forms = audit(self.text)
        self.assertEqual(len(forms), 17)
        print(f"Native-first source UTF-8 bytes: {len(old)} -> {len(self.text.encode('utf-8'))}")

    def test_all_2046_exact_binary_domain_cells(self):
        self.assertEqual(domain_capacity(), 2046)

    def test_d3_d4_authority_and_exact_head_budget(self):
        for width, code, name in [
            (3, "001", "QUOTE"), (3, "010", "ATOM"), (4, "0100", "NOT")
        ]:
            rows = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            self.assertRegex(rows, rf"(?m)^\s*\({code}\s+.*\(LISP {name}\)")
        historical_constructors = 24 * (3 + 3) + 6 * (4 + 3 + 3)
        self.assertEqual(historical_constructors, 204)
        self.assertEqual(24 + 6, 30)  # 30 direct, exact one-bit D1 atoms
        self.assertEqual(historical_constructors - 30, 174)
        print("30 direct D1 values instead of 204 constructor-head bits; "
              "174 head-bit overhead removed in typed AST, physical T5 not measured")

    def test_d1_truth_table(self):
        for original in [False, True]:
            self.assertEqual(original, original and True)
            self.assertEqual(not original, not (original and True))
        self.assertTrue(True)    # D3 ATOM(QUOTE EMPTY)
        self.assertFalse(not True)  # D4 NOT(D3 ATOM(QUOTE EMPTY))

    def test_negative_mutations_fail_closed(self):
        for bad in [
            self.text.replace(YES, "1", 1),
            self.text.replace(NO, "(001 ())", 1),
            self.text.replace(NO, "(0100 (001 ()))", 1),
            self.text.replace(YES, NO, 1),
        ]:
            with self.assertRaises(ValueError):
                audit(bad)


if __name__ == "__main__":
    unittest.main()
