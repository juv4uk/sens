#!/usr/bin/env python3
"""Перевірка нового фізичного формату name.sens, не текстового файла без розширення."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sens_t5_codec import (
    SensT5Error, decode_bytes, encode_projection, encode_words,
    parse_words, typed_sha256,
)


class PhysicalT5CodecTests(unittest.TestCase):
    def test_canonical_packed_fixture_no_eos(self):
        physical = encode_projection("10 001 00 000 01")
        self.assertEqual(physical.hex(), "638906a1")
        self.assertEqual(decode_bytes(physical), ["10", "001", "00", "000", "01"])
        self.assertNotEqual(physical, b"10 001 00 000 01")
        self.assertNotIn(b" ", physical)
        self.assertEqual(encode_projection("10 01").hex(), "64")

    def test_trit2_never_appears_as_text_file_or_semantic_word(self):
        for bad in ["102", "10 2 01", "(CONS x y)", "10 01 ; foo",
                    "10 FOO 01", "01010 123", ""] :
            with self.subTest(bad=bad), self.assertRaises(SensT5Error):
                encode_projection(bad)

    def test_all_d1_to_d9_widths_and_values_exact(self):
        for width in range(1, 10):
            for value in range(1 << width):
                word = f"{value:0{width}b}"
                encoded = encode_projection(word)
                self.assertEqual(decode_bytes(encoded), [word])

    def test_w10_w11_transport_preserves_exact_bits_not_semantic_admission(self):
        for width in (10, 11):
            for value in (0, 1, 1 << (width - 1), (1 << width) - 1):
                word = f"{value:0{width}b}"
                with self.subTest(width=width, word=word):
                    packed = encode_words([word])
                    self.assertEqual(decode_bytes(packed), [word])
                    self.assertEqual(encode_words(decode_bytes(packed)), packed)

    def test_malformed_separators_and_overwidth_word_have_exact_reason(self):
        def physical(trits: str) -> bytes:
            self.assertEqual(len(trits) % 5, 0)
            return bytes(int(trits[i:i + 5], 3)
                         for i in range(0, len(trits), 5))

        for label, trits, reason in (
            ("double-delimiter", "02212", "repeated separator"),
            ("leading-delimiter", "20002", "leading separator"),
            ("twelve-bits", "0" * 12 + "2" * 3, "exceeds exact W1..W11"),
        ):
            with self.subTest(label=label), self.assertRaisesRegex(SensT5Error, reason):
                decode_bytes(physical(trits))

    def test_naked_collision_has_distinct_typed_digest(self):
        lhs = ["0", "00"]
        rhs = ["000"]
        self.assertEqual("".join(lhs), "".join(rhs))
        self.assertNotEqual(typed_sha256(lhs), typed_sha256(rhs))
        self.assertNotEqual(encode_words(lhs), encode_words(rhs))
        self.assertEqual(decode_bytes(encode_words(lhs)), lhs)

    def test_noncanonical_trailer_and_impossible_byte_fail(self):
        with self.assertRaises(SensT5Error):
            decode_bytes(b"")
        with self.assertRaises(SensT5Error):
            decode_bytes(b"\xf3")
        with self.assertRaises(SensT5Error):
            decode_bytes(b"\xf2")  # 22222 is not an allowed five-trit tail.
        with self.assertRaises(SensT5Error):
            decode_bytes(bytes.fromhex("64f2"))  # obsolete EOS extra byte.
        self.assertEqual(decode_bytes(bytes.fromhex("64")), ["10", "01"])

    def test_binary_file_does_not_claim_to_translate_names(self):
        projection = "10 101 00 x 01"
        with self.assertRaisesRegex(SensT5Error, "requires exact"):
            encode_projection(projection)
        self.assertEqual(parse_words("000\n"), ["000"])

    def test_one_or_many_top_level_source_word_sequences(self):
        for text in ["1", "000", "10 01", "10 001 01",
                     "10 01 10 000 01"]:
            ws = parse_words(text)
            self.assertEqual(decode_bytes(encode_words(ws)), ws)


if __name__ == "__main__":
    unittest.main()
