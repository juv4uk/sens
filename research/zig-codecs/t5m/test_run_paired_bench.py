"""Fast tests for T5M benchmark reporting; no codec or language semantics."""
from __future__ import annotations

import unittest

from run_paired_bench import percentile_nearest_rank


class NearestRankPercentileTests(unittest.TestCase):
    def test_p90_uses_nearest_rank_for_fifteen_raw_samples(self) -> None:
        self.assertEqual(percentile_nearest_rank(list(range(1, 16)), 90), 14)

    def test_p90_of_five_samples_selects_the_highest_sample(self) -> None:
        self.assertEqual(percentile_nearest_rank([9.0, 1.0, 5.0, 3.0, 7.0], 90), 9.0)

    def test_empty_samples_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one sample"):
            percentile_nearest_rank([], 90)

    def test_percentile_outside_one_to_one_hundred_is_rejected(self) -> None:
        for percentile in (0, 101):
            with self.subTest(percentile=percentile):
                with self.assertRaisesRegex(ValueError, "between 1 and 100"):
                    percentile_nearest_rank([1.0, 2.0], percentile)


if __name__ == "__main__":
    unittest.main()
