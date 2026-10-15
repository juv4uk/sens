"""Негативні й позитивні квитанції парного exact-Q runner; без семантики SENS."""
import os
import runpy
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = runpy.run_path(str(ROOT / "scripts/bench_math_sens_vs_rust.py"))


class PairedRustMathTest(unittest.TestCase):
    def runner(self, directory: Path, *, checksum: int, ops: int,
               schema: str = "sens-exact-q-rust-benchmark/v1") -> Path:
        path = directory / "paired-rust-stub"
        # This is a *mock* receipt to test the gate, not an arithmetic benchmark.
        path.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "iters = int(sys.argv[2])\n"
            f"print(json.dumps(dict(schema={schema!r}, iters=iters, "
            f"ops={ops!r}, checksum={str(checksum)!r})))\n",
            encoding="utf-8",
        )
        path.chmod(0o700)
        return path

    def test_matching_receipt_and_missing_runner_are_distinguished(self):
        count = 19
        checksum, ops = BENCH["workload_python"](count)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = self.runner(root, checksum=checksum, ops=ops)
            positive = BENCH["measure_rust"](root, count, 2, str(path), checksum, ops)
            self.assertEqual(positive["status"], "MEASURED")
            self.assertEqual(positive["checksum"], checksum)
            self.assertEqual(len(positive["binary_sha256"]), 64)
            absent = BENCH["measure_rust"](root, count, 2, str(root / "no-file"),
                                           checksum, ops)
            self.assertEqual(absent["status"], "UNVERIFIED")

    def test_mismatched_identity_operations_or_single_checksum_bit_fails_closed(self):
        count = 19
        checksum, ops = BENCH["workload_python"](count)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for kwargs in (
                {"checksum": checksum ^ 1, "ops": ops},
                {"checksum": checksum, "ops": ops + 1},
                {"checksum": checksum, "ops": ops, "schema": "research-demand-not-q"},
            ):
                with self.subTest(mutant=kwargs):
                    path = self.runner(root, **kwargs)
                    row = BENCH["measure_rust"](root, count, 1, str(path), checksum, ops)
                    self.assertEqual(row["status"], "ERROR")
                    self.assertIn("MATH_RUST_UNMATCHED_RECEIPT", row["note"])


if __name__ == "__main__":
    unittest.main()
