"""Platform-unit evidence checks; never assert SENS language semantics."""
import math
import unittest

from rss_units import InvalidPeakRSS, normalize_peak_rss_kib


class PeakRSSUnitsTests(unittest.TestCase):
    def test_linux_wait4_is_already_kib(self):
        self.assertEqual(normalize_peak_rss_kib(22136, "Linux"), 22136.0)

    def test_darwin_wait4_bytes_to_kib(self):
        self.assertEqual(normalize_peak_rss_kib(22667264, "Darwin"), 22136.0)

    def test_darwin_does_not_truncate_fractional_kib(self):
        self.assertEqual(normalize_peak_rss_kib(1536, "Darwin"), 1.5)

    def test_windows_does_not_fake_linux_units(self):
        with self.assertRaisesRegex(InvalidPeakRSS, "unsupported"):
            normalize_peak_rss_kib(22136, "Windows")

    def test_other_os_is_rejected(self):
        with self.assertRaises(InvalidPeakRSS):
            normalize_peak_rss_kib(22136, "FreeBSD")

    def test_zero_and_negative_are_rejected(self):
        for value in (0, -1, -0.5):
            with self.subTest(value=value), self.assertRaises(InvalidPeakRSS):
                normalize_peak_rss_kib(value, "Linux")

    def test_nan_and_infinity_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(InvalidPeakRSS):
                normalize_peak_rss_kib(value, "Darwin")

    def test_non_numeric_and_bool_are_rejected(self):
        for value in (None, True, "22136", [], {}):
            with self.subTest(value=repr(value)), self.assertRaises(InvalidPeakRSS):
                normalize_peak_rss_kib(value, "Linux")


if __name__ == "__main__":
    unittest.main()
