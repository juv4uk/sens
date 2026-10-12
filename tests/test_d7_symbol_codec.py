"""SENS D7: keyboard-only Ukrainian, Sanskrit IAST, no D2 in glyph codec."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from d7_symbol_codec import (  # noqa: E402
    CAPITAL, D2_OWNED, D7CodecError, D7SymbolCodec, UK_KEYBOARD,
    current_codec,
)


class D7SymbolCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.codec = current_codec()
        cls.authority = json.loads(
            (ROOT / "knowledge/d7-ratified.json").read_text(encoding="utf-8")
        )

    def test_exact_owner_ratified_bits_not_computed_from_glyphs(self) -> None:
        c = self.codec
        self.assertEqual(set(c.roles), set(self.authority["residents"]))
        self.assertEqual(len(c.roles), 126)
        self.assertNotIn("0100001", c.roles)
        self.assertNotIn("0101010", c.roles)
        for word in c.roles:
            self.assertRegex(word, r"^[01]{7}$")
            self.assertEqual(c.roles[word], self.authority["residents"][word])

    def test_uk_ukr_sym_are_keyboard_only_single_characters(self) -> None:
        for layout in ("ук", "укр", "sym"):
            for bits, glyph in self.codec.forward[layout].items():
                with self.subTest(layout=layout, bits=bits):
                    self.assertEqual(len(glyph), 1)
                    self.assertIn(glyph, UK_KEYBOARD)
                    self.assertEqual(self.codec.encode_tokens([glyph], layout), (bits,))
        self.assertEqual(self.codec.forward["ук"], self.codec.forward["укр"])
        self.assertEqual(self.codec.forward["ук"], self.codec.forward["sym"])

    def test_sanskrit_iast_is_not_english_and_devanagari_is_separate(self) -> None:
        bits = "0000000"
        self.assertEqual(self.codec.glyph(bits, "ук"), "к")
        self.assertEqual(self.codec.glyph(bits, "san"), "k")
        self.assertEqual(self.codec.glyph(bits, "sa-iast"), "k")
        self.assertEqual(self.codec.glyph(bits, "sa-deva"), "क")
        self.assertEqual(self.codec.glyph(bits, "sa-slp1"), "k")
        self.assertIsNone(self.codec.glyph(bits, "en"))
        self.assertEqual(self.codec.glyph("0000001", "san"), "kh")
        self.assertEqual(self.codec.glyph("0000001", "sa-slp1"), "K")
        self.assertEqual(self.codec.glyph("0000001", "sa-deva"), "ख")
        self.assertIsNone(self.codec.glyph("0000001", "ук"))

    def test_ukrainian_keyboard_roundtrip_and_uppercase(self) -> None:
        words = self.codec.encode_text("кіт", "ук")
        self.assertEqual(words, ("0000000", "1000100", "0001111"))
        self.assertEqual(self.codec.render_text(words, "ук"), "кіт")
        upper = self.codec.encode_text("Кіт", "ук")
        self.assertEqual(upper, (CAPITAL,) + words)
        self.assertEqual(self.codec.render_text(upper, "ук"), "Кіт")
        self.assertEqual(self.codec.switch_surface("кіт", "ук", "san"), "kit")
        self.assertEqual(self.codec.switch_surface("kit", "san", "ук"), "кіт")

    def test_d2_remains_structure_even_if_keys_are_physically_typable(self) -> None:
        owner_rows = self.authority["rows"]
        for row in owner_rows:
            if row.get("report_name") not in D2_OWNED:
                continue
            for layout in self.codec.forward:
                with self.subTest(role=row["report_name"], layout=layout):
                    self.assertIsNone(self.codec.glyph(row["coordinate"], layout))
        for symbol in (" ", "\n", "\t", "(", ")", "."):
            with self.subTest(symbol=repr(symbol)):
                with self.assertRaises(D7CodecError):
                    self.codec.encode_text(symbol, "ук")

    def test_sanskrit_multigraph_is_one_sanskrit_cell(self) -> None:
        asp = ("0000001",)
        self.assertEqual(self.codec.encode_text("kh", "san"), asp)
        self.assertEqual(self.codec.render_text(asp, "san"), "kh")
        self.assertEqual(self.codec.encode_text("K", "sa-slp1"), asp)

    def test_digits_are_text_cells_and_not_number_or_d2(self) -> None:
        bits = "0011111"
        self.assertEqual(self.codec.glyph(bits, "ук"), "1")
        self.assertEqual(self.codec.glyph(bits, "san"), "1")
        self.assertEqual(self.codec.glyph(bits, "sa-deva"), "१")
        self.assertEqual(self.codec.roles[bits], "text.digit.1")
        self.assertEqual(self.codec.encode_text("१", "sa-deva"), (bits,))

    def test_owner_quote_typo_is_fixed_without_minting_a_new_cell(self) -> None:
        self.assertEqual(self.codec.glyph("1100101", "ук"), '"')
        self.assertEqual(self.codec.glyph("1100101", "san"), '"')
        self.assertEqual(self.codec.encode_text('"', "ук"), ("1100101",))

    def test_keyboard_key_without_its_own_ratified_code_stays_unencoded(self) -> None:
        for glyph in ("я", "ї", "є", "ю", "щ", "№"):
            with self.subTest(glyph=glyph):
                with self.assertRaises(D7CodecError):
                    self.codec.encode_text(glyph, "ук")
        for invalid in ("@", "#", "&", "<", ">", "k", "kh"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(D7CodecError):
                    self.codec.encode_text(invalid, "ук")

    def test_unassigned_cell_or_bad_width_does_not_become_a_symbol(self) -> None:
        for invalid in ("0100001", "0101010", "00000000", "101", "xxxxxxx"):
            with self.subTest(bits=invalid):
                with self.assertRaises(D7CodecError):
                    self.codec.glyph(invalid, "ук")
        self.assertIsNone(self.codec.glyph("1000010", "san"))

    def test_modified_authority_cannot_mint_a_reserved_cell(self) -> None:
        authority = json.loads(
            (ROOT / "knowledge/d7-ratified.json").read_text(encoding="utf-8")
        )
        authority["residents"]["0100001"] = "invented"
        with self.assertRaises(D7CodecError):
            D7SymbolCodec(authority)


if __name__ == "__main__":
    unittest.main()
