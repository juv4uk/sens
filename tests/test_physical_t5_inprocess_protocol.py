#!/usr/bin/env python3
"""Falsifiers for physical SENS in-process benchmark evidence protocol."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sens_physical_phase", ROOT / "benchmarks/byte-pack/physical_phase.py"
)
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

PHASES = MOD.PHASES


def protocol(reps: int = 5, inner: int = 20, *, value: str = "()") -> bytes:
    lines = [
        "PROBE\tversion\t1",
        "ORACLE_HEX\t" + value.encode("utf-8").hex(),
        "WORDS\t8",
        "T5_BYTES\t6",
    ]
    for phase in PHASES:
        for rep in range(reps):
            lines.append(f"SAMPLE\t{phase}\t{rep}\t{inner}\t{100 + rep}")
    return ("\n".join(lines) + "\n").encode("ascii")


class ProbeEvidenceContract(unittest.TestCase):
    def test_complete_inprocess_rows_require_all_six_real_phase_names(self):
        value, words, size, samples = MOD.parse_probe(protocol(), reps=5, inner=20)
        self.assertEqual(value, b"()")
        self.assertEqual(words, 8)
        self.assertEqual(size, 6)
        self.assertEqual(set(samples), set(PHASES))
        self.assertTrue(all(len(v) == 5 for v in samples.values()))

    def test_rejects_missing_or_duplicated_samples(self):
        data = protocol().decode("ascii")
        line = "SAMPLE\tparse_d2\t0\t20\t100\n"
        self.assertIn(line, data)
        for bad in [data.replace(line, ""), data.replace(line, line + line)]:
            with self.subTest(bad=bad[:20]), self.assertRaises(ValueError):
                MOD.parse_probe(bad.encode("ascii"), reps=5, inner=20)

    def test_rejects_false_precision_or_non_monotonic_timers(self):
        data = protocol().decode("ascii")
        for replacement in [
            "SAMPLE\tdecode_t5\t0\t20\t0",
            "SAMPLE\tdecode_t5\t0\t19\t100",
            "SAMPLE\tdecode_t5\t7\t20\t100",
            "SAMPLE\tunknown\t0\t20\t100",
        ]:
            bad = data.replace("SAMPLE\tdecode_t5\t0\t20\t100", replacement)
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                MOD.parse_probe(bad.encode("ascii"), reps=5, inner=20)

    def test_rejects_missing_or_duplicate_oracle_and_malformed_schema(self):
        src = protocol().decode("ascii")
        cases = [
            src.replace("ORACLE_HEX\t2829\n", ""),
            src.replace("ORACLE_HEX\t2829\n", "ORACLE_HEX\t2829\nORACLE_HEX\t2829\n"),
            src.replace("PROBE\tversion\t1", "PROBE\tversion\tlegacy"),
            src.replace("ORACLE_HEX\t2829", "ORACLE_HEX\tXX"),
        ]
        for case in cases:
            with self.subTest(case=case[:40]), self.assertRaises(ValueError):
                MOD.parse_probe(case.encode("ascii"), reps=5, inner=20)

    def test_cli_stdout_must_exactly_match_core_oracle(self):
        with tempfile.TemporaryDirectory() as temporary:
            previous_root = MOD.ROOT
            try:
                MOD.ROOT = Path(temporary)
                artifact = MOD.ROOT / "physical.sens"
                artifact.write_bytes(b"123456")
                helper, sens, trit = (MOD.ROOT / n for n in ("helper", "sens", "trit"))
                for exe in (helper, sens, trit):
                    exe.write_bytes(b"dummy")
                calls = [
                    b"()\n",
                    b"()\n",
                    protocol(value="NO"),
                ]
                with patch.object(MOD, "checked", side_effect=calls):
                    with self.assertRaisesRegex(ValueError, "differs from exact CLI stdout"):
                        MOD.one_fixture(helper, sens, trit, artifact, warmup=0, reps=5, inner=20)
                with patch.object(MOD, "checked", side_effect=[b"1\n", b"0\n"]):
                    with self.assertRaisesRegex(ValueError, "disagree"):
                        MOD.one_fixture(helper, sens, trit, artifact, warmup=0, reps=5, inner=20)
            finally:
                MOD.ROOT = previous_root

    def test_p95_nearest_rank_never_interpolates_invented_sample(self):
        self.assertEqual(MOD.nearest_rank([9, 1, 7, 3, 5], 0.95), 9)
        self.assertEqual(MOD.nearest_rank([9, 1, 7, 3, 5], 0.50), 5)


if __name__ == "__main__":
    unittest.main()
