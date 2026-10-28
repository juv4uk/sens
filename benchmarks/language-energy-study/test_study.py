"""Physical-research instrumentation tests; no SENS language semantics."""
import importlib.util
import shutil
import subprocess
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks" / "measurement-triad"))
import verdict

SPEC = importlib.util.spec_from_file_location("study", Path(__file__).with_name("study.py"))
study = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(study)


class PhysicalStudyTests(unittest.TestCase):
    def test_corpus_observation_matches_independent_physical_bytes(self):
        data = (ROOT / "lib/core4.lisp").read_bytes()
        self.assertGreater(len(data), 512)
        for n in (1, 512, 513):
            observed = sum(data[i % len(data)] for i in range(n))
            self.assertEqual(
                study.physical_expected(n),
                f"PHYSICAL_COPY\tbytes={len(data)}\tcopies={n}\tobserved={observed}")

    def test_hierarchical_metrics_require_real_positive_evidence(self):
        evidence = {
            "schema": verdict.PHYSICAL_SCHEMA,
            "metric": "energy_uj",
            "parity": {"passed": True, "oracle_id": "physical-byte-parity"},
            "provenance": {name: "captured" for name in verdict.REQUIRED_PROVENANCE},
            "pairs": [
                {"process_id": f"block-{block}", "order": ("AB" if index % 2 == 0 else "BA"),
                 "baseline_energy_uj": 1000 + block, "candidate_energy_uj": 900 + block}
                for block in range(8) for index in range(4)
            ],
        }
        result = verdict.analyze(evidence, draws=1000, seed=1)
        self.assertEqual(result["metric"], "energy_uj")
        self.assertEqual(result["independent_processes"], 8)
        self.assertLess(result["ratio"], 1.0)
        evidence["pairs"][0]["candidate_energy_uj"] = 0
        with self.assertRaises(verdict.InvalidEvidence):
            verdict.analyze(evidence, draws=1000, seed=1)

    def test_without_exact_parity_no_numeric_verdict(self):
        evidence = {
            "schema": verdict.PHYSICAL_SCHEMA, "metric": "peak_rss_kib",
            "parity": {"passed": False, "oracle_id": "physical-byte-parity"}
        }
        result = verdict.analyze(evidence)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIsNone(result["ratio"])



class PhysicalPilotAuditTests(unittest.TestCase):
    RAPL = (
        "RUST_RAPL_PACKAGE energy_uj=50000 energy_j=0.050000 "
        "elapsed_ns=123456789 elapsed_s=0.123457 wrapped_once=false "
        "scope=whole_package_not_process "
        "counter=/sys/class/powercap/intel-rapl:0/energy_uj status=MEASURED"
    )

    def test_valid_physical_package_reading_keeps_scope_and_units(self):
        observed = study.parse_rapl_record(self.RAPL)
        self.assertEqual(observed["energy_uj"], 50000)
        self.assertEqual(observed["elapsed_ns"], 123456789)
        self.assertEqual(observed["scope"], "whole_package_not_process")
        self.assertFalse(observed["wrapped_once"])

    def test_rapl_record_fails_closed_on_invalid_hardware_evidence(self):
        cases = {
            "missing": "",
            "duplicate": self.RAPL + "\n" + self.RAPL,
            "wrong_scope": self.RAPL.replace("scope=whole_package_not_process", "scope=process"),
            "missing_scope": self.RAPL.replace("scope=whole_package_not_process ", ""),
            "missing_status": self.RAPL.replace("status=MEASURED", ""),
            "zero_energy": self.RAPL.replace("energy_uj=50000", "energy_uj=0"),
            "nonmatching_joules": self.RAPL.replace("energy_j=0.050000", "energy_j=100.000000"),
            "invalid_elapsed": self.RAPL.replace("elapsed_ns=123456789", "elapsed_ns=0"),
            "invalid_wrapped": self.RAPL.replace("wrapped_once=false", "wrapped_once=maybe"),
            "invalid_counter": self.RAPL.replace("/energy_uj", "/energy-other"),
            "duplicate_field": self.RAPL + " energy_uj=50000",
        }
        for name, payload in cases.items():
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                study.parse_rapl_record(payload)

    def fake_run(self, stdout: str, usage_line: str, returncode: int = 0):
        def run(command, **_kwargs):
            Path(command[command.index("-o") + 1]).write_text(usage_line)
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="simulated stderr")
        return run

    def test_measure_keeps_no_sensor_as_missing_energy(self):
        line = "METRIC_RSS_KIB=1012\tuser_s=0.01\tsys_s=0.00\n"
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(
            study.subprocess, "run",
            side_effect=self.fake_run(study.physical_expected(2), line),
        ):
            result = study.measure(["fake"], 2, Path(folder), None,
                                   study.physical_expected(2))
        self.assertIsNone(result["energy_uj"])
        self.assertEqual(result["peak_rss_kib"], 1012)
        self.assertEqual(result["time_boundary"], "host_wrapper_includes_subprocess")
        self.assertGreater(result["wall_time_ns"], 0)

    def test_measure_rejects_parity_interruption_and_invalid_rss(self):
        expected = study.physical_expected(2)
        line = "METRIC_RSS_KIB=1012\tuser_s=0.01\tsys_s=0.00\n"
        cases = [
            ("wrong_checksum", "PHYSICAL_COPY\tbytes=1\tcopies=2\tobserved=0", line, 0),
            ("interrupted", expected, line, -9),
            ("zero_rss", expected, "METRIC_RSS_KIB=0\tuser_s=0\tsys_s=0\n", 0),
            ("missing_rss", expected, "", 0),
        ]
        for name, output, usage, code in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                with mock.patch.object(study.subprocess, "run",
                                       side_effect=self.fake_run(output, usage, code)):
                    with self.assertRaises(RuntimeError):
                        study.measure(["fake"], 2, Path(folder), None, expected)

    def test_meter_scope_rejection_in_full_measurement_path(self):
        expected = study.physical_expected(1)
        line = "METRIC_RSS_KIB=1012\tuser_s=0.01\tsys_s=0.00\n"
        output = expected + "\n" + self.RAPL.replace(
            "scope=whole_package_not_process", "scope=process")
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(study.subprocess, "run",
                                   side_effect=self.fake_run(output, line)):
                with self.assertRaises(RuntimeError):
                    study.measure(["fake"], 1, Path(folder), Path("/fake/meter"), expected)

    def test_compiled_c_and_python_observe_equal_small_physical_copy(self):
        cc = shutil.which("cc")
        if cc is None:
            self.skipTest("C compiler unavailable")
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            corpus = directory / "bytes"
            corpus.write_bytes(bytes(range(1, 129)))
            binary = directory / "copy-c"
            subprocess.run([cc, "-std=c11", "-O2", str(Path(__file__).with_name("copy.c")),
                            "-o", str(binary)], check=True, timeout=30, capture_output=True)
            n = 8192
            expected = (f"PHYSICAL_COPY\tbytes=128\tcopies={n}\tobserved="
                        f"{sum(corpus.read_bytes()[i % 128] for i in range(n))}")
            for command in ([str(binary)], [sys.executable, str(Path(__file__).with_name("copy.py"))]):
                run = subprocess.run([*command, str(corpus), str(n)],
                                     check=True, capture_output=True, text=True, timeout=15)
                self.assertEqual(run.stdout.strip(), expected)
        # Output parity is NOT proof that a compiler executed every memcpy.




if __name__ == "__main__":
    unittest.main()
