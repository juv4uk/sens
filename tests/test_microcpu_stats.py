#!/usr/bin/env python3
"""Мінімальні негативні свідки статистики microCPU без зміни семантики."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks/microcpu"))
from bench import paired_ratio_interval


class ПарнаСтатистика(unittest.TestCase):
    def test_відтворюваний_інтервал(self):
        a = [20, 22, 18, 21, 19, 20, 23, 21, 22]
        b = [10, 11, 9, 10, 10, 11, 11, 10, 11]
        left = paired_ratio_interval(a, b, draws=1024)
        right = paired_ratio_interval(a, b, draws=1024)
        self.assertEqual(left, right)
        low, high = left["bootstrap_percentile_ci95"]
        self.assertLessEqual(low, left["ratio_of_means"])
        self.assertLessEqual(left["ratio_of_means"], high)
        self.assertGreater(low, 1)

    def test_відхилити_непарні_або_нульові_часи(self):
        with self.assertRaises(ValueError):
            paired_ratio_interval([2] * 7, [1] * 6)
        with self.assertRaises(ValueError):
            paired_ratio_interval([2] * 6, [1] * 6)
        with self.assertRaises(ValueError):
            paired_ratio_interval([2] * 7, [0] * 7)


if __name__ == "__main__":
    unittest.main()
