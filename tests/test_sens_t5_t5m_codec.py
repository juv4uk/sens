#!/usr/bin/env python3
"""Перевірка нового фізичного формату name.sens, не текстового файла без розширення."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sens_t5_t5m_codec import (
    SensT5Error, decode_bytes, encode_projection, encode_words,
    decode_t5m_bytes, encode_t5m_projection, parse_words, typed_sha256,
    encode_typed_domain_words,
)


class PhysicalT5CodecTests(unittest.TestCase):
    def test_canonical_packed_fixture_no_eos(self):
        physical = encode_projection("10 001 00 000 01")
        self.assertEqual(physical.hex(), "638906a1")
        self.assertEqual(decode_bytes(physical), ["10", "001", "00", "000", "01"])
        self.assertNotEqual(physical, b"10 001 00 000 01")
        self.assertNotIn(b" ", physical)
        self.assertEqual(encode_projection("10 01").hex(), "64")

    def test_default_t5m_is_one_byte_per_five_trits(self):
        self.assertEqual(encode_t5m_projection("1"), b"\xa1")
        self.assertEqual(encode_t5m_projection("00000000001"), b"\x00\x00\xa1")
        self.assertEqual(decode_t5m_bytes(b"\xa1"), ["1"])
        self.assertEqual(decode_t5m_bytes(b"\x00\x00\xa1"), ["00000000001"])

    def test_t5m_rejects_invalid_byte_and_noncanonical_padding(self):
        for data in (b"", b"\xf3", b"\xf2"):
            with self.subTest(data=data), self.assertRaises(SensT5Error):
                decode_t5m_bytes(data)

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

    def test_legacy_t5_encoder_rejects_w12_before_emitting_unreadable_bytes(self):
        word = "0" * 12
        with self.assertRaisesRegex(SensT5Error, "W1..W11"):
            parse_words(word)
        with self.assertRaisesRegex(SensT5Error, "W1..W11"):
            encode_words([word])
        with self.assertRaisesRegex(SensT5Error, "W1..W11"):
            encode_projection(word)

    def test_t5m_still_roundtrips_w12_w24_exactly(self):
        for word in ("0" * 12, "101010101010", "1" + "0" * 22 + "1"):
            with self.subTest(width=len(word), word=word):
                physical = encode_t5m_projection(word)
                self.assertEqual(decode_t5m_bytes(physical), [word])

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

    def test_2046_exact_domain_coordinates_and_256_legacy_sid8_holds(self):
        # Total capacity D1–D10 is 2046 exact addresses, not 2046
        # executable functions. D2 is syntax, D7 text; D10 runtime pending.
        admitted = [
            (f"D{width}", f"{value:0{width}b}")
            for width in range(1, 10)
            for value in range(1 << width)
        ]
        self.assertEqual(len(admitted), 1022)
        self.assertEqual(sum(len(bits) for _domain, bits in admitted), 8194)
        self.assertEqual(sum(domain == "D7" for domain, _bits in admitted), 128)
        payload = encode_typed_domain_words(admitted)
        self.assertEqual(len(payload), 1843)  # 8194 bits + 1021 trit separators
        self.assertEqual(decode_bytes(payload), [bits for _domain, bits in admitted])
        self.assertEqual(encode_words(decode_bytes(payload)), payload)

        ten_bit_holds = 0
        for value in range(1024):
            word = f"{value:010b}"
            with self.subTest(domain="D10", word=word):
                with self.assertRaisesRegex(SensT5Error, "D10_RUNTIME_HOLD"):
                    encode_typed_domain_words([("D10", word)])
            ten_bit_holds += 1
        self.assertEqual(len(admitted) + ten_bit_holds, 2046)

        # Every historical сід8 spelling is source evidence only, not a D8
        # identity. An explicit SOURCE ERA must precede migration.
        for old in range(256):
            with self.subTest(legacy=old):
                with self.assertRaisesRegex(SensT5Error, "SID8 cannot be inferred"):
                    encode_typed_domain_words([("SID8", f"{old:08b}")])

    def test_explicit_width_collision_and_corrupt_tag_fail_closed(self):
        # The same numerical value 65 in D7 text and D8 code is NOT the
        # same typed machine identity, even though both fit in a host byte.
        d7 = ("D7", "1000001")
        d8 = ("D8", "01000001")
        self.assertEqual(int(d7[1], 2), int(d8[1], 2))
        self.assertNotEqual(typed_sha256([d7[1]]), typed_sha256([d8[1]]))
        self.assertNotEqual(encode_typed_domain_words([d7]),
                            encode_typed_domain_words([d8]))
        self.assertEqual(decode_bytes(encode_typed_domain_words([d7])), [d7[1]])
        for case in (
            [("D7", "01000001")],  # forbidden implicit W8 -> W7
            [("D8", "1000001")],   # forbidden implicit W7 -> W8
            [("D7", "1")],
            [("D3", "012")],
            [("D11", "00000000000")],
            [("SID8", "00000001")],
            [("D10", "0000000000")],
        ):
            with self.subTest(case=case), self.assertRaises(SensT5Error):
                encode_typed_domain_words(case)
        with self.assertRaises(SensT5Error):
            encode_typed_domain_words([])

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
