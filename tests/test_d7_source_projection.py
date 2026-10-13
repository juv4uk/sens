"""D7 keyboard/v2: current 128/128 W7 text, no retired local ordinals."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from d7_source_projection import D7ProjectionError, load_current_d7, project


class D7ProjectionTests(unittest.TestCase):
    def test_all_128_keyboard_rows_are_exact_width_text_projections(self):
        evidence, rows = load_current_d7()
        self.assertEqual(len(evidence), 128)
        self.assertEqual(len(rows), 128)
        for number in range(128):
            bits = f"{number:07b}"
            with self.subTest(bits=bits):
                self.assertEqual(rows[bits].bits, bits)
                self.assertIsNone(rows[bits].lisp)
                projection = project(bits, role="text")
                self.assertEqual(projection["role"], "text")
                self.assertEqual(projection["status"], "OWNER-RATIFIED")

    def test_v1_reserved_cells_now_are_v2_text_data(self):
        for bits in ("0100001", "0101010"):
            with self.subTest(bits=bits):
                self.assertEqual(project(bits, role="text")["status"], "OWNER-RATIFIED")

    def test_keyboard_projections_share_one_exact_coordinate(self):
        bits = "1101011"
        self.assertEqual(project(bits, role="text", namespace="en")["surface"], "k")
        self.assertEqual(project(bits, role="text", namespace="ук")["surface"], "л")
        self.assertEqual(project(bits, role="text", namespace="san")["surface"], "क")
        self.assertEqual(project("0100111", role="text", namespace="ук")["surface"], "'")

    def test_digit_has_exact_seven_bit_coordinate(self):
        digit = project("0110001", role="text", namespace="en")
        self.assertEqual((digit["coordinate"], digit["width"], digit["surface"]),
                         ("0110001", 7, "1"))

    def test_retired_local_ordinal_is_not_a_current_d7_source_role(self):
        for n in range(128):
            with self.subTest(word=n):
                with self.assertRaisesRegex(D7ProjectionError, "only current D7 text"):
                    project(f"{n:07b}", role="local-ordinal")

    def test_legacy_sound_and_phonetic_namespaces_are_not_current(self):
        for role in ("", "sound-text", "sound", "Number"):
            with self.assertRaisesRegex(D7ProjectionError, "only current D7 text"):
                project("0000000", role=role)
        with self.assertRaisesRegex(D7ProjectionError, "unsupported"):
            project("0000000", role="text", namespace="slp1")

    def test_bad_width_is_blocked(self):
        for bits in ("1", "00000000", "000000x", " 0000000", "0000000 "):
            with self.assertRaisesRegex(D7ProjectionError, "exactly seven"):
                project(bits, role="text")


if __name__ == "__main__":
    unittest.main()
