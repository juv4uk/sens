#!/usr/bin/env python3
"""Cachegrind runner for the ratified D1->D4 exact-width foundation.

The benchmark compares like-for-like carrier work across D1/D2/D3/D4 and also
measures the width ladder, D3->D4 selector generation, and mixed typed-domain
routing. It deliberately does not compare English names with historical
Function8 identities.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import statistics
import subprocess
from pathlib import Path

CASES = ("d1", "d2", "d3", "d4", "ladder", "selector", "mixed")
IREF_RE = re.compile(r"I\s+refs:\s*([0-9,]+)")


def run_native(binary: str, case: str, iterations: int) -> str:
    proc = subprocess.run(
        [binary, case, str(iterations)],
        check=True,
        capture_output=True,
        text=True,
    )
    line = proc.stdout.strip().splitlines()[-1]
    if f"case={case}" not in line:
        raise RuntimeError(f"unexpected output for {case}: {line!r}")
    return line


def irefs(binary: str, case: str, iterations: int) -> int:
    proc = subprocess.run(
        [
            "valgrind",
            "--tool=cachegrind",
            "--cache-sim=no",
            "--branch-sim=no",
            "--cachegrind-out-file=/dev/null",
            binary,
            case,
            str(iterations),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    match = IREF_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(f"Cachegrind I refs missing for {case}: {proc.stderr[-1200:]}")
    return int(match.group(1).replace(",", ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--iterations", type=int, default=200_000)
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()

    if args.iterations <= 0 or args.reps <= 0:
        raise SystemExit("iterations and reps must be positive")

    # Correctness/invariant pass before measurement.
    for case in ("empty",) + CASES:
        print("[verify]", run_native(args.binary, case, min(args.iterations, 10_000)))

    baselines = [irefs(args.binary, "empty", args.iterations) for _ in range(args.reps)]
    empty = statistics.median(baselines)

    rows = []
    for case in CASES:
        raw = [irefs(args.binary, case, args.iterations) for _ in range(args.reps)]
        net = [max(0, value - empty) for value in raw]
        median_raw = statistics.median(raw)
        median_net = statistics.median(net)
        rows.append(
            {
                "case": case,
                "iterations": args.iterations,
                "reps": args.reps,
                "empty_i_refs": int(empty),
                "raw_i_refs_median": int(median_raw),
                "raw_i_refs_per_iteration": median_raw / args.iterations,
                "net_i_refs_median": int(median_net),
                "net_i_refs_per_iteration": median_net / args.iterations,
                "spread_pct": (
                    (max(raw) - min(raw)) / median_raw * 100.0 if median_raw else 0.0
                ),
            }
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "case",
        "iterations",
        "reps",
        "empty_i_refs",
        "raw_i_refs_median",
        "raw_i_refs_per_iteration",
        "net_i_refs_median",
        "net_i_refs_per_iteration",
        "spread_pct",
    ]
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "## Ratified D1-D4 foundation benchmark",
        "",
        f"Cachegrind I refs, median of {args.reps} runs, {args.iterations:,} iterations.",
        "The empty-loop baseline is subtracted. D1-D4 rows execute the same carrier shape.",
        "",
        "| case | raw I refs / iter | extra I refs / iter vs empty | spread |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['raw_i_refs_per_iteration']:.3f} | "
            f"{row['net_i_refs_per_iteration']:.3f} | "
            f"{row['spread_pct']:.3f}% |"
        )
    lines += [
        "",
        "D1-D3 use PredicateBit/Racana2/Bija3. D4 uses exact Bit4 through a",
        "benchmark-local transparent wrapper until production D4 semantics lands in #2169.",
        "The selector lane verifies 101/110 -> 1010/1011/1100/1101 before measuring.",
        "",
    ]

    report = "\n".join(lines)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
