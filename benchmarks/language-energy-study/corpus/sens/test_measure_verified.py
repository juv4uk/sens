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


class ProvenanceIdentityTests(unittest.TestCase):
    def test_linux_cpu_model_from_realistic_cpuinfo(self):
        with tempfile.TemporaryDirectory() as d:
            cpuinfo = Path(d) / "cpuinfo"
            cpuinfo.write_text(
                "processor : 0\nmodel name : AMD EPYC 7763 64-Core Processor\n"
            )
            from unittest import mock
            with mock.patch.object(meter.platform, "system", return_value="Linux"), \
                 mock.patch.object(meter.platform, "processor", return_value=""):
                value = meter.cpu_identity(cpuinfo)
            self.assertEqual(value["cpu_model"], "AMD EPYC 7763 64-Core Processor")
            self.assertEqual(value["cpu_model_source"], "/proc/cpuinfo")
            self.assertEqual(value["cpu_model_status"], "RECORDED")

    def test_missing_cpu_model_exposes_missing_metadata(self):
        from unittest import mock
        with mock.patch.object(meter.platform, "system", return_value="Linux"), \
             mock.patch.object(meter.platform, "processor", return_value=""):
            result = meter.cpu_identity(Path("/nonexistent-science-cpuinfo"))
        self.assertEqual(result["cpu_model_status"], "CPU_MODEL_NOT_RECORDED")
        self.assertIsNone(result["cpu_model"])

    def test_nonlinux_processor_fallback_is_labeled(self):
        from unittest import mock
        with mock.patch.object(meter.platform, "system", return_value="Windows"), \
             mock.patch.object(meter.platform, "processor", return_value="Intel Test CPU"):
            result = meter.cpu_identity(Path("/nonexistent-science-cpuinfo"))
        self.assertEqual(result["cpu_model"], "Intel Test CPU")
        self.assertEqual(result["cpu_model_source"], "platform.processor")

    def test_real_run_id_only_not_fictional_job_id(self):
        result = meter.github_run_identity(
            {"GITHUB_RUN_ID": "40724311685", "GITHUB_JOB": "build-sens"}
        )
        self.assertEqual(result["github_run_id"], 40724311685)
        self.assertEqual(result["github_run_id_status"], "RECORDED")
        self.assertEqual(result["github_job_label"], "build-sens")
        self.assertEqual(result["github_job_label_kind"],
                         "LOGICAL_JOB_NAME_NOT_NUMERIC_JOB_ID")

    def test_missing_or_invalid_run_id_not_fabricated(self):
        for env, status in [
            ({}, "NOT_PROVIDED"),
            ({"GITHUB_RUN_ID": "-1"}, "INVALID"),
            ({"GITHUB_RUN_ID": "bad"}, "INVALID"),
            ({"GITHUB_RUN_ID": "0"}, "INVALID"),
            ({"GITHUB_RUN_ID": "123\n456"}, "INVALID"),
        ]:
            with self.subTest(env=env):
                result = meter.github_run_identity(env)
                self.assertIsNone(result["github_run_id"])
                self.assertEqual(result["github_run_id_status"], status)


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
        self.assertIn(raw["host"]["cpu_model_status"],
                      ("RECORDED", "CPU_MODEL_NOT_RECORDED"))
        self.assertIn("github_run_id_status", raw["github_actions"])
        self.assertTrue(all(x["admitted"] for x in raw["samples"]))
        self.assertTrue(all(x["stderr_clean"] for x in raw["samples"]))
        self.assertTrue(all(len(x["stdout_sha256"]) == 64 for x in raw["samples"]))

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

    def test_noncanonical_stdout_bytes_rejected(self):
        # Even though splitlines() would accept both, native byte parity must not.
        sources = [
            "import sys, time; time.sleep(.03); sys.stdout.write('10')",
            "import sys, time; time.sleep(.03); sys.stdout.buffer.write(b'10\\r\\n')",
            "import sys, time; time.sleep(.03); sys.stdout.buffer.write(b'10\\n\\n')",
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assertEqual(self.run_fixture(source), 1)
                data = json.loads(self.output.read_text())
                self.assertEqual(data["status"], "BLOCKED_PARITY_OR_MEASUREMENT")
                self.assertFalse(data["samples"][0]["output_matches"])
                self.assertEqual(len(data["samples"]), 1)

    def test_stdout_warning_on_stderr_rejected(self):
        source = (
            "import time, sys; time.sleep(.03); "
            "print('10'); print('WARNING', file=sys.stderr)"
        )
        self.assertEqual(self.run_fixture(source), 1)
        sample = json.loads(self.output.read_text())["samples"][0]
        self.assertTrue(sample["output_matches"])
        self.assertFalse(sample["stderr_clean"])
        self.assertFalse(sample["admitted"])
        self.assertIn("WARNING", sample["stderr_excerpt"])

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
