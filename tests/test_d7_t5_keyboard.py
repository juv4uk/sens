"""Current D7 v2 W7 data through physical T5; no obsolete D7 phonetic rules."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from d7_symbol_codec import current_codec
from sens_t5_t5m_codec import (
    SensT5Error, decode_bytes, decode_d7_t5, encode_d7_uk_t5, encode_words,
)


class D7V2T5Tests(unittest.TestCase):
    def test_exact_t5_roundtrip_for_new_128_cell_keyboard(self):
        codec = current_codec()
        for text in ("кіт", "Привіт, друже! ім'я", "№1 ₴", "\t\n()"):
            with self.subTest(text=text):
                packed = encode_d7_uk_t5(text)
                words = list(codec.encode_text(text, "ук"))
                self.assertEqual(decode_bytes(packed), words)
                self.assertEqual(decode_d7_t5(packed), text)
                self.assertEqual(decode_d7_t5(packed, surface="en"),
                                 codec.render_text(words, "en"))
                self.assertTrue(all(len(word) == 7 for word in words))

    def test_every_v2_coordinate_is_transportable_not_reserved(self):
        words = [f"{i:07b}" for i in range(128)]
        physical = encode_words(words)
        self.assertEqual(decode_bytes(physical), words)
        self.assertEqual(decode_d7_t5(physical),
                         current_codec().render_text(words, "ук"))

    def test_d2_structural_words_do_not_turn_into_w7_text(self):
        for d2 in ("00", "01", "10", "11"):
            with self.subTest(word=d2):
                with self.assertRaisesRegex(SensT5Error, "D7_T5_WIDTH"):
                    decode_d7_t5(encode_words([d2]))

    def test_malformed_frame_or_unknown_unicode_fail_closed(self):
        with self.assertRaisesRegex(SensT5Error, "invalid T5 byte"):
            decode_d7_t5(bytes([243]))
        with self.assertRaisesRegex(SensT5Error, "D7_UK_INPUT"):
            encode_d7_uk_t5("🙂")


if __name__ == "__main__":
    unittest.main()
