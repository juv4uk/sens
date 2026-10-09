"""Synthetic fixtures exercise rejection and statistics; NEVER performance evidence."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("verdict", Path(__file__).with_name("verdict.py"))
verdict = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verdict)


def fixture(ratio=0.8):
    pairs = []
    for process in range(10):
        for i in range(6):
            base = 1000.0 + 4.0 * process + 2.0 * i
            pairs.append({
                "process_id": f"restart-{process}",
                "order": "AB" if i % 2 == 0 else "BA",
                "baseline_ns": base,
                "candidate_ns": base * ratio,
            })
    return {
        "schema": "sens-paired-wall-time/v1",
        "metric": "wall_time_ns",
        "parity": {"passed": True, "oracle_id": "synthetic-fixture-not-a-SENS-oracle"},
        "provenance": {key: "SYNTHETIC-DO-NOT-PUBLISH" for key in verdict.REQUIRED_PROVENANCE},
        "pairs": pairs,
    }


class VerdictTests(unittest.TestCase):
    def test_large_effect_is_detected_only_when_supported(self):
        result = verdict.analyze(fixture(0.8), draws=1000)
        self.assertEqual(result["status"], "FASTER")
        self.assertLess(result["ci95_ratio"][1], 0.99)

    def test_no_effect_does_not_claim_winner(self):
        self.assertEqual(verdict.analyze(fixture(1), draws=1000)["status"], "INCONCLUSIVE")

    def test_parity_failure_blocks_timing(self):
        sample = fixture()
        sample["parity"]["passed"] = False
        self.assertEqual(verdict.analyze(sample)["status"], "BLOCKED")

    def test_insufficient_independent_restarts_are_inconclusive(self):
        sample = fixture()
        sample["pairs"] = sample["pairs"][:12]
        self.assertEqual(verdict.analyze(sample)["status"], "INCONCLUSIVE")

    def test_order_bias_is_not_accepted(self):
        sample = fixture()
        for pair in sample["pairs"]:
            pair["order"] = "AB"
        self.assertEqual(verdict.analyze(sample)["status"], "INCONCLUSIVE")

    def test_instruction_counts_cannot_be_treated_as_latency(self):
        sample = fixture()
        sample["metric"] = "i_refs"
        with self.assertRaises(verdict.InvalidEvidence):
            verdict.analyze(sample)

    def test_missing_environment_blocks_claim(self):
        sample = fixture()
        del sample["provenance"]["cpu_model"]
        self.assertEqual(verdict.analyze(sample)["status"], "BLOCKED")

    def test_nan_or_zero_rejected(self):
        sample = fixture()
        sample["pairs"][0]["candidate_ns"] = float("nan")
        with self.assertRaises(verdict.InvalidEvidence):
            verdict.analyze(sample)


if __name__ == "__main__":
    unittest.main()
