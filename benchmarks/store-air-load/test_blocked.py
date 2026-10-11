#!/usr/bin/env python3
"""Негативні свідки: STORE→AIR→LOAD ніколи не приховує BLOCKED як вимір."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import run_text


class BlockedEvidenceTests(unittest.TestCase):
    def test_helper_exit_two_keeps_failure_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / "helper.py"
            executable.write_text(
                "import sys\n"
                "print('D3:110 admitted-control mismatch', file=sys.stderr)\n"
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError) as caught:
                run_text([sys.executable, str(executable)])
            message = str(caught.exception)
            self.assertIn("STORE-AIR-LOAD: BLOCKED", message)
            self.assertIn("exit=2", message)
            self.assertIn("D3:110 admitted-control mismatch", message)

    def test_accepted_helper_output_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / "helper.py"
            executable.write_text(
                "print('TRACE_HEX=3130')\n"
                "print('VALUE_HEX=2829')\n",
                encoding="utf-8",
            )
            self.assertEqual(
                run_text([sys.executable, str(executable)]),
                "TRACE_HEX=3130\nVALUE_HEX=2829",
            )


if __name__ == "__main__":
    unittest.main()
