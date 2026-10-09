"""Verification of the experiment protocol (not a benchmark speed verdict)."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "benchmarks" / "methodology" / "paired_wall.py"
spec = importlib.util.spec_from_file_location("paired_wall", SOURCE)
assert spec and spec.loader
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class RandomPairedProtocol(unittest.TestCase):
    def test_seeded_orders_balanced_and_repeatable(self):
        a = bench.balanced_orders(51, random.Random(481))
        b = bench.balanced_orders(51, random.Random(481))
        self.assertEqual(a, b)
        self.assertEqual(len(a), 51)
        self.assertEqual(set(a), {"AB", "BA"})
        self.assertLessEqual(abs(a.count("AB") - a.count("BA")), 1)
        self.assertEqual(bench.balanced_orders(0, random.Random(4)), [])

    def test_relative_effect_bootstrap_recovers_b_faster(self):
        samples = [[math.log(0.6)] * 7 for _ in range(5)]
        result = bench.session_bootstrap(samples, draws=600, seed=77)
        self.assertAlmostEqual(result["B_over_A_ratio"], 0.6, places=10)
        lo, hi = result["B_over_A_95pct_exploratory_CI"]
        self.assertAlmostEqual(lo, 0.6)
        self.assertAlmostEqual(hi, 0.6)
        self.assertEqual(result["exploratory_single_host_verdict"],
                         "EXPLORATORY_B_FASTER")
        self.assertEqual(result["publishable_kalibera_jones_verdict"],
                         "BLOCKED_SINGLE_BUILD_SINGLE_HOST")

    def test_equal_lanes_are_not_a_speedup(self):
        result = bench.session_bootstrap([[0.0] * 5 for _ in range(4)],
                                         draws=600, seed=7)
        self.assertEqual(result["B_over_A_ratio"], 1.0)
        self.assertEqual(result["B_over_A_95pct_exploratory_CI"], [1.0, 1.0])
        self.assertEqual(result["exploratory_single_host_verdict"], "INCONCLUSIVE")

    def test_bad_bootstrap_unit_is_rejected(self):
        for samples in ([[0.0] * 5], [[0.0] * 4] * 3, [[float("nan")] * 5] * 3):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                bench.session_bootstrap(samples, draws=400, seed=0)

    def test_json_argv_never_uses_shell_expansion(self):
        self.assertEqual(bench.command('["a", "$HOME", "one two"]'),
                         ["a", "$HOME", "one two"])
        for malformed in ("not-json", "[]", '"echo hi"', '["", "x"]', '["a", 5]'):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                bench.command(malformed)

    def run_cli(self, a: list[str], b: list[str], payload: Path, out: Path):
        return subprocess.run(
            [sys.executable, str(SOURCE),
             "--a-json", json.dumps(a), "--b-json", json.dumps(b),
             "--payload", str(payload), "--out", str(out),
             "--sessions", "3", "--pairs-per-session", "5",
             "--warmups", "0", "--bootstrap", "400", "--seed", "29"],
            cwd=ROOT, capture_output=True, text=True, timeout=45, check=False
        )

    def test_same_command_a_a_is_parity_admitted_without_perf_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            payload = base / "exact.sens"
            payload.write_bytes(bytes([0x11, 0x26, 0xA1]))
            cmd = [sys.executable, "-c", "print('same-stdout')"]
            out = base / "artifacts"
            run = self.run_cli(cmd, cmd, payload, out)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads((out / "results.json").read_text())
            self.assertEqual(result["result"], "PARITY_PASS_EXPLORATORY_TIMING_ONLY")
            self.assertEqual(result["sessions"], 3)
            self.assertEqual(result["paired_trials_per_session"], 5)
            self.assertEqual(result["statistics"]["publishable_kalibera_jones_verdict"],
                             "BLOCKED_SINGLE_BUILD_SINGLE_HOST")
            rows = (out / "raw.tsv").read_text().splitlines()
            self.assertEqual(len(rows), 1 + 3 * 5)
            self.assertEqual(set(row.split("\t")[2] for row in rows[1:]),
                             {"AB", "BA"})
            repeat = self.run_cli(cmd, cmd, payload, out)
            self.assertNotEqual(repeat.returncode, 0)  # never overwrite pinned evidence

    def test_output_mismatch_blocks_all_timing_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            payload = base / "exact.sens"
            payload.write_bytes(b"\x01")
            a = [sys.executable, "-c", "print('A')"]
            b = [sys.executable, "-c", "print('B')"]
            out = base / "bad"
            run = self.run_cli(a, b, payload, out)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("output differs", run.stderr)
            self.assertFalse((out / "results.json").exists())


if __name__ == "__main__":
    unittest.main()
