"""Regression witnesses for the draft typed D1-D9 transport experiment."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from domain_word_carrier import (DomainWord, CarrierError, MAGIC, decode, encode,
                                 display, parse_display)


class DomainWordCarrierTest(unittest.TestCase):
    def test_same_payload_different_domain_partition(self):
        a = [DomainWord(1, "1"), DomainWord(2, "01")]
        b = [DomainWord(2, "10"), DomainWord(1, "1")]
        self.assertEqual("".join(x.bits for x in a), "101")
        self.assertEqual("".join(x.bits for x in b), "101")
        self.assertNotEqual(encode(a), encode(b))
        self.assertEqual(decode(encode(a)), a)
        self.assertEqual(decode(encode(b)), b)

    def test_full_ladder_exact_domain_widths(self):
        words = [DomainWord(n, "1".zfill(n)) for n in range(1, 10)]
        self.assertEqual(decode(encode(words)), words)
        self.assertEqual(parse_display(display(words)), words)

    def test_structure_distinct_from_text(self):
        words = [DomainWord(2, "10"), DomainWord(7, "1100011"), DomainWord(2, "01")]
        self.assertEqual(decode(encode(words)), words)
        self.assertNotEqual(encode([DomainWord(2, "10")]),
                            encode([DomainWord(7, "0000010")]))

    def test_zero_suffix_and_empty(self):
        for words in ([], [DomainWord(3, "000")],
                      [DomainWord(1, "0"), DomainWord(9, "000000000")]):
            self.assertEqual(decode(encode(words)), words)
        self.assertEqual(encode([]), MAGIC + b"\0\0\0\0")

    def test_cross_byte_word_boundary(self):
        words = [DomainWord(3, "001"), DomainWord(9, "100000001")]
        self.assertEqual(decode(encode(words)), words)

    def test_reject_missing_trailing_or_corrupt_bytes(self):
        packet = encode([DomainWord(1, "1")])
        for broken in (packet[:-1], packet + b"\0",
                       packet[:-1] + bytes((packet[-1] | 1,))):
            with self.assertRaises(CarrierError):
                decode(broken)

    def test_reject_bad_descriptor(self):
        packet = bytearray(encode([DomainWord(1, "1")]))
        packet[7] = 0xF0
        with self.assertRaises(CarrierError):
            decode(bytes(packet))

    def test_reject_magic_or_bogus_count(self):
        with self.assertRaises(CarrierError):
            decode(b"hello")
        with self.assertRaises(CarrierError):
            decode(MAGIC + (1_000_001).to_bytes(4, "big"))

    def test_reject_invalid_width_payload_and_label(self):
        with self.assertRaises(CarrierError):
            DomainWord(7, "101")
        with self.assertRaises(CarrierError):
            DomainWord(10, "0" * 10)
        for token in ("101", "D03:001", "D3:0x1"):
            with self.assertRaises(CarrierError):
                parse_display(token)


if __name__ == "__main__":
    unittest.main()
