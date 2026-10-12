#!/usr/bin/env python3
"""Негативні свідки: STORE→AIR→LOAD ніколи не приховує BLOCKED як вимір."""
from __future__ import annotations

import subprocess
from contextlib import redirect_stdout
from io import StringIO
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import CURRENT_CONTRACT, SEMANTIC_GENERATION, require_current_contract, run_text


class BlockedEvidenceTests(unittest.TestCase):
    def test_current_generation_is_contract_11_9_d1_d9_subset(self):
        self.assertEqual(CURRENT_CONTRACT, "11.9")
        self.assertEqual(SEMANTIC_GENERATION, "contract-11-9-exact-d1-d9")
        require_current_contract("11.9")

    def test_stale_11_8_generation_fails_closed_as_blocked(self):
        output = StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as caught:
            require_current_contract("11.8")
        self.assertNotEqual(caught.exception.code, 0)
        self.assertIn("SENS_BENCHMARK_STATUS=BLOCKED", output.getvalue())
        self.assertIn("Contract 11.8", str(caught.exception))
        self.assertIn("Contract 11.9", str(caught.exception))

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
