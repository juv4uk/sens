"""Synthetic structural controls only; not physical sensor or SENS semantics tests."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_calibration import InvalidRecord, validate

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40
SHA_D = "d" * 40
OUTPUT = "e" * 64


def record():
    def run(arm):
        return {"arm": arm, "binary_sha": SHA_A if arm == "A" else SHA_B,
                "output_sha256": OUTPUT, "functional_units": 100,
                "elapsed_ns": 100_000_000, "start_uj": 1_000_000,
                "end_uj": 1_200_000, "peak_rss_bytes": 123_456,
                "exit_code": 0}
    def session(i):
        return {"id": "session-" + str(i), "recorded_at_utc": "2026-10-28T12:00:00Z",
                "cpu_temperature_c": 44.0, "read_overhead_ns": 1_000,
                "idle_control": {"start_uj": 10_000, "end_uj": 20_000,
                                 "elapsed_ns": 100_000_000},
                "blocks": [{"id": "block-1", "order": "AB", "runs": [run("A"), run("B")]},
                           {"id": "block-2", "order": "BA", "runs": [run("B"), run("A")]}]}
    return {"schema": "sens-energy-calibration/v1", "mode": "SYNTHETIC",
            "provenance": {"source_sha": SHA_C, "collector_sha": SHA_D,
                           "input_sha": SHA_C, "machine_id": "synthetic-host",
                           "cpu_model": "SYNTHETIC-CPU", "os_release": "Linux test-only",
                           "kernel": "test-only", "governor": "test-only",
                           "sensor_name": "package-0",
                           "sensor_path": "/sys/class/powercap/intel-rapl:0",
                           "energy_unit": "microjoule", "clock": "monotonic_ns",
                           "functional_unit": "synthetic byte-copy task x 100",
                           "recorded_at_utc": "2026-10-28T12:00:00Z",
                           "power_ceiling_reference": "synthetic upper bound, not hardware",
                           "documented_max_package_power_w": 75,
                           "max_energy_range_uj": 100_000_000,
                           "sensor_access_confirmed": True},
            "sessions": [session(1), session(2)]}


class CheckCalibrationTests(unittest.TestCase):
    def reject(self, variant, code):
        with self.assertRaisesRegex(InvalidRecord, code):
            validate(variant)

    def test_synthetic_balanced_structure_pass(self):
        report = validate(record())
        self.assertEqual(report["status"], "STRUCTURAL_PASS")
        self.assertEqual(report["energy"], "PHYSICAL_CALIBRATION_NOT_VERIFIED")
        self.assertEqual(report["result_parity"], "DIGEST_MATCH_ONLY")
        self.assertEqual(report["sessions"], 2)

    def test_sensor_unavailable_never_returns_joules(self):
        x = record(); x["provenance"]["sensor_access_confirmed"] = False
        self.reject(x, "ENERGY_NOT_MEASURED")

    def test_no_power_ceiling_is_not_safe(self):
        x = record(); x["provenance"]["documented_max_package_power_w"] = None
        self.reject(x, "POWER_CEILING_NOT_DOCUMENTED")

    def test_reject_dram_as_package(self):
        x = record(); x["provenance"]["sensor_name"] = "dram"
        self.reject(x, "NOT_CPU_PACKAGE_DOMAIN")

    def test_reject_malformed_package_name(self):
        x = record(); x["provenance"]["sensor_name"] = "package-"
        self.reject(x, "NOT_CPU_PACKAGE_DOMAIN")

    def test_reject_wrong_unit(self):
        x = record(); x["provenance"]["energy_unit"] = "joules"
        self.reject(x, "ENERGY_UNIT_MISMATCH")

    def test_reject_non_monotonic_clock(self):
        x = record(); x["provenance"]["clock"] = "wall_clock"
        self.reject(x, "CLOCK_NOT_MONOTONIC")

    def test_reject_ambiguous_multiple_wraps(self):
        x = record(); x["provenance"]["max_energy_range_uj"] = 1000
        self.reject(x, "COUNTER_OUT_OF_RANGE|MULTIPLE_WRAP_NOT_EXCLUDED")

    def test_reject_unsafe_duration_even_if_no_observed_wrap(self):
        x = record(); x["provenance"]["max_energy_range_uj"] = 2_000_000
        self.reject(x, "MULTIPLE_WRAP_NOT_EXCLUDED")

    def test_reject_implausible_power(self):
        x = record(); x["sessions"][0]["blocks"][0]["runs"][0]["end_uj"] = 20_000_000
        self.reject(x, "DELTA_EXCEEDS_DOCUMENTED_POWER_CEILING")

    def test_single_wrap_plausibility_accepted(self):
        x = record(); a = x["sessions"][0]["blocks"][0]["runs"][0]
        a["start_uj"], a["end_uj"] = 99_900_000, 50_000
        self.assertEqual(validate(x)["status"], "STRUCTURAL_PASS")

    def test_reject_mismatched_output(self):
        x = record(); x["sessions"][0]["blocks"][0]["runs"][0]["output_sha256"] = "f" * 64
        self.reject(x, "OUTPUT_PARITY_MISMATCH")

    def test_reject_unbalanced_ab_ba(self):
        x = record(); x["sessions"][0]["blocks"][1]["order"] = "AB"
        x["sessions"][0]["blocks"][1]["runs"].reverse()
        self.reject(x, "BALANCED_AB_BA_REQUIRED")

    def test_reject_order_mismatch(self):
        x = record(); x["sessions"][0]["blocks"][0]["runs"].reverse()
        self.reject(x, "AB_BA_ORDER_MISMATCH")

    def test_reject_different_work_units(self):
        x = record(); x["sessions"][1]["blocks"][0]["runs"][0]["functional_units"] = 101
        self.reject(x, "UNEQUAL_FUNCTIONAL_UNITS")

    def test_reject_variant_sha_drift(self):
        x = record(); x["sessions"][1]["blocks"][0]["runs"][0]["binary_sha"] = SHA_C
        self.reject(x, "BINARY_CHANGED_DURING_STUDY")

    def test_reject_bad_rss(self):
        x = record(); x["sessions"][0]["blocks"][0]["runs"][0]["peak_rss_bytes"] = None
        self.reject(x, "PEAK_RSS_NOT_RECORDED")

    def test_reject_failed_workload(self):
        x = record(); x["sessions"][0]["blocks"][0]["runs"][0]["exit_code"] = 1
        self.reject(x, "WORKLOAD_FAILED")

    def test_reject_single_session_as_independent_replications(self):
        x = record(); x["sessions"] = x["sessions"][:1]
        self.reject(x, "NOT_ENOUGH_SESSION_RECORDS")

    def test_reject_duplicate_session_ids(self):
        x = record(); x["sessions"][1]["id"] = "session-1"
        self.reject(x, "DUPLICATE_SESSION_ID")

    def test_reject_zero_energy_delta(self):
        x = record(); x["sessions"][1]["idle_control"]["end_uj"] = 10_000
        self.reject(x, "ZERO_DELTA_NOT_MEASUREMENT")

    def test_cli_sensor_unavailable_exit_2(self):
        x = record(); x["provenance"]["sensor_access_confirmed"] = False
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "raw.json"
            file.write_text(json.dumps(x), encoding="utf-8")
            result = subprocess.run([sys.executable,
                                     str(Path(__file__).with_name("check_calibration.py")), str(file)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "ENERGY_NOT_MEASURED")

    def test_boolean_counter_rejected(self):
        x = record(); x["sessions"][0]["idle_control"]["start_uj"] = True
        self.reject(x, "INVALID_COUNTER_START")

    def run_cli(self, raw_json):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "raw.json"
            file.write_text(raw_json, encoding="utf-8")
            return subprocess.run([sys.executable,
                                   str(Path(__file__).with_name("check_calibration.py")), str(file)],
                                  capture_output=True, text=True, check=False)

    def test_cli_valid_synthetic_record_remains_structural_only(self):
        result = self.run_cli(json.dumps(record()))
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(result.stdout)
        self.assertEqual(actual["status"], "STRUCTURAL_PASS")
        self.assertEqual(actual["energy"], "PHYSICAL_CALIBRATION_NOT_VERIFIED")
        self.assertNotIn("joules", actual)

    def test_cli_conflicting_duplicate_sensor_access_rejected(self):
        raw = json.dumps(record())
        self.assertEqual(raw.count('"sensor_access_confirmed": true'), 1)
        raw = raw.replace('"sensor_access_confirmed": true',
                          '"sensor_access_confirmed": false, "sensor_access_confirmed": true', 1)
        result = self.run_cli(raw)
        self.assertEqual(result.returncode, 2)
        actual = json.loads(result.stdout)
        self.assertEqual(actual["status"], "CALIBRATION_REJECTED")
        self.assertIn("DUPLICATE_JSON_KEY:sensor_access_confirmed", actual["reason"])

    def test_cli_duplicate_nested_binary_sha_rejected(self):
        raw = json.dumps(record())
        self.assertIn('"binary_sha":', raw)
        raw = raw.replace('"binary_sha":', '"binary_sha": "f" , "binary_sha":', 1)
        result = self.run_cli(raw)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DUPLICATE_JSON_KEY:binary_sha", json.loads(result.stdout)["reason"])

    def test_cli_duplicate_root_schema_rejected(self):
        raw = json.dumps(record())
        raw = raw.replace('"schema":', '"schema": "fake", "schema":', 1)
        result = self.run_cli(raw)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DUPLICATE_JSON_KEY:schema", json.loads(result.stdout)["reason"])

    def test_cli_nonfinite_number_in_uninspected_field_rejected(self):
        raw = json.dumps(record())
        raw = raw.replace('"mode": "SYNTHETIC",', '"mode": "SYNTHETIC", "uninspected": NaN,', 1)
        result = self.run_cli(raw)
        self.assertEqual(result.returncode, 2)
        self.assertIn("NONFINITE_JSON_CONSTANT:NaN", json.loads(result.stdout)["reason"])


if __name__ == "__main__":
    unittest.main()
