"""Physical-research instrumentation tests; no SENS language semantics."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

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


    def test_rapl_parser_accepts_only_physical_package_measurement(self):
        valid = ("RUST_RAPL_PACKAGE energy_uj=112 energy_j=0.000112 "
                 "elapsed_ns=765432 wrapped_once=false scope=whole_package_not_process "
                 "counter=/sys/class/powercap/intel-rapl:0/energy_uj status=MEASURED")
        measured = study.parse_rapl_measurement([valid])
        self.assertEqual(measured["energy_uj"], 112)
        self.assertEqual(measured["wall_time_ns"], 765432)
        self.assertEqual(measured["scope"], "whole_package_not_process")
        self.assertFalse(measured["rapl_wrapped_once"])
        bad = [
            [],
            [valid, valid],
            [valid.replace("MEASURED", "ENERGY_NOT_MEASURED")],
            [valid.replace("scope=whole_package_not_process", "scope=process")],
            [valid.replace("wrapped_once=false", "wrapped_once=unknown")],
            [valid.replace("/energy_uj", "/power_uw")],
            [valid.replace("energy_uj=112", "energy_uj=0")],
            [valid.replace("energy_uj=112", "energy_uj=garbage")],
            [valid.replace("elapsed_ns=765432", "elapsed_ns=0")],
            [valid.replace("elapsed_ns=765432", "elapsed_ns=nan")],
            [valid.replace("counter=/sys/class/powercap/intel-rapl:0/energy_uj ", "")],
            [valid + " status=MEASURED"],
            [valid + " malformed-field"],
        ]
        for lines in bad:
            with self.subTest(lines=lines), self.assertRaises(RuntimeError):
                study.parse_rapl_measurement(lines)

    def test_measure_refuses_mismatch_bad_rss_and_failed_process(self):
        expected = study.physical_expected(3)
        good_usage = "METRIC_RSS_KIB=2048\tuser_s=0.01\tsys_s=0.00"
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)

            def synthetic(stdout, usage=good_usage, exit_code=0):
                def fake_run(args, **_kwargs):
                    self.assertIn("/usr/bin/time", args)
                    Path(args[args.index("-o") + 1]).write_text(usage)
                    return SimpleNamespace(stdout=stdout, stderr="simulated",
                                           returncode=exit_code)
                return fake_run

            for stdout, usage, rc in [
                ("PHYSICAL_COPY\tbytes=1\tcopies=3\tobserved=1", good_usage, 0),
                (expected + "\n" + expected, good_usage, 0),
                (expected + "\nDEBUG=unexpected", good_usage, 0),
                ("noise\n" + expected, good_usage, 0),
                (expected + "\nRUST_RAPL_PACKAGE status=MEASURED", good_usage, 0),
                (expected, "METRIC_RSS_KIB=0\tuser_s=0.01\tsys_s=0", 0),
                (expected, "METRIC_RSS_KIB=nan\tuser_s=0.01\tsys_s=0", 0),
                (expected, "", 0),
                (expected, good_usage, 137),
            ]:
                with self.subTest(stdout=stdout, usage=usage, rc=rc):
                    with patch.object(study.subprocess, "run", synthetic(stdout, usage, rc)):
                        with self.assertRaises(RuntimeError):
                            study.measure(["fake-copy"], 3, out, None, expected)
            self.assertFalse(list(out.glob("*.usage")), "failed samples must clean usage files")

    def test_measure_without_rapl_never_invents_joules(self):
        expected = study.physical_expected(3)
        with tempfile.TemporaryDirectory() as directory:
            def fake_run(args, **_kwargs):
                Path(args[args.index("-o") + 1]).write_text(
                    "METRIC_RSS_KIB=2048\tuser_s=0.01\tsys_s=0.00")
                return SimpleNamespace(stdout=expected, stderr="", returncode=0)
            with patch.object(study.subprocess, "run", fake_run):
                sample = study.measure(["fake-copy"], 3, Path(directory), None, expected)
            self.assertIsNone(sample["energy_uj"])
            self.assertNotIn("scope", sample)
            self.assertGreater(sample["wall_time_ns"], 0)

    def test_measure_times_out_fail_closed(self):
        expected = study.physical_expected(3)
        with tempfile.TemporaryDirectory() as directory:
            def expire(args, **_kwargs):
                raise study.subprocess.TimeoutExpired(args, 120)
            with patch.object(study.subprocess, "run", expire):
                with self.assertRaises(study.subprocess.TimeoutExpired):
                    study.measure(["fake-copy"], 3, Path(directory), None, expected)
            self.assertFalse(list(Path(directory).glob("*.usage")))



if __name__ == "__main__":
    unittest.main()
