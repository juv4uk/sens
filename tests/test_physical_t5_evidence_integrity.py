"""Negative-control audit for measured physical T5 reports.

These tests use the production physical benchmark's own raw measurements as
input, then deliberately corrupt the report. This is not a SENS speed claim.
"""
from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "evidence-integrity"))
sys.path.insert(0, str(ROOT / "scripts"))
import verify_physical_t5 as integrity

def load_benchmark():
    spec = importlib.util.spec_from_file_location(
        "measured_t5_transport", ROOT / "scripts" / "benchmark-sens-physical.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

BENCH = load_benchmark()
SHA = "a" * 40
FIXTURE = "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"


class PhysicalT5IntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        case = BENCH.inspect_fixture(FIXTURE, reps=3, iterations=10)
        cls.report = {
            "schema": BENCH.SCHEMA,
            "git_sha": SHA,
            "cpu": "measurement-test-machine",
            "os": "unit-test-platform",
            "python": "3",
            "timer": "perf_counter_ns",
            "lane": "CPython transport-mechanism-only; not SENS execution vs Python",
            "all_transport_preflights_passed": True,
            "fixtures": [case],
        }

    def verify(self, report):
        return integrity.verify(report, ROOT, SHA)

    def test_actual_physical_fixture_verified(self):
        result = self.verify(copy.deepcopy(self.report))
        self.assertEqual(result["verification"], "PASS_TRANSPORT_EVIDENCE_ONLY")
        self.assertFalse(result["verified_cases"][0]["native_execution_measured"])
        self.assertEqual(result["semantic_oracle"], "NOT_PROVED")

    def test_measured_fixture_sha_tampering_rejected(self):
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["physical_sha256"] = "0" * 64
        with self.assertRaisesRegex(integrity.InvalidEvidence, "physical_sha256"):
            self.verify(data)

    def test_typed_word_sha_tampering_rejected(self):
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["typed_word_sha256"] = "0" * 64
        with self.assertRaisesRegex(integrity.InvalidEvidence, "typed_word_sha256"):
            self.verify(data)

    def test_fabricated_median_rejected(self):
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["timings"]["t5_median_ns"] *= 1.5
        with self.assertRaisesRegex(integrity.InvalidEvidence, "t5 median"):
            self.verify(data)

    def test_fabricated_ratio_rejected(self):
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["timings"]["t5_over_view_time_ratio"] *= 1.5
        with self.assertRaisesRegex(integrity.InvalidEvidence, "timing ratio"):
            self.verify(data)

    def test_nan_and_infinite_sample_rejected(self):
        for wrong in (float("nan"), float("inf"), -10, True):
            data = copy.deepcopy(self.report)
            data["fixtures"][0]["timings"]["view_samples"][0] = wrong
            with self.subTest(wrong=wrong), self.assertRaises(integrity.InvalidEvidence):
                self.verify(data)

    def test_forged_native_or_oracle_achievement_rejected(self):
        for key in ("native_execution", "semantic_oracle_parity"):
            data = copy.deepcopy(self.report)
            data["fixtures"][0][key] = "PASS"
            with self.subTest(key=key), self.assertRaisesRegex(
                    integrity.InvalidEvidence, "unearned"):
                self.verify(data)

    def test_wrong_git_commit_or_duplicate_fixtures_rejected(self):
        data = copy.deepcopy(self.report)
        data["git_sha"] = "b" * 40
        with self.assertRaisesRegex(integrity.InvalidEvidence, "another commit"):
            self.verify(data)
        data = copy.deepcopy(self.report)
        data["fixtures"].append(copy.deepcopy(data["fixtures"][0]))
        with self.assertRaisesRegex(integrity.InvalidEvidence, "duplicate"):
            self.verify(data)

    def test_path_traversal_and_boolean_counts_rejected(self):
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["fixture"] = "../outside.sens"
        with self.assertRaisesRegex(integrity.InvalidEvidence, "unsafe"):
            self.verify(data)
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["timings"]["repetitions"] = True
        with self.assertRaisesRegex(integrity.InvalidEvidence, "expected integer"):
            self.verify(data)

    def test_counted_bits_and_raw_samples_required(self):
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["semantic_bit_count"] += 1
        with self.assertRaisesRegex(integrity.InvalidEvidence, "semantic_bit_count"):
            self.verify(data)
        data = copy.deepcopy(self.report)
        data["fixtures"][0]["timings"]["view_samples"].pop()
        with self.assertRaisesRegex(integrity.InvalidEvidence, "sample count"):
            self.verify(data)


if __name__ == "__main__":
    unittest.main()
