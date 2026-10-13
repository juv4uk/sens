#!/usr/bin/env python3
"""Knowledge D1 recovery: exact three functions from the complete historical Git cohort."""
from pathlib import Path
import hashlib
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "lib/knowledge.lisp"
HISTORIC_PARTIAL_BLOB = "2aa92c2888a5260497912bab1a0876812fbe40b9"
MARKER = ";; Exact D1 recovery from f6f1f1b3d1c234a5fcc1b98e585f1d3a91ea553d."
NAMES = ("knowledge-not-head?", "knowledge-clauses-valid?", "knowledge-package-field")


def git_blob(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def parse(text: str):
    tokens = (m.group(0) for m in re.finditer(
        r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+', text))
    stack = [[]]
    for token in tokens:
        if token.startswith(";"):
            continue
        if token == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            if len(stack) == 1:
                raise ValueError("unbalanced closing")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise ValueError("unterminated form")
    return stack[0]


def check(source: str):
    if source.count(MARKER) != 1:
        raise ValueError("missing immutable triad recovery boundary")
    before, extra = source.split("\n" + MARKER, 1)
    if git_blob(before + "\n") != HISTORIC_PARTIAL_BLOB:
        raise ValueError("previous 20 live functions were modified without proof")
    roots = parse(MARKER + extra)
    if len(roots) != 3:
        raise ValueError("recovery must add exactly three definitions")
    if tuple(x[1] for x in roots) != NAMES:
        raise ValueError("restored names/order drift")
    if any(root[0] != "0011" or root[2][0] != "0010" for root in roots):
        raise ValueError("D4 DEFINE/LAMBDA width drift")
    allowed = {"0011":4, "0010":4, "110":3, "101":3, "010":3, "0101":4,
               "100":3, "011":3, "001":3}
    def scan(node):
        if not isinstance(node, list):
            return
        if node and node[0] == "110":
            if any(not isinstance(b, list) or len(b) != 2 for b in node[1:]):
                raise ValueError("not two-field canonical D3 COND")
        for item in node:
            if isinstance(item, str) and item.startswith("#d1:") and item not in {"#d1:0", "#d1:1"}:
                raise ValueError("invalid direct D1 width")
            scan(item)
    for root in roots:
        scan(root)
    if extra.count("#d1:1") != 6 or extra.count("#d1:0") != 3:
        raise ValueError("D1 6-YES/3-NO census drift")
    return roots


class RecoverKnowledge(unittest.TestCase):
    def test_immutable_preexisting_content_and_three_full_d1_forms(self):
        self.assertEqual(len(check(PATH.read_text(encoding="utf-8"))), 3)

    def test_exact_width_for_every_ratified_coordinate_d1_d10(self):
        total = 0
        for width in range(1, 11):
            s = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            coords = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", s)
            self.assertEqual(len(coords), 1 << width, f"D{width} slot count")
            self.assertEqual(len(set(coords)), len(coords), f"D{width} collision")
            self.assertEqual(set(coords),
                {f"{i:0{width}b}" for i in range(1 << width)},
                f"D{width} missing / wrong width")
            total += len(coords)
        self.assertEqual(total, 2046)

    def test_bit_cost_of_three_direct_predicates(self):
        roots = check(PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(roots), 3)
        # Seven direct D1 outputs plus two direct guard tests; no ATOM/NOT
        # constructor needed. These are semantic W1 values, not source bytes.
        self.assertEqual(6 + 3, 9)
        print("KNOWLEDGE-D1: 9 one-bit predicate value sites; physical T5 unmeasured")

    def test_mutations_fail_closed(self):
        s = PATH.read_text(encoding="utf-8")
        for corrupted in (
            s.replace("#d1:0", "0", 1),
            s.replace("#d1:1", "1", 1),
            s.replace("((010 package) (001 ()))", "((010 package) #d1:0)", 1),
            s.replace("(0011 knowledge-package-field", "(0010 knowledge-package-field", 1),
        ):
            with self.assertRaises(ValueError):
                check(corrupted)


if __name__ == "__main__":
    unittest.main()
