"""Physical-research instrumentation tests; no SENS language semantics."""
import importlib.util
from pathlib import Path
import sys
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


    def test_python_c_copy_at_8192_and_reject_zero(self):
        """Real optimized C and Python byte buffers, no SENS semantics."""
        import shutil
        import subprocess
        if not shutil.which("cc"):
            self.skipTest("C_TOOLCHAIN_NOT_VERIFIED: cc unavailable")
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            corpus = folder / "synthetic.bin"
            raw = bytes((i * 37 + 5) % 256 for i in range(271))
            corpus.write_bytes(raw)
            expected = f"PHYSICAL_COPY\tbytes=271\tcopies=8192\tobserved={sum(raw[i % len(raw)] for i in range(8192))}"
            c_bin = folder / "optimized-c"
            subprocess.run(["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                            str(Path(__file__).with_name("copy.c")), "-o", str(c_bin)],
                           check=True, timeout=30)
            py = [sys.executable, str(Path(__file__).with_name("copy.py"))]
            for command in (py, [str(c_bin)]):
                good = subprocess.run([*command, str(corpus), "8192"], capture_output=True,
                                      text=True, timeout=20, check=True)
                self.assertEqual(good.stdout.strip(), expected)
                bad = subprocess.run([*command, str(corpus), "0"],
                                     capture_output=True, timeout=10)
                self.assertNotEqual(bad.returncode, 0)

    def test_rust_copy_at_8192_or_explicit_unverified(self):
        """A missing Rust compiler must remain visibly SKIPPED, not proven."""
        import shutil
        import subprocess
        if not shutil.which("rustc"):
            self.skipTest("RUST_NOT_VERIFIED: rustc unavailable")
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            corpus = folder / "synthetic.bin"
            raw = bytes((i * 37 + 5) % 256 for i in range(271))
            corpus.write_bytes(raw)
            binary = folder / "optimized-rust"
            subprocess.run(["rustc", "--edition=2021", "-O",
                            str(Path(__file__).with_name("copy.rs")), "-o", str(binary)],
                           capture_output=True, check=True, timeout=60)
            run = subprocess.run([str(binary), str(corpus), "8192"],
                                 capture_output=True, text=True, timeout=20, check=True)
            self.assertEqual(run.stdout.strip(),
                             f"PHYSICAL_COPY\tbytes=271\tcopies=8192\tobserved={sum(raw[i % len(raw)] for i in range(8192))}")

    def test_instrumentation_fail_closed_and_identical_wall_clock_scope(self):
        """Mocks test failure paths only; their timings/energy are NOT data."""
        from unittest.mock import patch
        from types import SimpleNamespace

        good = "PHYSICAL_COPY\tbytes=13\tcopies=4\tobserved=27"
        rapl = "RUST_RAPL_PACKAGE energy_uj=1500 elapsed_ns=4000 scope=whole_package_not_process counter=/sys/class/powercap/intel-rapl:0/energy_uj wrapped_once=false status=MEASURED"

        def fake_run(stdout, code=0, rss=100):
            def execute(argv, **kwargs):
                path = Path(argv[argv.index("-o") + 1])
                path.write_text(f"METRIC_RSS_KIB={rss}\tuser_s=0.01\tsys_s=0.01\n")
                return SimpleNamespace(returncode=code, stdout=stdout, stderr="")
            return execute

        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            with patch.object(study.subprocess, "run", side_effect=fake_run(good)):
                valid = study.measure(["/fake/command"], 4, out, None, good)
            self.assertGreater(valid["wall_time_ns"], 0)
            self.assertIsNone(valid["energy_uj"])
            with patch.object(study.subprocess, "run", side_effect=fake_run(good + "\n" + rapl)):
                metered = study.measure(["/fake/command"], 4, out, Path("/fake/rapl"), good)
            self.assertGreater(metered["wall_time_ns"], 0)
            self.assertEqual(metered["rapl_child_elapsed_ns"], 4000)
            self.assertEqual(metered["energy_uj"], 1500)
            self.assertEqual(metered["scope"], "whole_package_not_process")
            self.assertNotIn("host_wrapper_wall_ns", metered)
            for output, code, rss, meter in (
                (good.replace("observed=27", "observed=28"), 0, 100, None),
                (good, 137, 100, None),
                (good, 0, 0, None),
                (good + "\nUNEXPECTED", 0, 100, None),
                (good + "\n" + rapl.replace("energy_uj=1500", "energy_uj=0"), 0, 100, Path("/fake/rapl")),
                (good + "\n" + rapl.replace("elapsed_ns=4000", "elapsed_ns=0"), 0, 100, Path("/fake/rapl")),
                (good + "\n" + rapl.replace("status=MEASURED", "status=UNKNOWN"), 0, 100, Path("/fake/rapl")),
                (good + "\n" + rapl.replace("scope=whole_package_not_process", "scope=process"), 0, 100, Path("/fake/rapl")),
                (good + "\nRUST_RAPL_PACKAGE status=MEASURED scope=whole_package_not_process", 0, 100, Path("/fake/rapl")),
            ):
                with patch.object(study.subprocess, "run", side_effect=fake_run(output, code, rss)):
                    with self.assertRaises(RuntimeError):
                        study.measure(["/fake/command"], 4, out, meter, good)

    def test_total_traffic_budget_includes_every_process(self):
        """Resource bound must include 4*blocks*pairs measured + 3 warmups."""
        sample = study.validate_pilot_budget(8, 4, 64, 322314)
        self.assertEqual(sample["declared_process_launches"], 131)
        self.assertEqual(sample["declared_total_copy_bytes"], 131 * 64 * 322314)
        for args in ((8, 4, 8192, 322314), (8, 4, 64, 0),
                     (64, 30, 8192, 322314), (8, 4, 64, 65 * 1024 * 1024)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                study.validate_pilot_budget(*args)

    def test_rapl_parser_requires_unambiguous_hardware_provenance(self):
        """Valid package energy is not a synthetic TDP estimate."""
        valid = ("RUST_RAPL_PACKAGE energy_uj=1500 elapsed_ns=4000 "
                 "scope=whole_package_not_process "
                 "counter=/sys/class/powercap/intel-rapl:0/energy_uj "
                 "wrapped_once=false status=MEASURED")
        measured = study.parse_rapl_measurement([valid])
        self.assertEqual(measured["energy_uj"], 1500)
        self.assertEqual(measured["rapl_child_elapsed_ns"], 4000)
        self.assertFalse(measured["wrapped_once"])
        self.assertEqual(measured["counter"],
                         "/sys/class/powercap/intel-rapl:0/energy_uj")
        for invalid in (
            [valid, valid],
            [valid.replace("energy_uj=1500", "energy_uj=0")],
            [valid.replace("elapsed_ns=4000", "elapsed_ns=0")],
            [valid.replace("scope=whole_package_not_process", "scope=process")],
            [valid.replace("wrapped_once=false", "wrapped_once=maybe")],
            [valid.replace("status=MEASURED", "status=NOT_MEASURED")],
            [valid.replace("counter=/sys/class/powercap/intel-rapl:0/energy_uj ", "")],
            [valid.replace("counter=/sys/class/powercap/intel-rapl:0/energy_uj",
                           "counter=/sys/class/powercap/intel-rapl:0/power_uw")],
            [valid + " status=MEASURED"],
            [valid + " malformed-field"],
        ):
            with self.subTest(invalid=invalid), self.assertRaises(RuntimeError):
                study.parse_rapl_measurement(invalid)

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
