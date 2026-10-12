#!/usr/bin/env python3
"""Regression tests for canonical physical T5 word projections."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as physical_run  # noqa: E402
from sens_t5_codec import decode_bytes, encode_words  # noqa: E402


class CanonicalWordProjectionTests(unittest.TestCase):
    def test_projection_preserves_exact_word_boundaries_and_terminal_lf(self) -> None:
        words = ["10", "001", "00", "000", "01"]
        payload = encode_words(words)

        projection = physical_run.canonical_word_projection(payload)

        self.assertEqual(projection, b"10 001 00 000 01\n")
        self.assertEqual(decode_bytes(payload), words)
        self.assertEqual(encode_words(projection.decode("ascii").split()), payload)

    def test_projection_is_stable_for_multiform_word_stream(self) -> None:
        words = ["10", "001", "00", "000", "01", "00", "10", "111", "00", "10", "001", "00", "000", "01"]
        payload = encode_words(words)

        projection = physical_run.canonical_word_projection(payload)

        self.assertEqual(projection, (" ".join(words) + chr(10)).encode("ascii"))
        self.assertEqual(encode_words(projection.decode("ascii").split()), payload)

    def test_empty_physical_file_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            physical_run.canonical_word_projection(b"")

    def test_invalid_t5_byte_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            physical_run.canonical_word_projection(bytes([243]))

    def test_all_padding_without_a_word_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            physical_run.canonical_word_projection(bytes([242]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
