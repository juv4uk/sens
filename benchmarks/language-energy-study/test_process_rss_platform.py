#!/usr/bin/env python3
"""#6291: portable process launch and native Win32 per-child peak memory.

Win32 tests actually run on Windows Actions; POSIX check is real on POSIX.
No Python test here defines SENS semantic laws.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_study


class ProcessRssPlatform(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "POSIX-only os.wait4 subprocess smoke")
    def test_posix_real_child_preserved(self):
        cmd = f'{sys.executable} -c "print(144)"'
        ns, rss, stdout = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsInstance(ns, float)
        self.assertGreater(ns, 0)
        self.assertIsInstance(rss, float)
        self.assertGreater(rss, 0)
        self.assertEqual(stdout, "144")

    @unittest.skipUnless(os.name == "nt", "real Windows runner required")
    def test_win32_native_peak_working_set_and_exact_stdout(self):
        cmd = f'{sys.executable} -c "print(144)"'
        ns, rss, stdout = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsInstance(ns, float)
        self.assertGreater(ns, 0)
        self.assertIsInstance(rss, float)
        self.assertGreater(rss, 0)
        self.assertLess(rss, 2 * 1024 * 1024)
        self.assertEqual(stdout, "144")

    @unittest.skipUnless(os.name == "nt", "real Windows runner required")
    def test_win32_nonzero_exit_rejected(self):
        cmd = f'{sys.executable} -c "import sys;sys.exit(7)"'
        ns, rss, reason = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsNone(ns)
        self.assertIsNone(rss)
        self.assertIn("EXIT_7", reason)

    @unittest.skipUnless(os.name == "nt", "real Windows runner required")
    def test_win32_multiline_rejected(self):
        cmd = f'{sys.executable} -c "print(144);print(145)"'
        ns, rss, reason = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsNone(ns)
        self.assertIsNone(rss)
        self.assertIn("BAD_STDOUT_LINES_2", reason)

    @unittest.skipUnless(os.name == "nt", "real Windows runner required")
    def test_win32_missing_rss_rejected(self):
        cmd = f'{sys.executable} -c "print(144)"'
        with patch.object(run_study, "_windows_process_peak_rss_kib", return_value=None):
            ns, rss, reason = run_study.run_once(cmd, os.environ.copy(), timeout_s=8)
        self.assertIsNone(ns)
        self.assertIsNone(rss)
        self.assertEqual(reason, "RSS_UNAVAILABLE_WIN32")

    @unittest.skipUnless(os.name == "nt", "real Windows runner required")
    def test_win32_timeout_is_fail_closed(self):
        cmd = f'{sys.executable} -c "import time;time.sleep(1)"'
        ns, rss, reason = run_study.run_once(cmd, os.environ.copy(), timeout_s=0.02)
        self.assertIsNone(ns)
        self.assertIsNone(rss)
        self.assertIn("TIMEOUT_", reason)


if __name__ == "__main__":
    unittest.main()
