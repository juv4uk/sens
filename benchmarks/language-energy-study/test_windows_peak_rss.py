#!/usr/bin/env python3
"""Windows peak RSS: use the real PSAPI on a hosted Windows process."""
import os
import subprocess
import sys
import unittest

from windows_peak_rss import peak_working_set_kib


class WindowsPeakRSSTests(unittest.TestCase):
    def test_bad_pids_fail_closed(self):
        for invalid in (None, 0, -1, False, True, 1.5, "123", 2**32):
            with self.subTest(pid=invalid):
                with self.assertRaises(ValueError):
                    peak_working_set_kib(invalid)

    @unittest.skipUnless(os.name == "nt", "physical Windows-only sensor")
    def test_current_pid_physical_nonzero(self):
        self.assertGreater(peak_working_set_kib(os.getpid()), 0)

    @unittest.skipUnless(os.name == "nt", "physical Windows-only sensor")
    def test_real_child_peak_working_set(self):
        # Touch each 4 KiB page to avoid a fake reservation-only allocation.
        child_code = (
            "import time\n"
            "buf=bytearray(20*1024*1024)\n"
            "for i in range(0, len(buf), 4096): buf[i]=1\n"
            "print('READY', flush=True)\n"
            "time.sleep(2)\n"
        )
        proc = subprocess.Popen(
            [sys.executable, "-c", child_code],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        try:
            self.assertEqual(proc.stdout.readline().strip(), "READY")
            rss = peak_working_set_kib(proc.pid)
            # Lower bound: resident 20 MiB buffer; this is physical RAM, not bytes reserved.
            self.assertGreater(rss, 20 * 1024)
        finally:
            proc.kill()
            proc.communicate(timeout=10)

    @unittest.skipUnless(os.name == "nt", "physical Windows-only sensor")
    def test_nonexistent_pid_fails_not_zero(self):
        # The System Idle Process cannot be queried for a normal process RSS.
        with self.assertRaises(ValueError):
            peak_working_set_kib(0)

    @unittest.skipIf(os.name == "nt", "non-Windows test")
    def test_nonwindows_does_not_forge_rss(self):
        with self.assertRaisesRegex(RuntimeError, "WINDOWS_ONLY"):
            peak_working_set_kib(os.getpid())


if __name__ == "__main__":
    unittest.main()
