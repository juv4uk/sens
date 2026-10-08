#!/usr/bin/env python3
"""Bounded current exact-domain ATOM to physical-T5 canary."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "migration-atom-cohort"
SOURCE = FIXTURE / "atom-empty.lisp"
PHYSICAL = FIXTURE / "atom-empty.sens"
EXPECTED = "10 010 00 000 01\n"
EXPECTED_BYTES = bytes.fromhex("643806a1")
EXPECTED_TRITS = [1,0,2,0,1,0,2,0,0,2,0,0,0,2,0,1,2,2,2,2]

class AtomT5Cohort(unittest.TestCase):
    def test_exact_projection_and_physical_bytes(self):
        self.assertEqual(SOURCE.read_text(encoding="utf-8"), EXPECTED)
        payload = PHYSICAL.read_bytes()
        self.assertEqual(payload, EXPECTED_BYTES)
        self.assertNotEqual(payload, EXPECTED.encode("ascii"))
        self.assertFalse((FIXTURE / "atom-empty").exists())

    def test_t5_bytes_are_canonical_and_typed_shape_is_preserved(self):
        trits = []
        for byte in PHYSICAL.read_bytes():
            self.assertLess(byte, 243)
            value = byte
            digits = [0] * 5
            for i in range(4, -1, -1):
                digits[i] = value % 3
                value //= 3
            trits.extend(digits)
        self.assertEqual(trits, EXPECTED_TRITS)
        self.assertEqual(trits[16:], [2,2,2,2])

if __name__ == "__main__":
    unittest.main()
