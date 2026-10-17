from __future__ import annotations

import unittest

from aggregate_process import aggregate_reports


def report(native_samples, python_samples, *, source_hash="a" * 64):
    pairs = []
    for index, (native, python) in enumerate(zip(native_samples, python_samples)):
        pairs.append({
            "index": index,
            "order": ["native_sens", "python_microcpu"],
            "elapsed_ns": {"native_sens": native, "python_microcpu": python},
            "outputs": {"native_sens": "1", "python_microcpu": "1"},
        })
    return {
        "schema": "sens-physical-d3-paired-fresh-process-wall/v1",
        "research_status": "RESEARCH_NON_GATE",
        "repository_head": "b" * 40, "contract_version": "11.9",
        "native_sens_binary_sha256": "c" * 64,
        "python_executable_sha256": "d" * 64, "python_version": "Python test",
        "source_sha256": {"runner": source_hash},
        "cpu": "test CPU", "platform": "Linux-test", "architecture": "x86_64",
        "cpu_affinity": [0], "reps_per_workload": len(pairs), "warmup_pairs": 1,
        "tracked_worktree_status": "",
        "cases": {
            "case": {
                "physical_path": "tests/fixture.sens",
                "physical_bytes": 1, "physical_sha256": "e" * 64,
                "expected_result": "1", "parity": "pass",
                "correctness_gate_outputs": {
                    "native_sens": "1", "python_microcpu": "1",
                },
                "native_sens": {"samples_ns": native_samples},
                "python_microcpu": {"samples_ns": python_samples},
                "pairs": pairs,
            }
        },
    }


class AggregateProcessTests(unittest.TestCase):
    def test_aggregates_only_matching_raw_paired_reports(self):
        reports = [
            report(list(range(10, 25)), list(range(40, 55))),
            report(list(range(14, 29)), list(range(48, 63))),
            report(list(range(18, 33)), list(range(56, 71))),
        ]

        summary = aggregate_reports(reports, source_names=["r1", "r2", "r3"])

        case = summary["cases"]["case"]
        self.assertEqual(case["sample_pairs"], 45)
        self.assertEqual(case["native_sens"]["p50_ns"], 21)
        self.assertEqual(case["python_microcpu"]["p50_ns"], 55)
        self.assertEqual(case["per_replication"][0]["native_sens_p50_ns"], 17)
        self.assertAlmostEqual(case["per_replication"][2]["python_over_native_p50_ratio"], 63 / 25)

    def test_requires_three_independent_parent_process_reports(self):
        with self.assertRaisesRegex(ValueError, "at least three"):
            aggregate_reports([report([10], [20])], source_names=["r1"])

    def test_rejects_reports_with_different_runner_provenance(self):
        reports = [
            report(list(range(10, 25)), list(range(20, 35))),
            report(list(range(11, 26)), list(range(21, 36)), source_hash="f" * 64),
            report(list(range(12, 27)), list(range(22, 37)),),
        ]

        with self.assertRaisesRegex(ValueError, "disagree"):
            aggregate_reports(reports, source_names=["r1", "r2", "r3"])


if __name__ == "__main__":
    unittest.main()
