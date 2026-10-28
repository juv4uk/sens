"""Physical-research instrumentation tests; no SENS language semantics."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

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

    def test_output_parity_rejects_forged_or_extra_lines(self):
        expected = "PHYSICAL_COPY\\tbytes=4\\tcopies=8\\tobserved=10"
        self.assertIsNone(study.parse_sample_output(expected + "\\n", expected, metered=False))
        for bad in (
            expected + "\\nPHYSICAL_COPY\\tbytes=4\\tcopies=8\\tobserved=10",
            "PHYSICAL_COPY\\tbytes=4\\tcopies=7\\tobserved=10",
            expected + "\\nWARNING skipped seven copies",
            "\\n" + expected,
        ):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                study.parse_sample_output(bad, expected, metered=False)

    def test_meter_requires_exact_positive_package_observation(self):
        expected = "PHYSICAL_COPY\\tbytes=4\\tcopies=8\\tobserved=10"
        meter = ("RUST_RAPL_PACKAGE energy_uj=1234 elapsed_ns=100000000 "
                 "scope=whole_package_not_process status=MEASURED")
        got = study.parse_sample_output(expected + "\\n" + meter, expected, metered=True)
        self.assertEqual(got["energy_uj"], 1234)
        self.assertEqual(got["elapsed_ns"], 100000000)
        self.assertEqual(got["scope"], "whole_package_not_process")
        for bad in (
            meter.replace("energy_uj=1234", "energy_uj=0"),
            meter.replace("energy_uj=1234", "energy_uj=NaN"),
            meter.replace("elapsed_ns=100000000", "elapsed_ns=0"),
            meter.replace("scope=whole_package_not_process", "scope=process_only"),
            meter.replace("status=MEASURED", "status=NOT_MEASURED"),
            meter + " energy_uj=9999",
            meter.replace(" energy_uj=1234", ""),
            meter.replace(" elapsed_ns=100000000", ""),
            meter + " invalidfield",
        ):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                study.parse_sample_output(expected + "\\n" + bad, expected, metered=True)
        for stdout in (expected, expected + "\\n" + meter + "\\n" + meter,
                       meter + "\\n" + expected):
            with self.subTest(stdout=stdout), self.assertRaises(RuntimeError):
                study.parse_sample_output(stdout, expected, metered=True)

    def test_rss_requires_positive_kernel_peak_and_valid_times(self):
        actual = study.parse_resource_usage("METRIC_RSS_KIB=1200\\tuser_s=0.02\\tsys_s=0.01")
        self.assertEqual(actual["peak_rss_kib"], 1200)
        for bad in ("", "METRIC_RSS_KIB=0\\tuser_s=0\\tsys_s=0",
                    "METRIC_RSS_KIB=NaN\\tuser_s=0\\tsys_s=0",
                    "METRIC_RSS_KIB=1200\\tuser_s=nan\\tsys_s=0",
                    "METRIC_RSS_KIB=1200\\tuser_s=0\\tsys_s=0\\nEXTRA"):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                study.parse_resource_usage(bad)

    def test_interrupted_process_is_never_a_measurement(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with mock.patch.object(study.subprocess, "run",
                                   return_value=__import__("subprocess").CompletedProcess(
                                       args=["fake"], returncode=-9, stdout="", stderr="killed")):
                with self.assertRaisesRegex(RuntimeError, "execution failed: -9"):
                    study.measure(["fake"], 4, out, None,
                                  "PHYSICAL_COPY\\tbytes=4\\tcopies=4\\tobserved=10")

    def test_without_exact_parity_no_numeric_verdict(self):
        evidence = {
            "schema": verdict.PHYSICAL_SCHEMA, "metric": "peak_rss_kib",
            "parity": {"passed": False, "oracle_id": "physical-byte-parity"}
        }
        result = verdict.analyze(evidence)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIsNone(result["ratio"])


if __name__ == "__main__":
    unittest.main()
