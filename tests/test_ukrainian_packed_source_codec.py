#!/usr/bin/env python3
from __future__ import annotations

import unittest

from domain_word_carrier import CarrierError, DomainWord, MAGIC, decode, encode
from sens_source_pair_codec import decode_ukrainian, encode_ukrainian


class UkrainianPackedSourceCodecTests(unittest.TestCase):
    def test_explicit_ukrainian_quote_form_roundtrips_byte_for_byte(self):
        source = "(як-є ())".encode("utf-8")
        packed = encode_ukrainian(source)
        self.assertTrue(packed.startswith(MAGIC))
        self.assertEqual(decode_ukrainian(packed), source)

    def test_car_cons_empty_roundtrips(self):
        source = "(перше (сполучити ()))".encode("utf-8")
        packed = encode_ukrainian(source)
        self.assertEqual(decode_ukrainian(packed), source)

    def test_multiple_top_level_forms_use_canonical_single_space(self):
        source = "(сполучити ()) (як-є ())".encode("utf-8")
        packed = encode_ukrainian(source)
        self.assertEqual(decode_ukrainian(packed), source)

    def test_ascii_semantic_alias_is_not_canonical_ukrainian(self):
        with self.assertRaises(CarrierError):
            encode_ukrainian(b"(cons ())")

    def test_reader_abbreviation_is_not_canonical(self):
        with self.assertRaises(CarrierError):
            encode_ukrainian("(як-є 'x)".encode("utf-8"))

    def test_comments_are_not_canonical(self):
        with self.assertRaises(CarrierError):
            encode_ukrainian("(сполучити ()) ; comment".encode("utf-8"))

    def test_number_without_ratified_value_codec_fails_closed(self):
        with self.assertRaises(CarrierError):
            encode_ukrainian("(сполучити 2)".encode("utf-8"))

    def test_different_domain_partitions_have_distinct_packed_bytes(self):
        a = [DomainWord(1, "1"), DomainWord(2, "01")]
        b = [DomainWord(2, "10"), DomainWord(1, "1")]
        self.assertNotEqual(encode(a), encode(b))
        self.assertEqual(decode(encode(a)), a)
        self.assertEqual(decode(encode(b)), b)

    def test_corrupt_tail_fails_closed(self):
        packet = encode([DomainWord(3, "001")])
        self.assertEqual(decode(packet), [DomainWord(3, "001")])
        with self.assertRaises(CarrierError):
            decode(packet[:-1])

    def test_nonzero_padding_fails_closed(self):
        packet = bytearray(encode([DomainWord(3, "001")]))
        packet[-1] |= 1
        with self.assertRaises(CarrierError):
            decode(bytes(packet))


if __name__ == "__main__":
    unittest.main()
