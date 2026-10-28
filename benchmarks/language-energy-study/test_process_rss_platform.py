#!/usr/bin/env python3
"""#6291: real per-child peak RSS (KiB) on Linux, Darwin and Windows.

The Windows checks actually execute child processes on Windows Actions.
On Linux they are SKIPPED, not falsely reported as Windows passes.
No SENS language law is tested here; it is a physical process meter.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_study


class ProcessRssPlatform(unittest.TestCase):
    def test_linux_wait4_kib_not_redivided(self):
        with patch.object(run_study.sys, "platform", "linux"):
            self.assertEqual(run_study._unix_peak_rss_kib(22076), 22076.0)

    def test_darwin_wait4_bytes_to_kib(self):
        with patch.object(run_study.sys, "platform", "darwin"):
            self.assertEqual(run_study._unix_peak_rss_kib(22076 * 1024), 22076.0)

    def test_zero_rss_not_admitted(self):
        with patch.object(run_study.sys, "platform", "linux"):
            self.assertIsNone(run_study._unix_peak_rss_kib(0))
        with patch.object(run_study.sys, "platform", "darwin"):
            self.assertIsNone(run_study._unix_peak_rss_kib(-1))

    @unittest.skipUnless(os.name == "nt", "real Win32 process-meter requires Windows")
    def test_win32_native_peak_working_set_and_exact_stdout(self):
        cmd = f'{sys.executable} -c "print(144)"'
        ns, rss, stdout = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsInstance(ns, float)
        self.assertGreater(ns, 0)
        self.assertIsInstance(rss, float)
        self.assertGreater(rss, 0)
        self.assertLess(rss, 2 * 1024 * 1024)
        self.assertEqual(stdout, "144")

    @unittest.skipUnless(os.name == "nt", "real Win32 process-meter requires Windows")
    def test_win32_nonzero_exit_rejected(self):
        cmd = f'{sys.executable} -c "import sys;sys.exit(7)"'
        ns, rss, reason = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsNone(ns)
        self.assertIsNone(rss)
        self.assertIn("EXIT_7", reason)

    @unittest.skipUnless(os.name == "nt", "real Win32 process-meter requires Windows")
    def test_win32_multiline_rejected(self):
        cmd = f'{sys.executable} -c "print(144);print(145)"'
        ns, rss, reason = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsNone(ns)
        self.assertIsNone(rss)
        self.assertIn("BAD_STDOUT_LINES_2", reason)

    @unittest.skipUnless(os.name == "nt", "real Win32 process-meter requires Windows")
    def test_win32_timeout_is_fail_closed(self):
        cmd = f'{sys.executable} -c "import time;time.sleep(1)"'
        ns, rss, reason = run_study.run_once(cmd, os.environ.copy(), timeout_s=0.02)
        self.assertIsNone(ns)
        self.assertIsNone(rss)
        self.assertIn("TIMEOUT_", reason)


if __name__ == "__main__":
    unittest.main()
