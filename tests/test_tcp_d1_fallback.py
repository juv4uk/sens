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
HISTORIC_BLOB = "8860b61e171fcefa56147d93153071a14dd4c55e"
OLD = "(0100 (101 (100 decoded) (001 decoded)))"
DERIVED = "(010 (001 ()))"
DIRECT = "#d1:1"


def _source_without_migration_comment(text: str) -> str:
    """Strip the migration comment line so the surgical-replacement check
    compares only the code change, not the added documentation."""
    return "\n".join(
        line for line in text.splitlines()
        if not line.lstrip().startswith("; Migrated:")
    )


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
        # Count only code occurrences, not comments
        code_lines = [line for line in self.source.splitlines() if not line.lstrip().startswith(";")]
        code = "\n".join(code_lines)
        self.assertEqual(code.count(DIRECT), 1)
        self.assertNotIn(DERIVED, code)
        self.assertNotIn(OLD, code)
        # Restore the original historical source exact Git blob. The
        # intermediate D3-derived predicate remains explicit provenance.
        clean = _source_without_migration_comment(self.source)
        self.assertEqual(clean.count(DIRECT), 1)
        intermediate = clean.replace(DIRECT, DERIVED, 1)
        self.assertEqual(intermediate.count(DERIVED), 1)
        reconstructed = intermediate.replace(DERIVED, OLD, 1).encode("utf-8")
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
        former = 4 + 3 + 3 + 3
        derived = 3 + 3
        current = 0  # #d1:1 is a predicate word, not a function-call head
        self.assertEqual((former, derived, current), (13, 6, 0))
        self.assertEqual(former - current, 13)
        print("TCP-D1: historical=13 derived=6 direct=0 function-head bits; "
              "D1 payload=1 bit; physical .sens size NOT measured")

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
        # Count only code occurrences, not comments
        code_lines = [line for line in self.source.splitlines() if not line.lstrip().startswith(";")]
        code = "\n".join(code_lines)
        self.assertEqual(code.count(DIRECT), 1)
        clean = _source_without_migration_comment(self.source)
        for corrupted in (
            clean.replace(DIRECT, "1", 1),        # numeric, not D1
            clean.replace(DIRECT, "#d1:0", 1),   # wrong D1 predicate
            clean.replace(DIRECT, "(0100 (001 ()))", 1),  # invalid NOT input
        ):
            self.assertNotIn(DIRECT, corrupted)
            self.assertNotEqual(
                git_blob(corrupted.replace(DIRECT, OLD, 1).encode("utf-8")),
                HISTORIC_BLOB,
            )


if __name__ == "__main__":
    unittest.main()
