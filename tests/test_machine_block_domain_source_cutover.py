#!/usr/bin/env python3
"""Точковий контроль: 17 виконуваних голів та 69 зекономлених бітів."""
from collections import Counter
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "docs/archive/historical/machine-block-original-200201b7.source.txt"
CURRENT = ROOT / "lib/machine/block.lisp"
EXACT = ROOT / "lib/machine/block-exact.lisp"
PIN = "200201b741787c4e144ad4194848acf51d7b439e"
SUCCESSORS = {
    "00001001": ("0011", "DEFINE", 6),
    "00001000": ("0010", "LAMBDA", 6),
    "00000001": ("001", "QUOTE", 1),
    "00100111": ("1110", "LIST", 2),
    "00101001": ("1111", "APPEND", 2),
}


def git_blob(data):
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def lex(source):
    clean = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
    return re.findall(r"\(|\)|[^\s()]+", clean)


class MachineBlockDomainCutover(unittest.TestCase):
    def test_pinned_historical_oracle(self):
        self.assertEqual(git_blob(ORIGINAL.read_bytes()), PIN)

    def test_only_seventeen_executable_heads_migrated(self):
        old = lex(ORIGINAL.read_text(encoding="utf-8"))
        current = lex(CURRENT.read_text(encoding="utf-8"))
        exact = lex(EXACT.read_text(encoding="utf-8"))
        self.assertEqual(
            Counter(x for x in old if x in SUCCESSORS),
            Counter({key: spec[2] for key, spec in SUCCESSORS.items()})
        )
        expected = [SUCCESSORS[x][0] if x in SUCCESSORS else x for x in old]
        self.assertEqual(expected, current, "Недопустима зміна AST або даних")
        self.assertEqual(current, exact, "Відхилення від незалежної exact-domain копії")
        self.assertEqual(len(old), len(current))
        self.assertEqual(sum(n * (8 - len(bits)) for bits, _, n in SUCCESSORS.values()), 69)
        self.assertFalse(any(x in SUCCESSORS for x in current))

    def test_ratifed_domain_widths(self):
        for _, (bits, name, _) in SUCCESSORS.items():
            self.assertIn(len(bits), (3, 4))
            surface = (ROOT / f"lib/domains/d{len(bits)}.lisp").read_text(encoding="utf-8")
            self.assertRegex(surface, rf"(?m)^\s*\({bits}\s+.*\(LISP {name}\)")

    def test_negative_probes(self):
        source = CURRENT.read_text(encoding="utf-8")
        reference = lex(EXACT.read_text(encoding="utf-8"))
        for mutation in (
            source.replace("(1111 left right)", "(1110 left right)"),
            source.replace("(0010 (forms)", "(0010 (form)"),
            source.replace("(0011 machine-block", "(00001001 machine-block"),
        ):
            with self.subTest(probe=mutation[-60:]):
                self.assertNotEqual(lex(mutation), reference)


if __name__ == "__main__":
    unittest.main()
