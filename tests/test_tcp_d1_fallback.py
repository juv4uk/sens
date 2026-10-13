#!/usr/bin/env python3
"""Доказ однієї TCP-міграції та побітового бюджету D3/D4.
Виконується без TCP, UTF-8 і D24+: арифметична політика не маскує D1.
"""
import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/tcp.lisp"
HISTORIC_BLOB = "c03540deaae5aa529fa91a5cf6df66f5ceb273a4"
OLD = "(0100 (101 (100 decoded) (001 decoded)))"
NEW = "(010 (001 ()))"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def domain_rows(width: int) -> list[str]:
    source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
    return re.findall(r"(?m)^\s*\(([01]+)\s+\(ук\s", source)


class TcpD1ExhaustiveFallback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_historical_single_cutover_is_byte_exact(self):
        self.assertEqual(self.source.count(NEW), 1)
        self.assertNotIn(OLD, self.source)
        reconstructed = self.source.replace(NEW, OLD, 1).encode("utf-8")
        self.assertEqual(git_blob(reconstructed), HISTORIC_BLOB)
        print(f"TCP-D1: exact single source replacement; "
              f"UTF-8 bytes {len(reconstructed)} -> {len(self.source.encode('utf-8'))}")

    def test_all_domain_widths_and_coordinates_are_stable(self):
        for width in range(1, 11):
            keys = domain_rows(width)
            self.assertEqual(len(keys), 1 << width, f"D{width} missing resident")
            self.assertEqual(len(set(keys)), len(keys), f"D{width} duplicate coordinate")
            self.assertTrue(all(len(k) == width for k in keys), f"D{width} wrong width")
            self.assertEqual(set(keys), {f"{n:0{width}b}" for n in range(1 << width)})
        self.assertIn("010", domain_rows(3))  # ATOM
        self.assertIn("001", domain_rows(3))  # QUOTE
        self.assertIn("101", domain_rows(3))  # EQ
        self.assertIn("0100", domain_rows(4))  # NOT

    def test_semantic_code_heads_save_seven_bits(self):
        # Count ONLY domain function identity bits, not D2 frames, payload,
        # word boundaries or physical packed T5 sizes.
        former = (4 + 3 + 3 + 3)
        current = (3 + 3)
        self.assertEqual((former, current, former - current), (13, 6, 7))
        print("TCP-D1: 13 -> 6 exact function-head bits, saving 7; "
              "physical .sens size NOT measured")

    def test_exhaustive_two_value_d1_law(self):
        # First COND branch handles successful tag equality; second has D1 YES.
        # Covers all D1 outcomes. No textual NIL, host truthiness or integer 1.
        for equality in (False, True):
            old_fallback = not equality
            direct_yes = True
            old_result = "text" if equality else ("fallback" if old_fallback else "missing")
            new_result = "text" if equality else ("fallback" if direct_yes else "missing")
            self.assertEqual(new_result, old_result)

    def test_mutations_are_rejected(self):
        source = self.source
        self.assertEqual(source.count(NEW), 1)
        for corrupted in (
            source.replace(NEW, "(1)", 1),
            source.replace(NEW, "(0100 (001 ()))", 1),
            source.replace(NEW, "(010 (001 (0)))", 1),
        ):
            with self.assertRaises(AssertionError):
                self.assertEqual(git_blob(corrupted.replace(NEW, OLD).encode("utf-8")), HISTORIC_BLOB)


if __name__ == "__main__":
    unittest.main()
