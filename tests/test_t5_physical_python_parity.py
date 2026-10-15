#!/usr/bin/env python3
"""Physical T5 golden vectors: Python transport \u2194 documented Zig bridge fixtures.

Mechanical only. Does not run Zig, does not admit programs, does not judge
SENS semantics. Keeps the width=identity axiom visible: decoded word length
is the domain width; leading zeros are payload, not padding to strip.
"""
from __future__ import annotations

import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEC = ROOT / "scripts" / "sens_t5_codec.py"

# Same fixtures as scripts/test_zig_codec_bridge.py (physical layer only).
GOLDEN_T5 = bytes.fromhex("638906a1")  # QUOTE carrier from Zig F3C/T5 goldens
GOLDEN_WIDTH_VECTORS = {
    "d1_zero": "50",
    "d1_one": "a1",
    "d2_zero_zero": "1a",
    "d2_zero_one": "35",
    "d2_one_zero": "6b",
    "d2_one_one": "86",
    "d2_d3_d2_multiple_words": "663b",
    "d9_leading_zero_width": "5102",
    "d10_zero_coordinate": "0000",
}
NEGATIVE_PHYSICAL = {
    "invalid_byte_243": "f3",
    "empty": "",
    "all_padding": "f2",
    "empty_domain_word": "a2",
}


def load_codec():
    spec = importlib.util.spec_from_file_location("sens_t5_codec_parity", CODEC)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class T5PhysicalPythonParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.codec = load_codec()

    def test_quote_golden_roundtrip(self) -> None:
        words = self.codec.decode_bytes(GOLDEN_T5)
        self.assertEqual(words, ["10", "001", "00", "000", "01"])
        for word in words:
            self.assertTrue(set(word) <= {"0", "1"})
            self.assertGreaterEqual(len(word), 1)
            self.assertLessEqual(len(word), 11)
        replay = self.codec.encode_words(words)
        self.assertEqual(replay, GOLDEN_T5)
        self.assertEqual(
            hashlib.sha256(replay).hexdigest(),
            hashlib.sha256(GOLDEN_T5).hexdigest(),
        )

    def test_width_vectors_preserve_exact_bit_length(self) -> None:
        for name, hex_body in GOLDEN_WIDTH_VECTORS.items():
            with self.subTest(name=name):
                raw = bytes.fromhex(hex_body)
                words = self.codec.decode_bytes(raw)
                self.assertTrue(words, name)
                for word in words:
                    self.assertRegex(word, r"^[01]{1,11}$")
                self.assertEqual(
                    self.codec.encode_words(words),
                    raw,
                    f"{name}: non-canonical or width-stripped replay",
                )

    def test_negative_physical_rejected(self) -> None:
        for name, hex_body in NEGATIVE_PHYSICAL.items():
            with self.subTest(name=name):
                raw = bytes.fromhex(hex_body) if hex_body else b""
                with self.assertRaises(self.codec.SensT5Error):
                    self.codec.decode_bytes(raw)

    def test_d1_zero_and_one_are_distinct_identities(self) -> None:
        zero = self.codec.decode_bytes(bytes.fromhex("50"))
        one = self.codec.decode_bytes(bytes.fromhex("a1"))
        self.assertEqual(zero, ["0"])
        self.assertEqual(one, ["1"])
        self.assertNotEqual(zero, one)


if __name__ == "__main__":
    unittest.main(verbosity=2)
