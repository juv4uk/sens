from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run import load_physical  # noqa: E402
from aggregate import build_comparison  # noqa: E402


class PhysicalInputTests(unittest.TestCase):
    def test_loads_tracked_physical_sens_bytes_and_sha(self):
        path = ROOT / "tests/fixtures/semantic/d3-selftest.sens"

        physical = load_physical(path)

        self.assertEqual(physical.path, path)
        self.assertEqual(physical.data, path.read_bytes())
        self.assertEqual(
            physical.sha256,
            "3493225aebcf8703667a7b6d13aee1ec0d5f2a4d56b60a8fadcf593a2e1e8413",
        )
        self.assertEqual(physical.sha256, hashlib.sha256(physical.data).hexdigest())

    def test_rejects_untracked_physical_file(self):
        with tempfile.TemporaryDirectory(prefix="untracked-sens-", dir=ROOT) as temp:
            path = Path(temp) / "candidate.sens"
            path.write_bytes(b"not an admitted benchmark input")

            with self.assertRaisesRegex(ValueError, "git-tracked"):
                load_physical(path)

    def test_aggregate_keeps_raw_samples_and_refuses_language_winner(self):
        reports = []
        for offset in (0, 1, 2):
            reports.append({
                "repository_head": "a" * 40, "contract_version": "11.9",
                "cpu": "test CPU", "platform": "Linux-test-x86_64-glibc2.41",
                "architecture": "x86_64", "python": "3.12",
                "rustc": "rustc test", "zig_version_pin": "0.16.0",
                "sens_cli_sha256": "b" * 64, "phase_probe_sha256": "c" * 64,
                "samples_per_process": 9, "loops_per_sample": 100,
                "warmup_samples": 2,
                "cases": {"physical": {
                    "path": "tests/fixtures/test.sens", "physical_bytes": 1,
                    "physical_sha256": "d" * 64, "expected_result": "1",
                    "parity": {"equal": True}, "word_count": 1,
                    "microcpu_slot_count": 1,
                    "native_sens": {
                        "full_decode_parse_execute": {
                            "p50": 10 + offset, "p95": 20 + offset,
                            "samples": 9, "raw_ns_per_operation": [10 + offset],
                        },
                        "warm_eval_hot": {
                            "p50": 2 + offset, "p95": 3 + offset,
                            "samples": 9, "raw_ns_per_operation": [2 + offset],
                        },
                    },
                    "python_microcpu": {
                        "full_decode_compile_execute": {
                            "p50": 30 + offset, "p95": 40 + offset,
                            "samples": 9, "raw_ns_per_operation": [30 + offset],
                        },
                        "warm_compiled_slot_replay": {
                            "p50": 5 + offset, "p95": 6 + offset,
                            "samples": 9, "raw_ns_per_operation": [5 + offset],
                        },
                    },
                }},
            })

        comparison = build_comparison(reports)

        self.assertEqual(comparison["sens"]["commit"], "a" * 40)
        self.assertEqual(comparison["environment"]["arch"], "x86_64")
        self.assertEqual(comparison["workloads"][0]["parity"], "pass")
        self.assertEqual(comparison["workloads"][0]["measurements"][0]["sens_samples"],
                         [10, 11, 12])
        self.assertEqual(comparison["verdicts"][0]["verdict"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
