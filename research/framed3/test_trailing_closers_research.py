"""Вичерпні короткі корпуси D2, усі W1–W9, негативні випадки та EOF."""
from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trailing_closers_research as suffix


class SuffixLaw(unittest.TestCase):
    def test_all_ratified_payload_widths(self):
        for width in (1, 3, 4, 5, 6, 7, 8, 9):
            for value in set((0, 1, (1 << width) - 2, (1 << width) - 1)):
                word = format(value, f"0{width}b")
                for words in (
                    ("10", word, "01"),
                    ("10", "10", word, "01", "01"),
                    (word, "10", word, "01"),
                    ("10", "001", word, "01"),
                    ("10", "0", "11", word, "01"),
                ):
                    with self.subTest(width=width, word=word, words=words):
                        short = suffix.trim(words)
                        self.assertEqual(suffix.restore(short), words)

    def test_exact_d2_separator_and_dot_not_transport_trit(self):
        for words in (
            ("10", "00", "01"),
            ("10", "0", "00", "01"),
            ("10", "0", "11", "1", "01"),
            ("10", "0", "11", "10", "1", "01", "01"),
            ("10", "0", "11", "10", "1", "00", "01", "01"),
            ("10", "0", "01", "10", "1", "01"),
            ("10", "1", "01", "00"),
            ("001", "10", "000", "01"),
            ("000",),
            ("00",),
            ("01", "000"),  # invalid, kept only for rejection below
        ):
            if words[0] == "01":
                with self.assertRaises(suffix.SuffixError):
                    suffix.validate(words)
            else:
                self.assertEqual(suffix.restore(suffix.trim(words)), words)

    def test_depth_and_exact_physical_trits(self):
        for depth in (1, 2, 3, 4, 16, 120):
            words = ("10",) * depth + ("000000000",) + ("01",) * depth
            short = suffix.trim(words)
            self.assertEqual(short, ("10",) * depth + ("000000000",))
            self.assertEqual(suffix.restore(short), words)
            report = suffix.measure(words)
            self.assertEqual(report["closes_removed"], depth)
            self.assertEqual(report["trits_saved"], 3 * depth)
            self.assertGreaterEqual(report["hypothetical_t5_bytes_before"],
                                    report["hypothetical_t5_bytes_after"])

    def test_exhaustive_all_short_word_sequences(self):
        # W2:00/01/10/11 plus D1/D3/D7/D9; no width inference.
        choices = ("0", "1", "00", "01", "10", "11",
                   "000", "001", "0000000", "000000000")
        valid, compressed = 0, 0
        for length in range(1, 5):
            for words in product(choices, repeat=length):
                try:
                    suffix.validate(words)
                except suffix.SuffixError:
                    continue
                valid += 1
                short = suffix.trim(words)
                self.assertEqual(suffix.restore(short), words)
                compressed += len(short) < len(words)
        self.assertGreater(valid, 500)
        self.assertGreater(compressed, 200)

    def test_strict_negative_and_future_d10(self):
        for words in (
            (), ("01",), ("10", "01", "01"),
            ("10", "11", "1", "01"),
            ("10", "0", "11", "01"),
            ("10", "0", "11", "0", "1", "01"),
            ("10", "01", "10"),
            ("10", "2", "01"),
            ("10", "", "01"),
            ("10", "0" * 10, "01"),
        ):
            with self.subTest(words=words):
                with self.assertRaises(suffix.SuffixError):
                    suffix.trim(words)
        for short in (
            (), ("01",), ("10", "11"), ("10", "0", "11"),
            ("10", "1", "01"),  # noncanonical suffix still present
            ("10", "0000000000"),  # W10/D10 unratified
        ):
            with self.subTest(short=short):
                with self.assertRaises(suffix.SuffixError):
                    suffix.restore(short)

    def test_word_boundary_and_silent_truncation_counterexample(self):
        inner = ("10",)
        nested = ("10", "10")
        self.assertEqual(suffix.restore(inner), ("10", "01"))
        self.assertEqual(suffix.restore(nested),
                         ("10", "10", "01", "01"))
        self.assertEqual(nested[:1], inner)
        # A truncated compressed valid program is ANOTHER valid program.
        self.assertNotEqual(suffix.restore(nested[:1]), suffix.restore(nested))
        # Therefore physical EOF alone cannot validate message integrity.

    def test_no_end_closes_leaves_complete_program_unchanged(self):
        for words in (("1",), ("001",), ("10", "01", "000"),
                      ("10", "01", "00"), ("00",)):
            self.assertEqual(suffix.trim(words), words)
            self.assertEqual(suffix.restore(words), words)
            self.assertEqual(suffix.measure(words)["trits_saved"], 0)


if __name__ == "__main__":
    unittest.main()
