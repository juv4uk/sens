from __future__ import annotations

import sys
import unittest

from process_bench import measure_case, pair_order


class PairedProcessTests(unittest.TestCase):
    def test_pair_order_alternates_to_reduce_order_bias(self):
        self.assertEqual(pair_order(0), ("native_sens", "python_microcpu"))
        self.assertEqual(pair_order(1), ("python_microcpu", "native_sens"))
        self.assertEqual(pair_order(2), pair_order(0))

    def test_each_fresh_process_must_return_expected_value(self):
        commands = {
            "native_sens": [sys.executable, "-c", "print('1')"],
            "python_microcpu": [sys.executable, "-c", "print('1')"],
        }

        report = measure_case(commands, expected="1", reps=2, warmup=0)

        self.assertEqual(report["parity"], "pass")
        self.assertEqual(len(report["pairs"]), 2)
        for pair in report["pairs"]:
            self.assertEqual(set(pair["elapsed_ns"]), set(commands))
            self.assertTrue(all(value > 0 for value in pair["elapsed_ns"].values()))
            self.assertEqual(pair["outputs"], {"native_sens": "1", "python_microcpu": "1"})

    def test_mismatched_fresh_process_fails_before_timing(self):
        commands = {
            "native_sens": [sys.executable, "-c", "print('1')"],
            "python_microcpu": [sys.executable, "-c", "print('0')"],
        }

        with self.assertRaisesRegex(ValueError, "parity"):
            measure_case(commands, expected="1", reps=2, warmup=0)


if __name__ == "__main__":
    unittest.main()
