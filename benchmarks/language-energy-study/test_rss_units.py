"""Integration checks for per-child RSS units in run_study.run_once()."""
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_study


class FakeChild:
    pid = 4242
    returncode = None
    stdout = StringIO("144\\n")
    stderr = StringIO("")

    def __init__(self):
        self.stdout = StringIO("144\\n")
        self.stderr = StringIO("")

    def communicate(self, timeout):
        return "144\\n", ""


class RunOnceRSSIntegrationTests(unittest.TestCase):
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
