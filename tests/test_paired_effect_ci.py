"""Falsifiers for the opt-in SENS paired performance statistics reporter."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks/packed-vs-visible/paired_effect_ci.py"
SHA = "0" * 40

spec = importlib.util.spec_from_file_location("sens_paired_effect", SCRIPT)
assert spec is not None and spec.loader is not None
stat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stat)


def row(visible=None, packed=None):
    visible = visible if visible is not None else [200.0 + i for i in range(9)]
    packed = packed if packed is not None else [100.0 + i for i in range(9)]
    return {
        "schema": "sens-packed-visible-runtime/v1",
        "case": "quote-empty-64",
        "phase": "warm-session-parse-lower-eval",
        "oracle": "same-evaluated-value-output",
        "samples": len(visible),
        "visible_samples_ns": visible,
        "packed_samples_ns": packed,
        "visible_median_ns": visible[len(visible) // 2],
        "packed_median_ns": packed[len(packed) // 2],
        "ratio_visible_over_packed": visible[len(visible) // 2] / packed[len(packed) // 2],
    }


class PairedEffectTests(unittest.TestCase):
    def test_positive_effect_and_reproducible_bootstrap(self):
        record = row()
        a = stat.analyze(record, source_sha=SHA, seed=112, resamples=1000)
        b = stat.analyze(record, source_sha=SHA, seed=112, resamples=1000)
        self.assertEqual(a, b)
        self.assertEqual(a["verdict"], "PACKED_FASTER_WITHIN_RUN")
        self.assertGreater(a["ci95_paired_bootstrap"][0], 1)
        self.assertEqual(a["paired_batches"], 9)
        self.assertIn("NOT independent-run Kalibera-Jones", a["ci_scope"])

    def test_slowdown_is_not_suppressed(self):
        result = stat.analyze(
            row(visible=[100.0 + i for i in range(9)],
                packed=[200.0 + i for i in range(9)]),
            source_sha=SHA, seed=112, resamples=1000,
        )
        self.assertEqual(result["verdict"], "VISIBLE_FASTER_WITHIN_RUN")
        self.assertLess(result["ci95_paired_bootstrap"][1], 1)

    def test_true_tie_is_not_a_win(self):
        equal = [100.0 + i for i in range(9)]
        outcome = stat.analyze(row(visible=equal, packed=equal),
                               source_sha=SHA, seed=112, resamples=1000)
        self.assertEqual(outcome["verdict"], "INCONCLUSIVE")
        self.assertEqual(outcome["ci95_paired_bootstrap"], [1.0, 1.0])

    def test_rejects_wrong_oracle_median_and_missing_pair(self):
        wrong = row()
        wrong["oracle"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "oracle"):
            stat.analyze(wrong, source_sha=SHA, seed=1, resamples=1000)
        wrong = row()
        wrong["visible_median_ns"] += 100
        with self.assertRaisesRegex(ValueError, "median"):
            stat.analyze(wrong, source_sha=SHA, seed=1, resamples=1000)
        wrong = row()
        wrong["packed_samples_ns"].pop()
        with self.assertRaisesRegex(ValueError, "odd count|batch counts"):
            stat.analyze(wrong, source_sha=SHA, seed=1, resamples=1000)
        wrong = row()
        wrong["packed_samples_ns"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            stat.analyze(wrong, source_sha=SHA, seed=1, resamples=1000)

    def test_cli_json_markdown_and_duplicate_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "source.jsonl"
            dest = root / "reports"
            raw.write_text(json.dumps(row()) + "\n", encoding="utf-8")
            cmd = [
                sys.executable, str(SCRIPT), "--input", str(raw),
                "--out-dir", str(dest), "--source-sha", SHA,
                "--seed", "7", "--resamples", "1000",
            ]
            out = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(out.returncode, 0, out.stderr)
            results = json.loads((dest / "paired-effect.json").read_text())
            self.assertEqual(len(results["results"]), 1)
            self.assertIn("NOT a Kalibera", (dest / "paired-effect.md").read_text())
            raw.write_text(json.dumps(row()) + "\n" + json.dumps(row()) + "\n")
            duplicate = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("duplicate", duplicate.stderr)

    def test_explicit_schema_paired_ingest(self):
        record = row()
        record["schema"] = "sens-packed-visible-ingest/v1"
        record.pop("phase")
        record.pop("oracle")
        record["preflight"] = "same-D2-domain-AST"
        result = stat.analyze(record, source_sha=SHA, seed=15, resamples=1000)
        self.assertEqual(result["phase"], "ingest")


if __name__ == "__main__":
    unittest.main()
