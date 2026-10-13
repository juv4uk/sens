"""One home for the binary machine word and its decimal human projection."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from domain_tables import (  # noqa: E402
    human_number, is_number_width, machine_word, number_domains, number_word,
)


class BinaryProjection(unittest.TestCase):
    def test_machine_word_is_binary_of_exact_width(self):
        self.assertEqual(machine_word(5, 3), "101")
        self.assertEqual(machine_word(0, 4), "0000")
        self.assertEqual(machine_word(255, 8), "11111111")

    def test_human_number_is_only_a_projection(self):
        for number in (0, 1, 2, 7, 31, 127, 255):
            self.assertEqual(human_number(machine_word(number, 8)), number)

    def test_machine_word_fails_closed(self):
        for number, width in ((-1, 4), (8, 3), (256, 8)):
            with self.assertRaises(ValueError):
                machine_word(number, width)

    def test_human_number_rejects_non_binary(self):
        for word in ("", "012", "10a", "0b1"):
            with self.assertRaises(ValueError):
                human_number(word)


class NumericDomains(unittest.TestCase):
    def test_numbers_live_in_the_owner_ratified_ladder(self):
        self.assertEqual(
            number_domains(),
            (("D24", 24), ("D48", 48), ("D96", 96), ("D192", 192)),
        )

    def test_only_the_d24_ladder_widths_are_numeric(self):
        for width in (24, 48, 96, 192, 384):
            self.assertTrue(is_number_width(width))
        for width in (1, 7, 10, 23, 25, 100):
            self.assertFalse(is_number_width(width))

    def test_number_word_requires_an_explicit_numeric_domain(self):
        self.assertEqual(number_word(5, 24), "0" * 21 + "101")
        with self.assertRaises(ValueError):
            number_word(5, 7)


if __name__ == "__main__":
    unittest.main()
