"""Fail-closed D7 role/source projection, sourced only from owner #3572."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from d7_source_projection import D7ProjectionError, load_current_d7, project  # noqa: E402


class D7ProjectionTests(unittest.TestCase):
    def test_all_126_owner_ratified_rows_are_exact_and_not_callable(self) -> None:
        evidence, rows = load_current_d7()
        self.assertEqual(len(rows), 126)
        self.assertEqual(len(evidence), 128)
        for bits, row in rows.items():
            with self.subTest(bits=bits):
                result = project(bits, role="sound-text", namespace="en")
                self.assertEqual(row.bits, bits)
                self.assertEqual(evidence[bits]["status"], "OWNER-RATIFIED")
                self.assertIsNone(row.lisp)
                self.assertEqual(result["coordinate"], bits)
                self.assertEqual(result["width"], 7)
                self.assertEqual(result["domain"], "D7")
                self.assertEqual(result["surface"], row.en)
                self.assertEqual(result["symbol"], row.surface_symbols["en"])
                self.assertEqual(result["semantic_role"], evidence[bits]["semantic_role"])
                self.assertEqual(result["status"], "OWNER-RATIFIED")
                self.assertFalse(result["callable"])
                self.assertFalse(result["arithmetic_number"])

    def test_owner_reserved_sound_coordinates_fail_closed(self) -> None:
        for bits in ("0100001", "0101010"):
            with self.subTest(bits=bits):
                with self.assertRaisesRegex(D7ProjectionError, "reserved"):
                    project(bits, role="sound-text")

    def test_local_ordinal_only_for_fourteen_donor_locked_sutras(self) -> None:
        # LocalOrdinal має власну донорську підставу: W7-ширина не є допуском.
        for ordinal_number in range(1, 15):
            bits = f"{ordinal_number:07b}"
            with self.subTest(bits=bits):
                ordinal = project(bits, role="local-ordinal")
                sound = project(bits, role="sound-text")
                self.assertEqual(ordinal["coordinate"], bits)
                self.assertEqual(ordinal["role"], "local-ordinal")
                self.assertEqual(ordinal["status"], "D7-VALID-PROVENANCE")
                self.assertEqual(ordinal["donor_ref"], f"shiva-sutra:{ordinal_number}")
                self.assertEqual(ordinal["source_order"], ordinal_number)
                self.assertIsNone(ordinal["surface"])
                self.assertFalse(ordinal["arithmetic_number"])
                self.assertFalse(ordinal["callable"])
                self.assertEqual(sound["role"], "sound-text")
                self.assertNotEqual(sound["status"], ordinal["status"])

        # Навіть наявна звукова координата не породжує новий ordinal.
        # Два зарезервовані Sound/Text слова теж не стають порядковими.
        for bits in ("0000000", "0001111", "0100001", "0101010"):
            with self.subTest(unadmitted_ordinal=bits):
                with self.assertRaisesRegex(D7ProjectionError, "no donor-ratified LocalOrdinal"):
                    project(bits, role="local-ordinal")

    def test_text_digit_has_no_arithmetic_number_or_function_admission(self) -> None:
        one = project("0011111", role="sound-text", namespace="sym")
        self.assertEqual(one["surface"], "1")
        self.assertEqual(one["symbol"], "1")
        self.assertEqual(one["semantic_role"], "text-digit")
        self.assertFalse(one["arithmetic_number"])
        self.assertFalse(one["callable"])

    def test_human_surfaces_do_not_mint_independent_coordinates(self) -> None:
        english = project("0000000", role="sound-text", namespace="en")
        ukrainian = project("0000000", role="sound-text", namespace="ук")
        sanskrit = project("0000000", role="sound-text", namespace="san")
        self.assertEqual({english["coordinate"], ukrainian["coordinate"], sanskrit["coordinate"]}, {"0000000"})
        self.assertEqual(english["surface"], "varga.K.voiceless")
        self.assertEqual(ukrainian["surface"], "велярний-глухий")
        self.assertEqual(sanskrit["surface"], "ka-varga-aghoṣa")
        self.assertEqual(ukrainian["symbol"], "к")
        self.assertEqual(sanskrit["symbol"], "क")
        self.assertEqual(english["symbol"], "k")
        self.assertEqual(project("0000000", role="sound-text", namespace="укр")["symbol"], "к")

    def test_surface_specific_symbols_do_not_change_width_or_aliases(self) -> None:
        # The same exact coordinate has a different glyph by surface, not by identity.
        self.assertEqual(project("0000000", role="sound-text", namespace="ук")["coordinate"], "0000000")
        self.assertEqual(project("0000000", role="sound-text", namespace="san")["symbol"], "क")
        self.assertEqual(project("0000000", role="sound-text", namespace="en")["symbol"], "k")

        # Sanskrit has an admitted glyph for aspirated K; Ukrainian has no
        # admitted 1:1 symbol, so we do not fabricate one from the Latin form.
        aspirated_uk = project("0000001", role="sound-text", namespace="ук")
        self.assertIsNone(aspirated_uk["symbol"])
        self.assertEqual(project("0000001", role="sound-text", namespace="san")["symbol"], "ख")
        self.assertEqual(project("0000001", role="sound-text", namespace="en")["symbol"], "kh")

        # Text digit remains a D7 text glyph, not a Number, with script-specific numeral.
        self.assertEqual(project("0011111", role="sound-text", namespace="ук")["symbol"], "1")
        self.assertEqual(project("0011111", role="sound-text", namespace="en")["symbol"], "1")
        self.assertEqual(project("0011111", role="sound-text", namespace="san")["symbol"], "१")

    def test_nasal_vowels_use_surface_specific_nasalization_not_empty_universal_sym(self) -> None:
        nasal_a = "1000010"
        self.assertEqual(project(nasal_a, role="sound-text", namespace="san")["symbol"], "अँ")
        self.assertEqual(project(nasal_a, role="sound-text", namespace="en")["symbol"], "ã")
        self.assertEqual(project(nasal_a, role="sound-text", namespace="sym")["symbol"], "ã")
        self.assertIsNone(project(nasal_a, role="sound-text", namespace="ук")["symbol"])

    def test_non_glyph_and_control_symbols_are_explicit(self) -> None:
        # Control chars are represented by the normative escaped spellings on
        # script-specific surfaces; sym offers a print-safe control picture.
        self.assertEqual(project("1100001", role="sound-text", namespace="ук")["symbol"], chr(92) + "x0a")
        self.assertEqual(project("1100001", role="sound-text", namespace="sym")["symbol"], "␊")
        self.assertEqual(project("1100010", role="sound-text", namespace="en")["symbol"], chr(92) + "x09")
        self.assertEqual(project("1100010", role="sound-text", namespace="sym")["symbol"], "␉")

        # The existing ratified resident label is double-quote even though the
        # JSON projection metadata currently contains TAB for SLP1/IAST.
        self.assertEqual(project("1100101", role="sound-text", namespace="ук")["symbol"], '"')
        self.assertEqual(project("1100101", role="sound-text", namespace="en")["symbol"], '"')
        self.assertIsNone(project("1100101", role="sound-text", namespace="san")["symbol"])
        self.assertEqual(project("1100101", role="sound-text", namespace="sym")["symbol"], '"')

        # Capitalize-next-letter has no stable standalone glyph; absence is explicit.
        self.assertIsNone(project("0100010", role="sound-text", namespace="sym")["symbol"])

    def test_bare_or_malformed_width_does_not_gain_a_role(self) -> None:
        for bits in ("1", "00000000", "000000x", " 0000000", "0000000 "):
            with self.subTest(bits=bits):
                with self.assertRaisesRegex(D7ProjectionError, "exactly seven"):
                    project(bits, role="sound-text")
        for role in ("", "sound", "Number"):
            with self.subTest(role=role):
                with self.assertRaisesRegex(D7ProjectionError, "role must be explicit"):
                    project("0000000", role=role)
        with self.assertRaisesRegex(D7ProjectionError, "unsupported"):
            project("0000000", role="sound-text", namespace="invented")


if __name__ == "__main__":
    unittest.main()
