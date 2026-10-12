"""D7 Ukrainian physical T5: text signs have W7 identity, D2 grammar stays W2."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sens_t5_codec import (  # noqa: E402
    SensT5Error, decode_bytes, decode_d7_t5, encode_d7_uk_t5, encode_words,
)


class UkrainianD7T5Tests(unittest.TestCase):
    def test_golden_physical_five_byte_t5_exact_words(self) -> None:
        physical = encode_d7_uk_t5("кіт")
        self.assertEqual(physical, bytes.fromhex("001509a37d"))
        self.assertEqual(decode_bytes(physical), ["0000000", "1000100", "0001111"])
        self.assertEqual(decode_d7_t5(physical), "кіт")
        self.assertEqual(decode_d7_t5(physical, surface="san"), "kit")
        self.assertEqual(decode_d7_t5(physical, surface="sa-deva"), "कइत")

    def test_capital_is_existing_d7_modifier_not_an_eighth_bit(self) -> None:
        physical = encode_d7_uk_t5("Кіт")
        self.assertEqual(decode_bytes(physical),
                         ["0100010", "0000000", "1000100", "0001111"])
        self.assertEqual(decode_d7_t5(physical), "Кіт")

    def test_no_d2_word_can_be_reclassified_as_d7_symbol(self) -> None:
        for structural in ("00", "01", "10", "11"):
            with self.subTest(structural=structural):
                with self.assertRaisesRegex(SensT5Error, "D7_T5_WIDTH"):
                    decode_d7_t5(encode_words([structural]))
        for uk in ("\t", "\n", "(", ")"):
            with self.subTest(key=repr(uk)):
                with self.assertRaisesRegex(SensT5Error, "D7_UK_INPUT"):
                    encode_d7_uk_t5(uk)

    def test_owner_reserved_and_obsolete_d7_structural_signs_rejected(self) -> None:
        for word in ("0100001", "0101010", "1100001",
                     "1100010", "1100011", "1100100"):
            with self.subTest(word=word):
                with self.assertRaisesRegex(SensT5Error, "D7_T5_PROJECTION"):
                    decode_d7_t5(encode_words([word]))

    def test_text_period_and_space_are_d7_words_not_d2_control(self) -> None:
        physical = encode_d7_uk_t5("б. м")
        self.assertEqual(decode_bytes(physical),
                         ["0010110", "1111010", "1100000", "0011000"])
        self.assertEqual(decode_d7_t5(physical), "б. м")
        self.assertEqual(decode_d7_t5(physical, surface="en"), "b. m")
        self.assertEqual(decode_d7_t5(physical, surface="en-ipa"), "b. m")
        for bits, symbol in (("1100000", " "), ("1111010", ".")):
            self.assertEqual(decode_d7_t5(encode_words([bits])), symbol)

    def test_other_alphabet_does_not_become_ukrainian_keyboard(self) -> None:
        for invalid in ("@", "&", "#", "<", ">", "k", "kh", "я", "щ", "№"):
            with self.subTest(text=invalid):
                with self.assertRaisesRegex(SensT5Error, "D7_UK_INPUT"):
                    encode_d7_uk_t5(invalid)

    def test_invalid_physical_bytes_do_not_fallback_to_other_codec(self) -> None:
        with self.assertRaisesRegex(SensT5Error, "invalid T5 byte"):
            decode_d7_t5(bytes([243]))


if __name__ == "__main__":
    unittest.main()
