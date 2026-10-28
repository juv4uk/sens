#!/usr/bin/env python3
"""#6291 Windows process accounting, independent of SENS semantic laws."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from win_process_meter import (run_once_windows, validate_sample,
                               peak_working_set_kib)  # noqa: E402


class WindowsProcessAccounting(unittest.TestCase):
    def test_positive_mechanics(self):
        self.assertEqual(validate_sample(123, 4200, 0, "144\n", ""),
                         (123.0, 4200.0, "144"))

    def test_zero_time_or_memory_not_admitted(self):
        for ns, rss in ((0, 1024), (123, 0), (-2, 1024), (123, -4)):
            with self.subTest(ns=ns, rss=rss):
                self.assertIsNone(validate_sample(ns, rss, 0, "144\n", "")[0])

    def test_nonzero_exit_is_rejected(self):
        result = validate_sample(1500, 500, 3, "144\n", "ERROR")
        self.assertIsNone(result[0])
        self.assertIn("EXIT_3", result[2])

    def test_empty_or_multiline_is_rejected(self):
        for output in ("", "144\n145\n", "\n"):
            with self.subTest(output=output):
                result = validate_sample(1500, 500, 0, output, "")
                self.assertIsNone(result[0])
                self.assertIn("BAD_STDOUT", result[2])

    def test_linux_never_synthesizes_win32_memory(self):
        if os.name == "nt":
            self.skipTest("Windows has a real process meter")
        self.assertEqual(run_once_windows("any", {}, 1)[2],
                         "WIN32_METER_UNAVAILABLE")
        with self.assertRaises(OSError):
            peak_working_set_kib(None)

    @unittest.skipUnless(os.name == "nt", "physical Windows process required")
    def test_actual_windows_python_peak_working_set(self):
        command = subprocess.list2cmdline(
            [sys.executable, "-c", "print(144)"])
        elapsed, peak, actual = run_once_windows(command, os.environ.copy(), 8)
        self.assertEqual(actual, "144", actual)
        self.assertGreater(elapsed, 0)
        self.assertGreater(peak, 0)

    @unittest.skipUnless(os.name == "nt", "physical Windows process required")
    def test_actual_windows_exit_and_wrong_stdout(self):
        command = subprocess.list2cmdline(
            [sys.executable, "-c", "import sys; print(145); sys.exit(5)"])
        elapsed, peak, reason = run_once_windows(command, os.environ.copy(), 8)
        self.assertIsNone(elapsed)
        self.assertIsNone(peak)
        self.assertIn("EXIT_5", reason)

    @unittest.skipUnless(os.name == "nt", "physical Windows process required")
    def test_actual_windows_timeout(self):
        command = subprocess.list2cmdline(
            [sys.executable, "-c", "import time;time.sleep(3)"])
        elapsed, peak, reason = run_once_windows(command, os.environ.copy(), 0.15)
        self.assertIsNone(elapsed)
        self.assertIsNone(peak)
        self.assertIn("TIMEOUT_", reason)


if __name__ == "__main__":
    unittest.main()
