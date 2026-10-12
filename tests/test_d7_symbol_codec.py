"""Exact D7 code↔symbol tests: genuine surface glyphs, never translated descriptions."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from d7_symbol_codec import D7CodecError, D7SymbolCodec, current_codec  # noqa: E402


class D7SymbolCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.codec = current_codec()

    def test_all_ratified_cells_remain_exact_seven_bit_sound_text_not_callables(self) -> None:
        c = self.codec
        authority = json.loads((ROOT / "knowledge/d7-ratified.json").read_text(encoding="utf-8"))
        self.assertEqual(set(c.roles), set(authority["residents"]))
        self.assertEqual(len(c.roles), 126)
        self.assertNotIn("0100001", c.roles)
        self.assertNotIn("0101010", c.roles)
        for bits in c.roles:
            self.assertRegex(bits, r"^[01]{7}$")
            self.assertEqual(c.roles[bits], authority["residents"][bits])

    def test_same_bits_glyph_depends_on_surface(self) -> None:
        bits = "0000000"
        self.assertEqual(self.codec.glyph(bits, "ук"), "к")
        self.assertEqual(self.codec.glyph(bits, "укр"), "к")
        self.assertEqual(self.codec.glyph(bits, "san"), "क")
        self.assertEqual(self.codec.glyph(bits, "en"), "k")
        self.assertEqual(self.codec.glyph(bits, "slp1"), "k")
        self.assertEqual(self.codec.encode_tokens(["क"], "san"), (bits,))
        self.assertEqual(self.codec.encode_tokens(["к"], "ук"), (bits,))

    def test_sanskrit_aspirated_is_not_fake_ukrainian_letter(self) -> None:
        code = "0000001"
        self.assertEqual(self.codec.glyph(code, "en"), "kh")
        self.assertEqual(self.codec.glyph(code, "slp1"), "K")
        self.assertEqual(self.codec.glyph(code, "san"), "ख")
        self.assertIsNone(self.codec.glyph(code, "ук"))
        with self.assertRaises(D7CodecError):
            self.codec.render_text([code], "ук")

    def test_ukrainian_and_roman_text_round_trip_without_renumbering(self) -> None:
        words = self.codec.encode_text("кіт", "ук")
        self.assertEqual(words, self.codec.encode_text("kit", "en"))
        self.assertEqual(self.codec.render_text(words, "ук"), "кіт")
        self.assertEqual(self.codec.switch_surface("кіт", "ук", "en"), "kit")
        self.assertEqual(self.codec.switch_surface("kit", "en", "ук"), "кіт")

    def test_token_boundaries_are_never_discarded(self) -> None:
        aspirated = self.codec.encode_text("kh", "en")
        self.assertEqual(aspirated, ("0000001",))
        self.assertEqual(self.codec.render_text(aspirated, "en"), "kh")
        # k + h is a DIFFERENT pair of exact D7 words; joined 'kh' is ambiguous.
        words = (self.codec.encode_tokens(["k"], "en")[0],
                 self.codec.encode_tokens(["h"], "en")[0])
        self.assertNotEqual(words, aspirated)
        self.assertEqual(self.codec.render_tokens(words, "en"), ("k", "h"))
        with self.assertRaisesRegex(D7CodecError, "ambiguous"):
            self.codec.render_text(words, "en")

    def test_digits_are_d7_text_not_numeric_semantics(self) -> None:
        bits = "0011111"
        self.assertEqual(self.codec.glyph(bits, "ук"), "1")
        self.assertEqual(self.codec.glyph(bits, "san"), "१")
        self.assertEqual(self.codec.glyph(bits, "en"), "1")
        self.assertEqual(self.codec.encode_text("१", "san"), (bits,))
        self.assertEqual(self.codec.roles[bits], "text.digit.1")

    def test_missing_nasal_glyph_does_not_erase_ratification(self) -> None:
        bits = "1000010"
        self.assertIn(bits, self.codec.roles)
        self.assertIsNone(self.codec.glyph(bits, "ук"))
        self.assertIsNone(self.codec.glyph(bits, "san"))
        with self.assertRaises(D7CodecError):
            self.codec.render_tokens([bits], "san")

    def test_owner_data_inconsistency_is_not_silently_turned_into_tab(self) -> None:
        self.assertIn("1100101", self.codec.roles)
        for layout in ("ук", "укр", "san", "en", "slp1", "sym"):
            self.assertIsNone(self.codec.glyph("1100101", layout))

    def test_reserved_or_bad_width_fail_closed(self) -> None:
        for invalid in ("0100001", "0101010", "00000000", "101", "xxxxxxx", " 0000000"):
            with self.subTest(bits=invalid):
                with self.assertRaises(D7CodecError):
                    self.codec.glyph(invalid, "ук")
        with self.assertRaises(D7CodecError):
            self.codec.glyph("0000000", "invented")
        with self.assertRaises(D7CodecError):
            self.codec.encode_text("?", "san")

    def test_incomplete_or_collisionful_donor_cannot_override_ratification(self) -> None:
        authority = json.loads((ROOT / "knowledge/d7-ratified.json").read_text(encoding="utf-8"))
        authority["residents"]["0100001"] = "invented"
        with self.assertRaises(D7CodecError):
            D7SymbolCodec(authority)


if __name__ == "__main__":
    unittest.main()
