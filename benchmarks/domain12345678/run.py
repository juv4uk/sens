#!/usr/bin/env python3
"""Contract 11.8 W1-W9 exact-domain carrier microbenchmark, no Rust language laws."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import statistics
import subprocess
from pathlib import Path

CASES = (
    "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9",
    "mixed", "width-roundtrip",
)
CONTRACT_VERSION = "11.8"
SEMANTIC_GENERATION = "contract-11-8-exact-d1-d9"
D9_STATUS = "MEASURED-CARRIER"
D9_REASON = "Exact u16 W9 carrier is available; callability and language laws are not inferred"
D9_MECHANISM_OWNER = "#4008"
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


def command_output(args: list[str]) -> str:
    proc = subprocess.run(args, check=True, capture_output=True, text=True)
    return (proc.stdout or proc.stderr).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--iterations", type=int, default=200_000)
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()

    if args.iterations <= 0 or args.reps <= 0:
        raise SystemExit("iterations and reps must be positive")

    for case in ("empty",) + CASES:
        print("[verify]", run_native(args.binary, case, min(args.iterations, 10_000)))

    baselines = [irefs(args.binary, "empty", args.iterations) for _ in range(args.reps)]
    rows = []
    for case in CASES:
        raw = [irefs(args.binary, case, args.iterations) for _ in range(args.reps)]
        net = [max(0, value - base) for value, base in zip(raw, baselines)]
        median_raw = statistics.median(raw)
        median_net = statistics.median(net)
        rows.append(
            {
                "contract_version": CONTRACT_VERSION,
                "semantic_generation": SEMANTIC_GENERATION,
                "case": case,
                "iterations": args.iterations,
                "reps": args.reps,
                "raw_i_refs_median": int(median_raw),
                "raw_i_refs_per_iteration": median_raw / args.iterations,
                "net_i_refs_median": int(median_net),
                "net_i_refs_per_iteration": median_net / args.iterations,
                "spread_pct": (
                    (max(raw) - min(raw)) / median_raw * 100.0 if median_raw else 0.0
                ),
            }
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "results.tsv").open("w", newline="", encoding="utf-8") as fh:
        fields = list(rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    environment = {
        "git_sha": command_output(["git", "rev-parse", "HEAD"]),
        "rustc": command_output(["rustc", "--version"]),
        "valgrind": command_output(["valgrind", "--version"]),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "iterations": args.iterations,
        "reps": args.reps,
        "contract_version": CONTRACT_VERSION,
        "semantic_generation": SEMANTIC_GENERATION,
        "current_foundation": "D1-D9",
        "measured_carriers": "W1-W9",
        "d9_status": D9_STATUS,
        "d9_reason": D9_REASON,
        "d9_mechanism_owner": D9_MECHANISM_OWNER,
        "scope": "W1-W9 exact source-word -> DomainIdentity carrier/runtime",
        "semantic_authority": (
            "Contract 11.8 metadata; measured values are mechanical carrier cost only"
        ),
    }
    (args.out_dir / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# W1-W9 exact-width carrier benchmark — Contract 11.8 / D1-D9 authority",
        "",
        f"Cachegrind I refs, paired empty-loop subtraction, median of {args.reps} runs, "
        f"{args.iterations:,} iterations.",
        "",
        "This slice consumes production BinarySourceWord -> DomainIdentity APIs only.",
        "Current semantic authority is D1-D9; this Rust carrier materializes W1-W9.",
        f"D9 status: {D9_STATUS} — {D9_REASON}.",
        f"D9 mechanism owner: {D9_MECHANISM_OWNER}.",
        "It contains no benchmark-local residency table, surface-name lookup, or legacy "
        "Sens8/Function8 identity.",
        "",
        "| case | raw I refs / iter | extra I refs / iter vs paired empty | spread |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['raw_i_refs_per_iteration']:.3f} | "
            f"{row['net_i_refs_per_iteration']:.3f} | {row['spread_pct']:.3f}% |"
        )

    lines += [
        "",
        "Correctness invariants checked before measurement:",
        "- D1..D9 exact source words round-trip through DomainIdentity;",
        "- equal payload=1 at widths 1..9 never collapses;",
        "- D9 high-bit value 0x101 survives u16 source -> domain -> source;",
        "- names, callable-Core projection and semantic registry are not measured;",
        "- host u8 payload cannot substitute for exact-width D9 identity;",
        "",
        "Deferred lanes:",
        "- packed/framing accounting follows #3026/#2833;",
        "- W9 exact carrier has a measured lane; language execution remains separate;",
        "- registry/surface comparisons remain separate from carrier cost;",
        "- domain-law execution benchmarks are separate from carrier cost.",
        "",
    ]
    report = "\n".join(lines).rstrip() + "\n"
    (args.out_dir / "report.md").write_text(report, encoding="utf-8")
    print(report)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
