"""Integration and boundary tests for physical per-child RSS units."""
from io import StringIO
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_study
from rss_units import InvalidPeakRSS, normalize_peak_rss_kib


class FakeChild:
    pid = 4242
    returncode = None

    def __init__(self):
        self.stdout = StringIO("144\n")
        self.stderr = StringIO("")

    def communicate(self, timeout):
        return "144\n", ""


class PeakRSSUnitsTests(unittest.TestCase):
    def test_linux_wait4_is_already_kib(self):
        self.assertEqual(normalize_peak_rss_kib(22136, "Linux"), 22136.0)

    def test_darwin_wait4_bytes_to_kib(self):
        self.assertEqual(normalize_peak_rss_kib(22667264, "Darwin"), 22136.0)

    def test_darwin_preserves_fractional_kib(self):
        self.assertEqual(normalize_peak_rss_kib(1536, "Darwin"), 1.5)

    def test_unsupported_platforms_are_rejected(self):
        for os_name in ("Windows", "FreeBSD"):
            with self.subTest(os_name=os_name), self.assertRaises(InvalidPeakRSS):
                normalize_peak_rss_kib(22136, os_name)

    def test_zero_and_negative_counters_are_rejected(self):
        for value in (0, -1, -0.5):
            with self.subTest(value=value), self.assertRaises(InvalidPeakRSS):
                normalize_peak_rss_kib(value, "Linux")

    def test_non_finite_counters_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(InvalidPeakRSS):
                normalize_peak_rss_kib(value, "Darwin")

    def test_non_numeric_and_boolean_counters_are_rejected(self):
        for value in (None, True, "22136", [], {}, 10**10000):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(InvalidPeakRSS):
                normalize_peak_rss_kib(value, "Linux")


@unittest.skipUnless(hasattr(run_study.os, "wait4"), "POSIX wait4 is unavailable")
class PosixRunOnceRSSIntegrationTests(unittest.TestCase):
    def run_posix_once(self, system_name, raw_peak):
        child = FakeChild()
        usage = SimpleNamespace(ru_maxrss=raw_peak)
        with (
            patch.object(run_study.subprocess, "Popen", return_value=child),
            patch.object(run_study.platform, "system", return_value=system_name),
            patch.object(run_study.os, "wait4", return_value=(child.pid, 0, usage)),
        ):
            return run_study.run_once("fake-command", {})

    def test_darwin_wait4_bytes_are_normalized_to_kib(self):
        elapsed, peak_kib, stdout = self.run_posix_once("Darwin", 4096)
        self.assertGreater(elapsed, 0)
        self.assertEqual(peak_kib, 4.0)
        self.assertEqual(stdout, "144")

    def test_linux_wait4_kib_are_not_scaled_twice(self):
        elapsed, peak_kib, stdout = self.run_posix_once("Linux", 4096)
        self.assertGreater(elapsed, 0)
        self.assertEqual(peak_kib, 4096.0)
        self.assertEqual(stdout, "144")

    def test_invalid_physical_peak_is_rejected(self):
        elapsed, peak_kib, reason = self.run_posix_once("Darwin", 0)
        self.assertIsNone(elapsed)
        self.assertIsNone(peak_kib)
        self.assertTrue(reason.startswith("INVALID_PER_CHILD_RSS:"))


class WindowsPSAPIPathTests(unittest.TestCase):
    def test_windows_psapi_measurement_path_remains_available(self):
        child = FakeChild()
        child.returncode = 0
        with (
            patch.object(run_study.os, "name", "nt"),
            patch.object(run_study.subprocess, "Popen", return_value=child),
            patch.object(run_study, "_windows_process_peak_rss_kib", return_value=2.5),
        ):
            elapsed, peak_kib, stdout = run_study.run_once("fake-command", {})
        self.assertGreater(elapsed, 0)
        self.assertEqual(peak_kib, 2.5)
        self.assertEqual(stdout, "144")


if __name__ == "__main__":
    unittest.main()
