#!/usr/bin/env python3
"""Reject malformed or unproven physical-T5 preparation benchmarks.

This is not a "faster than" gate: the measured result is the result.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import statistics

CASES = {"d3-quote-empty", "d1-yes", "d3-atom-empty"}
PHASES = {"warm-bare", "fresh-bare"}
SCHEMA = "sens-native-zero-prepared/v1"
ORACLE = "physical-and-prepared-exact-value-output-parity"


def positive(x: object, field: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (float, int)):
        raise ValueError(f"{field}: expected measured number")
    value = float(x)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{field}: expected finite positive sample")
    return value


def validate(rows: list[dict]) -> tuple[int, list[dict]]:
    if len(rows) != 6 or {
        (r.get("case"), r.get("phase")) for r in rows
    } != {(case, phase) for case in CASES for phase in PHASES}:
        raise ValueError("expected exactly one row for each of six case/phase pairs")

    counts = {r.get("samples") for r in rows}
    if len(counts) != 1:
        raise ValueError("unpaired/unequal sample counts")
    samples = counts.pop()
    if not isinstance(samples, int) or not (3 <= samples <= 31) or samples % 2 == 0:
        raise ValueError("invalid sample count")
    for row in rows:
        ident = f"{row['case']}/{row['phase']}"
        if row.get("schema") != SCHEMA or row.get("oracle") != ORACLE:
            raise ValueError(f"{ident}: no exact independent oracle")
        if (not isinstance(row.get("iterations"), int)
                or not 16 <= row["iterations"] <= 4096):
            raise ValueError(f"{ident}: invalid iteration count")
        expected_bytes = 1 if row["case"] == "d1-yes" else 4
        if row.get("physical_bytes") != expected_bytes or row.get("form_count") != 1:
            raise ValueError(f"{ident}: changed physical identity or D2 program form count")
        positive(row.get("preparation_once_ns"), f"{ident}/one-time preparation")
        a = positive(row.get("direct_median_ns"), f"{ident}/direct median")
        b = positive(row.get("prepared_median_ns"), f"{ident}/prepared median")
        ratio = positive(row.get("ratio_direct_over_prepared"), f"{ident}/ratio")
        if not math.isclose(a / b, ratio, rel_tol=0.001):
            raise ValueError(f"{ident}: claimed ratio differs from measured medians")
        for key, median in [
            ("direct_samples_ns", a),
            ("prepared_samples_ns", b),
        ]:
            series = row.get(key)
            if not isinstance(series, list) or len(series) != samples:
                raise ValueError(f"{ident}: lost paired raw samples: {key}")
            nums = [positive(v, f"{ident}/{key}") for v in series]
            if not math.isclose(statistics.median(nums), median, abs_tol=0.02):
                raise ValueError(f"{ident}: claimed median differs from raw samples")
    return samples, rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    samples, evidence = validate(rows)
    lines = [
        "# SENS Native Zero — prepared T5 reuse",
        "",
        f"{samples} alternating-order paired samples per phase on the same GitHub-hosted CPU.",
        "Every candidate was validated from real physical bytes using exact D2,",
        "then compared by VALUE and OUTPUT with direct T5 execution before timing.",
        "",
        "| Case | Bare Session | Full T5 ns | Prepared reuse ns | Full/Reuse | Prepare once ns |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in evidence:
        lines.append(
            f"| {row['case']} | {row['phase']} | {row['direct_median_ns']:.1f} "
            f"| {row['prepared_median_ns']:.1f} | {row['ratio_direct_over_prepared']:.2f}× "
            f"| {row['preparation_once_ns']} |"
        )
    lines.extend([
        "",
        "**Different workloads:** full T5 decodes, validates D2, lowers and executes",
        "on every call; prepared reuse does all those preparatory stages ONCE.",
        "Preparation-once cost is excluded from repeated-execution measurements;",
        "ratios are amortization experiments, not equal-work decoder speedups.",
        "Each execution still enforces exact D1/D3 laws and uses the current evaluator.",
        "No cached semantic results, no Core4, no machine-code compilation, no process",
        "startup measurement, and no evidence of GPU/FPGA performance.",
        "",
    ])
    report = "\n".join(lines)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
