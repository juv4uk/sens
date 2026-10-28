#!/usr/bin/env python3
"""Only experimental measurement mechanics; no foreign oracle of SENS semantics."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("measure_verified.py")
spec = importlib.util.spec_from_file_location("sens_measure_verified", SCRIPT)
assert spec and spec.loader
meter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = meter
spec.loader.exec_module(meter)


class TimeParserTest(unittest.TestCase):
    def test_time_accepted(self):
        self.assertEqual(
            meter.parse_time("WALL_SECONDS=1.23\nMAX_RSS_KIB=400\nCHILD_EXIT=0\n"),
            {"elapsed_wall_s": 1.23, "max_rss_kib": 400, "child_exit": 0},
        )

    def test_invalid_time_and_rss(self):
        for value in [
            "WALL_SECONDS=nan\nMAX_RSS_KIB=400\nCHILD_EXIT=0",
            "WALL_SECONDS=0.00\nMAX_RSS_KIB=400\nCHILD_EXIT=0",
            "WALL_SECONDS=1.0\nMAX_RSS_KIB=0\nCHILD_EXIT=0",
            "WALL_SECONDS=1.0\nMAX_RSS_KIB=abc\nCHILD_EXIT=0",
            "WALL_SECONDS=1.0\nMAX_RSS_KIB=12\nCHILD_EXIT=0\nCHILD_EXIT=0",
            "WALL_SECONDS=1.0\nMAX_RSS_KIB=12\n",
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                meter.parse_time(value)


class NativeRunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(
            [
                "git", "-C", str(self.root), "-c", "user.name=Science",
                "-c", "user.email=science@example.invalid", "commit", "-q",
                "--allow-empty", "-m", "Fixture",
            ],
            check=True,
        )
        self.program = self.root / "program.py"
        self.output = self.root / "raw.json"

    def run_fixture(self, source: str, expected: str = "10", timeout: float = 10.0):
        self.program.write_text(source)
        return meter.main([
            "--binary", sys.executable, "--program", str(self.program),
            "--expected", expected, "--task-id", "fixture-not-SENS",
            "--repo-root", str(self.root), "--runs", "2", "--timeout-s",
            str(timeout), "--output", str(self.output),
        ])

    def test_real_subprocess_positive_and_provenance(self):
        result = self.run_fixture("import time; time.sleep(.05); print('10')")
        self.assertEqual(result, 0)
        raw = json.loads(self.output.read_text())
        self.assertEqual(raw["status"], "EXPLORATORY_OUTPUT_VERIFIED")
        self.assertEqual(raw["energy_status"], "ENERGY_NOT_MEASURED")
        self.assertIsNone(raw["energy_joules"])
        self.assertEqual(len(raw["checkout_head_sha"]), 40)
        self.assertEqual(len(raw["program_sha256"]), 64)
        self.assertTrue(all(x["admitted"] for x in raw["samples"]))

    def test_wrong_output_rejected(self):
        self.assertEqual(
            self.run_fixture("import time; time.sleep(.03); print('9')"), 1,
        )
        data = json.loads(self.output.read_text())
        self.assertFalse(data["samples"][0]["output_matches"])
        self.assertEqual(len(data["samples"]), 1)

    def test_empty_and_multiline_rejected(self):
        for source in (
            "import time; time.sleep(.03)",
            "import time; time.sleep(.03); print('10\\n10')",
        ):
            self.assertEqual(self.run_fixture(source), 1)

    def test_nonzero_exit_rejected(self):
        self.assertEqual(
            self.run_fixture(
                "import time, sys; time.sleep(.03); print('10'); sys.exit(7)"
            ), 1,
        )
        data = json.loads(self.output.read_text())
        self.assertFalse(data["samples"][0]["admitted"])

    def test_timeout_rejected(self):
        self.assertEqual(
            self.run_fixture("import time; time.sleep(.3); print('10')", timeout=.05),
            1,
        )
        self.assertEqual(
            json.loads(self.output.read_text())["samples"][0]["rejection"],
            "TIMEOUT",
        )

    def test_missing_binary_rejected(self):
        with self.assertRaises(SystemExit) as cm:
            meter.main([
                "--binary", str(self.root / "missing"),
                "--program", str(self.program),
                "--expected", "10", "--task-id", "x",
                "--repo-root", str(self.root), "--output", str(self.output),
            ])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
