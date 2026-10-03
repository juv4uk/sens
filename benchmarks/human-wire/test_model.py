#!/usr/bin/env python3
import unittest

from model import (
    bits_of,
    compare,
    duration_binary_units,
    fixed_slot_units,
    morse_hex_units,
    morse_symbol_units,
)


class HumanWireModelTests(unittest.TestCase):
    def test_morse_mark_timing(self):
        self.assertEqual(1, morse_symbol_units("E"))
        self.assertEqual(5, morse_symbol_units("A"))  # .- = 1 + gap + 3
        self.assertEqual(9, morse_symbol_units("F"))  # ..-.

    def test_hex_zero_byte_has_exact_morse_cost(self):
        # "00": each zero is ----- = 19 units; character gap = 3.
        self.assertEqual(41, morse_hex_units(b"\x00"))

    def test_binary_models_count_explicit_timing(self):
        self.assertEqual("00000000", bits_of(b"\x00"))
        self.assertEqual(15, duration_binary_units("00000000"))
        self.assertEqual(31, duration_binary_units("11111111"))
        self.assertEqual(8, fixed_slot_units("00000000"))

    def test_payload_and_frame_rates_are_separate(self):
        rows = compare(b"\x00\xff", payload_bits=8, unit_ms=60.0)
        for row in rows:
            self.assertEqual(8, row.payload_bits)
            self.assertEqual(16, row.transmitted_bits)
            self.assertGreater(row.equivalent_frame_bps, row.net_payload_bps)

    def test_invalid_payload_size_fails_closed(self):
        with self.assertRaises(ValueError):
            compare(b"\x00", payload_bits=9)


if __name__ == "__main__":
    unittest.main()
