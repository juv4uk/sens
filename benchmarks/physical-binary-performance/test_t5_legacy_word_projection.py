#!/usr/bin/env python3
"""Regression tests for canonical physical T5 word projections."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t5_legacy as physical_run  # noqa: E402
from sens_t5_t5m_codec import decode_bytes, encode_words  # noqa: E402


class CanonicalWordProjectionTests(unittest.TestCase):
    def test_actions_show_real_physical_process_latency_and_encoding(self) -> None:
        runtime = {
            "fixture": "tests/fixtures/example.sens", "lane": "sens-exec",
            "median_wall_ms": 2.25, "p95_wall_ms": 3.75,
            "physical_bytes": 21, "visible_to_physical_ratio": 4.0,
        }
        encoding = {
            "committed_fixture": runtime["fixture"],
            "encode_median_wall_ms": 1.5,
            "bytewise_matches_committed": True,
        }
        line = physical_run.action_notice(runtime, encoding)
        self.assertIn("::notice title=SENS physical T5", line)
        self.assertIn("execution p50=2.250 ms", line)
        self.assertIn("p95=3.750 ms", line)
        self.assertIn("encode p50=1.500 ms", line)
        self.assertIn("T5=21 B", line)
        self.assertIn("parity=PASS", line)
        with self.assertRaisesRegex(ValueError, "identical T5"):
            physical_run.action_notice(runtime, {**encoding, "bytewise_matches_committed": False})
        with self.assertRaisesRegex(ValueError, "matching"):
            physical_run.action_notice({**runtime, "lane": "sens-trit-open"}, encoding)

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
