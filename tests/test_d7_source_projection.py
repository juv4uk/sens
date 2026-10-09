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
                self.assertEqual(result["coordinate"], bits)
                self.assertEqual(result["width"], 7)
                self.assertEqual(result["domain"], "D7")
                self.assertEqual(result["surface"], row.en)
                self.assertEqual(result["semantic_role"], evidence[bits]["semantic_role"])
                self.assertEqual(result["status"], "OWNER-RATIFIED")
                self.assertFalse(result["callable"])
                self.assertFalse(result["arithmetic_number"])

    def test_owner_reserved_sound_coordinates_fail_closed(self) -> None:
        for bits in ("0100001", "0101010"):
            with self.subTest(bits=bits):
                with self.assertRaisesRegex(D7ProjectionError, "reserved"):
                    project(bits, role="sound-text")

    def test_local_ordinal_is_explicit_distinct_role_even_on_a_pinned_coordinate(self) -> None:
        bits = "0101010"
        ordinal = project(bits, role="local-ordinal")
        self.assertEqual(ordinal["coordinate"], bits)
        self.assertEqual(ordinal["role"], "local-ordinal")
        self.assertEqual(ordinal["status"], "ROLE-TAG-ONLY")
        self.assertIsNone(ordinal["surface"])
        self.assertFalse(ordinal["arithmetic_number"])
        self.assertFalse(ordinal["callable"])
        with self.assertRaises(D7ProjectionError):
            project(bits, role="sound-text")

    def test_text_digit_has_no_arithmetic_number_or_function_admission(self) -> None:
        one = project("0011111", role="sound-text", namespace="sym")
        self.assertEqual(one["surface"], "1")
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
