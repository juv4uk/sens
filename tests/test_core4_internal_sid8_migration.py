#!/usr/bin/env python3
"""Core4 width-firewall: 2046 residents, exact domains, no retired executable heads."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core4.lisp"
DOMAIN_DIR = ROOT / "lib/domains"

spec = importlib.util.spec_from_file_location("_core4_ast", ROOT / "scripts/cond-modernize.py")
if spec is None or spec.loader is None:
    raise RuntimeError("AST parser unavailable")
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)

FORBIDDEN_ACTIVE = {
    "00001010",  # historical W8 DEFMACRO
    "01000111",  # historical internal DIGIT->STRING slot
    "01011010",  # historical MONO-NS slot
    "11110111",  # historical structural EQUAL slot
    "10110001",  # historical recursive STRING< slot
}
D9_REQUIRED = {
    "110011100": "STRING-EMPTY?",
    "110011101": "STRING-REST",
    "110011110": "STRING-APPEND",
    "110101011": "STRING-FIRST",
}


def active_heads(source: str) -> Counter:
    counts: Counter = Counter()
    stack = list(parser.parse(source))
    while stack:
        node = stack.pop()
        if node.opaque or not node.children:
            continue
        head = node.children[0].atom
        if head is not None:
            counts[head] += 1
        if head in {"001", "як-є", "quote"}:
            continue
        stack.extend(node.children)
    return counts


def active_atoms(source: str) -> list[str]:
    atoms: list[str] = []
    stack = list(parser.parse(source))
    while stack:
        node = stack.pop()
        if node.opaque:
            continue
        if node.atom is not None:
            atoms.append(node.atom)
            continue
        if not node.children:
            continue
        head = node.children[0].atom
        if head in {"001", "як-є", "quote"}:
            if head is not None:
                atoms.append(head)
            continue
        stack.extend(node.children)
    return atoms


def domain_rows(width: int) -> dict[str, str]:
    text = (DOMAIN_DIR / f"d{width}.lisp").read_text(encoding="utf-8")
    rows: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(rf"^\s*\(([01]{{{width}}})\s+", line)
        if not m:
            continue
        lisp = re.search(r'\(LISP\s+(\(\)|"[^"]*"|[^()\s]+)\)', line)
        if lisp is None:
            raise ValueError(f"D{width} malformed LISP field at {m.group(1)}")
        name = lisp.group(1)
        rows[m.group(1)] = name[1:-1] if name.startswith('"') else name
    return rows


def verify(source: str) -> None:
    heads = active_heads(source)
    if "t" in active_atoms(source):
        raise ValueError("Core4 still contains executable host truth T")
    for head in FORBIDDEN_ACTIVE:
        if heads[head]:
            raise ValueError("forbidden migrated head survived: " + head)

    d8 = domain_rows(8)
    for head in heads:
        if len(head) == 8 and set(head) <= {"0", "1"} and head not in d8:
            raise ValueError("active 8-bit head is not a D8 resident: " + head)

    d9 = domain_rows(9)
    for bits, name in D9_REQUIRED.items():
        if heads[bits] < 1:
            raise ValueError(f"Core4 lost exact D9 head {bits} {name}")
        if d9.get(bits) != name:
            raise ValueError(f"D9 authority drift: {bits} -> {d9.get(bits)!r}, expected {name}")

    if heads["mono-ns"] != 1:
        raise ValueError("Core4 must retain exactly one honest MONO-NS mechanism boundary")
    if domain_rows(10).get("0011110110") != "MONO-NS":
        raise ValueError("D10 MONO-NS authority drifted")


class Core4WidthFirewall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_all_2046_d1_d10_residents_are_dense_exact_width(self):
        total = 0
        for width in range(1, 11):
            rows = domain_rows(width)
            expected = {f"{n:0{width}b}" for n in range(1 << width)}
            self.assertEqual(set(rows), expected, f"D{width} must be complete exact-width authority")
            total += len(rows)
        self.assertEqual(total, 2046)

    def test_core4_obeys_domain_width_firewall(self):
        verify(self.source)

    def test_current_d8_doseq_must_never_be_hidden_as_old_sid8_quote(self):
        # D3:001 цитує; чинний D8:00000001 є DOSEQ, не цитатою SID8.
        actual = active_heads("(00000001 (додати 2 3))")
        self.assertEqual(actual["00000001"], 1)
        self.assertEqual(actual["додати"], 1)
        self.assertIn("t", active_atoms("(00000001 t)"))
        self.assertNotIn("t", active_atoms("(001 t)"))
        self.assertNotIn("t", active_atoms("(як-є t)"))
        with self.assertRaisesRegex(ValueError, "host truth"):
            verify(self.source + "\n(00000001 t)\n")

    def test_seven_macros_are_language_owned_not_w8_defmacro(self):
        heads = active_heads(self.source)
        self.assertEqual(heads["00001010"], 0)
        self.assertEqual(heads["make-macro"], 7)
        for name in ["and", "or", "let", "let*", "->", "->>", "матеріалізувати-сталі-відповідники"]:
            self.assertIn(f"(0011 {name}", self.source)

    def test_negative_old_macro_head_is_rejected(self):
        mutated = self.source.replace("(0011 and", "(00001010 and", 1)
        with self.assertRaisesRegex(ValueError, "forbidden migrated head"):
            verify(mutated)

    def test_negative_cross_width_collision_is_rejected(self):
        mutated = self.source.replace("(110101011 ", "(11100000 ")
        with self.assertRaisesRegex(ValueError, "lost exact D9"):
            verify(mutated)

    def test_negative_host_truth_is_rejected(self):
        mutated = self.source.replace("(010 (001 ()))", "t", 1)
        with self.assertRaisesRegex(ValueError, "host truth"):
            verify(mutated)


if __name__ == "__main__":
    unittest.main()
