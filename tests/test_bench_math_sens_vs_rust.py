#!/usr/bin/env python3
"""Controls for the paired SENS-vs-Rust math benchmark harness."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from unittest import mock
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "bench_math_sens_vs_rust.py"


def load():
    spec = importlib.util.spec_from_file_location("sens_math_bench", CHECKER)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


class MathBenchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.m = load()

    def test_rational_canonical_law(self) -> None:
        Q = self.m.Q
        self.assertEqual((Q(2, 4).n, Q(2, 4).d), (1, 2))          # gcd-reduced
        self.assertEqual((Q(1, -2).n, Q(1, -2).d), (-1, 2))       # sign on numerator
        self.assertEqual((Q(1, 2).add(Q(1, 3)).n, Q(1, 2).add(Q(1, 3)).d), (5, 6))
        self.assertEqual((Q(2, 3).mul(Q(3, 4)).n, Q(2, 3).mul(Q(3, 4)).d), (1, 2))
        self.assertEqual((Q(3, 4).recip().n, Q(3, 4).recip().d), (4, 3))

    def test_recip_of_zero_raises(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            self.m.Q(0, 1).recip()

    def test_workload_is_deterministic(self) -> None:
        c1, ops1 = self.m.workload_python(1000)
        c2, ops2 = self.m.workload_python(1000)
        self.assertEqual((c1, ops1), (c2, ops2))
        self.assertEqual(ops1, 3000)

    def test_unavailable_side_is_unverified_not_fake(self) -> None:
        rust = self.m.measure_rust(Path("/nonexistent-root"), 10)
        sens = self.m.measure_sens(Path("/nonexistent-root"), 10)
        self.assertEqual(rust["status"], "UNVERIFIED")
        self.assertEqual(sens["status"], "UNVERIFIED")
        self.assertNotIn("median_s", rust)   # no fabricated number


    def test_research_generator_is_never_a_paired_timing_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generator = root / "target/release/core-math-demand-rust"
            generator.parent.mkdir(parents=True)
            generator.write_bytes(b"research-generator-not-a-benchmark")
            result = self.m.measure_rust(root, 10, 2)
            self.assertEqual(result["status"], "UNVERIFIED")
            self.assertNotIn("median_s", result)

    def test_paired_rust_receipt_accepts_match_and_blocks_mutants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "target/release/core-math-demand-rust-paired"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"local-stub-for-receipt-validator")
            checksum, ops = self.m.workload_python(17)
            receipt = {"schema": "sens-math-q-rust-side/v1",
                       "corpus": self.m.CORPUS, "iters": 17, "reps": 3,
                       "ops": ops, "checksum": str(checksum), "median_s": 0.005}
            with mock.patch.object(self.m, "_run",
                                   return_value=(True, json.dumps(receipt))):
                result = self.m.measure_rust(root, 17, 3)
            self.assertEqual(result["status"], "MEASURED")
            self.assertEqual(result["ops"], 51)
            self.assertEqual(result["checksum"], str(checksum))
            for mutant in ({"checksum": str(checksum + 1)}, {"iters": 16},
                           {"median_s": 0.0},
                           {"corpus": list(reversed(self.m.CORPUS))}):
                changed = dict(receipt, **mutant)
                with mock.patch.object(self.m, "_run",
                                       return_value=(True, json.dumps(changed))):
                    result = self.m.measure_rust(root, 17, 3)
                self.assertEqual(result["status"], "ERROR", mutant)
                self.assertNotIn("median_s", result)

if __name__ == "__main__":
    unittest.main()
