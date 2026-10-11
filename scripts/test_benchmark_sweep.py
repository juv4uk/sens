#!/usr/bin/env python3
"""Unit tests for benchmark sweep verdict classification."""
import unittest

from benchmark_sweep import classify_status


class BenchmarkStatusTests(unittest.TestCase):
    def test_zero_exit_is_pass_without_block_marker(self):
        self.assertEqual(classify_status(0, "measurement complete\n"), "PASS")

    def test_nonzero_exit_is_fail_without_explicit_block_marker(self):
        self.assertEqual(classify_status(1, "unexpected assertion failure\n"), "FAIL")

    def test_named_explicit_block_is_not_mislabeled_as_failure(self):
        self.assertEqual(
            classify_status(2, "ERROR: STORE-AIR-LOAD: BLOCKED; exit=2"),
            "BLOCKED",
        )

    def test_machine_readable_block_marker(self):
        self.assertEqual(
            classify_status(2, "SENS_BENCHMARK_STATUS=BLOCKED\n"),
            "BLOCKED",
        )

    def test_ordinary_prose_mentioning_blocked_is_not_a_verdict(self):
        self.assertEqual(
            classify_status(1, "documentation describes a BLOCKED lane"),
            "FAIL",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
