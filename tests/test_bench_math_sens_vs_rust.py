#!/usr/bin/env python3
"""Controls for the paired SENS-vs-Rust math benchmark harness."""
from __future__ import annotations

import importlib.util
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

    def test_rust_exact_q_receipt_rejects_wrong_checksum(self) -> None:
        import json
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            binary = root / "benchmarks/core-math-demand-rust/target/release/paired_exact_q"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"test-only-mocked-runner")
            checksum, ops = self.m.workload_python(7)
            valid = json.dumps({"schema": "sens-paired-exact-q-rust/v1",
                                "iters": 7, "ops": ops, "checksum": str(checksum)})
            with patch.object(self.m, "_run", return_value=(True, valid)):
                measured = self.m.measure_rust(root, 7, 2)
            self.assertEqual(measured["status"], "MEASURED")
            self.assertEqual(measured["ops"], 21)
            self.assertEqual(measured["checksum"], str(checksum))
            self.assertIn("binary_sha256", measured)
            mutant = json.dumps({"schema": "sens-paired-exact-q-rust/v1",
                                 "iters": 7, "ops": ops, "checksum": "0"})
            with patch.object(self.m, "_run", return_value=(True, mutant)):
                rejected = self.m.measure_rust(root, 7, 2)
            self.assertEqual(rejected["status"], "ERROR")
            self.assertNotIn("median_s", rejected)

    def test_rust_success_without_workload_receipt_does_not_count(self) -> None:
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            binary = root / "benchmarks/core-math-demand-rust/target/release/paired_exact_q"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"mock")
            with patch.object(self.m, "_run", return_value=(True, "done")):
                rejected = self.m.measure_rust(root, 1, 1)
            self.assertEqual(rejected["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
