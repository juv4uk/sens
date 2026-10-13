"""D7 keyboard/v2: current 128/128 text projection, distinct local ordinals."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from d7_source_projection import D7ProjectionError, load_current_d7, project


class D7ProjectionTests(unittest.TestCase):
    def test_all_128_keyboard_rows_are_text_not_callable(self):
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
                self.assertFalse(projection["callable"])
                self.assertFalse(projection["arithmetic_number"])

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

    def test_text_number_is_not_arithmetic_number(self):
        digit = project("0110001", role="text", namespace="en")
        self.assertEqual(digit["surface"], "1")
        self.assertFalse(digit["arithmetic_number"])
        self.assertFalse(digit["callable"])

    def test_local_ordinal_keeps_independent_donor_provenance(self):
        for n in range(1, 15):
            ordinal = project(f"{n:07b}", role="local-ordinal")
            self.assertEqual(ordinal["source_order"], n)
            self.assertEqual(ordinal["donor_ref"], f"shiva-sutra:{n}")
            self.assertFalse(ordinal["callable"])
            self.assertFalse(ordinal["arithmetic_number"])
        for bits in ("0000000", "0100001", "0101010", "0001111"):
            with self.assertRaisesRegex(D7ProjectionError, "no donor-ratified"):
                project(bits, role="local-ordinal")

    def test_legacy_sound_and_phonetic_namespaces_are_not_current(self):
        for role in ("", "sound-text", "sound", "Number"):
            with self.assertRaisesRegex(D7ProjectionError, "role must be explicit"):
                project("0000000", role=role)
        with self.assertRaisesRegex(D7ProjectionError, "unsupported"):
            project("0000000", role="text", namespace="slp1")

    def test_bad_width_is_blocked(self):
        for bits in ("1", "00000000", "000000x", " 0000000", "0000000 "):
            with self.assertRaisesRegex(D7ProjectionError, "exactly seven"):
                project(bits, role="text")


if __name__ == "__main__":
    unittest.main()
