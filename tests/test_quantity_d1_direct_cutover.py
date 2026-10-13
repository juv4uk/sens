#!/usr/bin/env python3
"""Exact W1 cutover of 13 branch results in the primary scientific-quantity library."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/quantity.lisp"
HISTORICAL_BLOB = "ec01dda338d186a10c8335371a24d15638cf6d58"
OLD = "(010 (001 ()))"
NEW = "#d1:1"
OLD_NOTE = "; (101 (001 (0)) (001 (1))). D1:1 remains (010 (001 ())). Width is identity."
NEW_NOTE = "; (101 (001 (0)) (001 (1))). D1:1 is projected directly as #d1:1. Width is identity."


def tokens(raw):
    regex = r'"(?:\\.|[^"\\])*"|;[^\n]*|\(|\)|[^\s()";]+'
    return [m.group() for m in re.finditer(regex, raw) if not m.group().startswith(";")]


def expressions(raw):
    tree = [[]]
    for token in tokens(raw):
        if token == "(":
            node = []
            tree[-1].append(node)
            tree.append(node)
        elif token == ")":
            if len(tree) == 1:
                raise ValueError("unexpected close")
            tree.pop()
        else:
            tree[-1].append(token)
    if len(tree) != 1:
        raise ValueError("unclosed expression")
    return tree[0]


def restore(raw):
    if raw.count(NEW) != 14:  # 13 live expressions + one explanatory comment
        raise ValueError("missing or extra direct D1")
    if any(OLD in line for line in raw.splitlines() if not line.lstrip().startswith(";")):
        raise ValueError("old D3 construction still live")
    if raw.count(NEW_NOTE) != 1:
        raise ValueError("incorrect provenance annotation")
    restored = raw.replace(NEW_NOTE, OLD_NOTE)
    restored = "\n".join(
        line if line.lstrip().startswith(";") else line.replace(NEW, OLD)
        for line in restored.split("\n")
    )
    old = restored.encode("utf-8")
    digest = hashlib.sha1(b"blob " + str(len(old)).encode() + b"\0" + old).hexdigest()
    if digest != HISTORICAL_BLOB:
        raise ValueError(f"unexpected source drift {digest}")
    return old


def widths():
    for width in range(1, 11):
        raw = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        keys = re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", raw)
        expected = {f"{i:0{width}b}" for i in range(1 << width)}
        if len(keys) != (1 << width) or set(keys) != expected:
            raise ValueError(f"D{width}: wrong width, missing/duplicate coordinate")
    return 2046


class QuantityDirectD1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_full_source_matches_historical_git_blob_after_thirteen_cuts(self):
        old = restore(self.source)
        self.assertEqual(len(expressions(self.source)), 43)
        self.assertEqual(self.source.count(NEW), 14)
        self.assertEqual(self.source.count(OLD), 1)  # documentary historical example only
        print(f"QUANTITY-D1: UTF8 source {len(old)} -> "
              f"{len(self.source.encode('utf-8'))} bytes; 13 direct D1 results")

    def test_full_domains_have_2046_exact_coordinates(self):
        self.assertEqual(widths(), 2046)

    def test_identity_and_construction_cost_are_not_confused(self):
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        d3 = (ROOT / "lib/domains/d3.lisp").read_text(encoding="utf-8")
        self.assertRegex(d1, r"(?m)^\s*\(1\s+\(ук\s+так\)")
        self.assertRegex(d3, r"(?m)^\s*\(001\s+.*\(LISP QUOTE\)")
        self.assertRegex(d3, r"(?m)^\s*\(010\s+.*\(LISP ATOM\)")
        old_heads = 13 * (3 + 3)
        semantic_bits = 13 * 1
        self.assertEqual((old_heads, semantic_bits, old_heads - semantic_bits), (78, 13, 65))
        print("QUANTITY-D1: 78 old D3 function-head bits -> direct 13 W1 values; "
              "65 head-bit overhead eliminated, physical T5 NOT measured")

    def test_status_kind_predicates_retained_in_source(self):
        roots = expressions(self.source)
        defs = {x[1]: x for x in roots if isinstance(x, list) and len(x) > 2 and x[0] == "0011"}
        status = defs["scientific-constant-status-valid?"]
        kind = defs["scientific-constant-kind-valid?"]
        self.assertEqual(len(status[2][2][1:]), 3)
        self.assertEqual(len(kind[2][2][1:]), 4)
        for func in (status, kind):
            for branch in func[2][2][1:]:
                self.assertEqual(len(branch), 2)
                self.assertEqual(branch[1], NEW)

    def test_invalid_mutations_do_not_qualify_as_d1(self):
        for corrupted in [
            self.source.replace(NEW, "1", 1),
            self.source.replace(NEW, "0", 1),
            self.source.replace(NEW, "(001 ())", 1),
            self.source.replace(NEW, OLD, 1),
        ]:
            with self.assertRaises(ValueError):
                restore(corrupted)


if __name__ == "__main__":
    unittest.main()
