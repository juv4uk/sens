"""D7 v2 invariant: 128/128 keyboard data, no historical D7 v1 roles."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from d7_symbol_codec import D7CodecError, D7SymbolCodec, current_codec


class CurrentD7KeyboardTests(unittest.TestCase):
    def test_every_coordinate_roundtrips_in_three_exact_surface_tables(self):
        codec = current_codec()
        all_words = tuple(f"{index:07b}" for index in range(128))
        for surface in ("en", "ук", "san"):
            with self.subTest(surface=surface):
                text = codec.render_text(all_words, surface)
                self.assertEqual(codec.encode_text(text, surface), all_words)
                self.assertEqual(len(set(text)), 128)

    def test_current_coordinates_replace_obsolete_reserved_status(self):
        codec = current_codec()
        for bits, uk in (("0100001", "!"), ("0101010", "*"),
                         ("0100111", "'"), ("1100001", "ф")):
            self.assertEqual(codec.glyph(bits, "ук"), uk)
        self.assertEqual(codec.switch_surface("кіт", "ук", "en"), "".join(chr(int(w, 2)) for w in codec.encode_text("кіт", "ук")))

    def test_cyrillic_and_sanskrit_punctuation_are_exact_data(self):
        codec = current_codec()
        for text, surface in (
            ("Привіт, друже! ім'я ґанок Європа №1 ₴.", "ук"),
            ("संस्कृतम्", "san"), ("(quote \"text\")", "en"),
            ("\t\n()", "ук"),
        ):
            with self.subTest(surface=surface, text=text):
                self.assertEqual(codec.render_text(codec.encode_text(text, surface), surface), text)

    def test_wrong_width_unmapped_glyph_and_non_v2_surface_fail_closed(self):
        codec = current_codec()
        for word in ("1", "01000010", "xxxxxxx", " 0100001"):
            with self.assertRaises(D7CodecError):
                codec.glyph(word, "ук")
        for surface in ("slp1", "sa-slp1", "en-ipa", "iast"):
            with self.assertRaises(D7CodecError):
                codec.encode_text("test", surface)
        with self.assertRaises(D7CodecError):
            codec.encode_text("🙂", "ук")

    def test_corrupted_v2_is_rejected_without_fallback_to_v1(self):
        doc = json.loads((ROOT / "knowledge/d7-keyboard-v2-ratified.json").read_text(encoding="utf-8"))
        doc["table"][33]["bits"] = "0101010"
        with self.assertRaises(D7CodecError):
            D7SymbolCodec(doc)


if __name__ == "__main__":
    unittest.main()
