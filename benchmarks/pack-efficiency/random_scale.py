#!/usr/bin/env python3
"""#2190 follow-up: random-access cost and size/working-set scaling."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import re
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

CASES = ("w1", "w2", "w3", "d1234", "mixed18", "w8")
PREP = {
    "unpacked": "prepare-random-unpacked",
    "packed": "prepare-random-packed",
    "cached": "prepare-random-cached",
}
SCAN = {
    "unpacked": "random-unpacked",
    "packed": "random-packed",
    "cached": "random-cached",
}
IREF_RE = re.compile(r"I\s+refs:\s*([0-9,]+)")
D1_RE = re.compile(r"D1\s+misses:\s*([0-9,]+)")
LLD_RE = re.compile(r"LLd\s+misses:\s*([0-9,]+)")
FIELD_RE = re.compile(r"([a-z_]+)=([^\s]+)")


def run_native(binary: Path, case: str, mode: str, count: int, repeats: int, accesses: int):
    proc = subprocess.run(
        [str(binary), case, mode, str(count), str(repeats), str(accesses)],
        check=True,
        capture_output=True,
        text=True,
    )
    line = proc.stdout.strip().splitlines()[-1]
    return {key: value for key, value in FIELD_RE.findall(line)}


def cachegrind(binary: Path, case: str, mode: str, count: int, repeats: int, accesses: int):
    proc = subprocess.run(
        [
            "valgrind",
            "--tool=cachegrind",
            "--cache-sim=yes",
            "--branch-sim=no",
            "--cachegrind-out-file=/dev/null",
            str(binary),
            case,
            mode,
            str(count),
            str(repeats),
            str(accesses),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    im = IREF_RE.search(proc.stderr)
    dm = D1_RE.search(proc.stderr)
    lm = LLD_RE.search(proc.stderr)
    if not im or not dm or not lm:
        raise RuntimeError(f"missing Cachegrind counters:\n{proc.stderr[-3000:]}")
    number = lambda m: int(m.group(1).replace(",", ""))
    return number(im), number(dm), number(lm)


def median(values):
    return statistics.median(values)


def paired_delta(grouped, key, scan_mode, prep_mode, field):
    scan = grouped[(key, scan_mode, field)]
    prep = grouped[(key, prep_mode, field)]
    return max(0.0, median([a - b for a, b in zip(scan, prep)]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sizes", default="8,64,1024,65536,1000000")
    ap.add_argument("--cases", default=",".join(CASES))
    ap.add_argument("--accesses", type=int, default=4096)
    ap.add_argument("--scan-repeats", type=int, default=1)
    ap.add_argument("--reps", type=int, default=1)
    args = ap.parse_args()

    sizes = tuple(int(x) for x in args.sizes.split(",") if x)
    cases = tuple(x for x in args.cases.split(",") if x)
    if not sizes or min(*sizes, args.accesses, args.scan_repeats, args.reps) < 1:
        ap.error("sizes/accesses/repeats must be positive")
    unknown = set(cases) - set(CASES)
    if unknown:
        ap.error(f"unknown cases: {sorted(unknown)}")

    args.out.mkdir(parents=True, exist_ok=True)

    # Correctness is established outside measured Cachegrind runs.
    for case in cases:
        for count in sizes:
            checksums = {}
            for lane, mode in SCAN.items():
                fact = run_native(
                    args.binary, case, mode, count, 1, min(args.accesses, 4096)
                )
                checksums[lane] = fact["checksum"]
            if len(set(checksums.values())) != 1:
                raise RuntimeError(f"{case}/{count}: random parity failed: {checksums}")
            print(f"[verify] {case}/{count}: {next(iter(checksums.values()))}")

    grouped = defaultdict(list)
    raw_rows = []
    for rep in range(1, args.reps + 1):
        for case in cases:
            for count in sizes:
                key = (case, count)
                for lane in PREP:
                    for mode in (PREP[lane], SCAN[lane]):
                        irefs, d1, lld = cachegrind(
                            args.binary,
                            case,
                            mode,
                            count,
                            args.scan_repeats,
                            args.accesses,
                        )
                        raw_rows.append(
                            (case, count, lane, mode, rep, irefs, d1, lld)
                        )
                        grouped[(key, mode, "i_refs")].append(irefs)
                        grouped[(key, mode, "d1_misses")].append(d1)
                        grouped[(key, mode, "lld_misses")].append(lld)
        print(f"[measure] repetition {rep}/{args.reps}")

    summary = []
    for case in cases:
        for count in sizes:
            key = (case, count)
            packed_fact = run_native(
                args.binary,
                case,
                PREP["packed"],
                count,
                1,
                args.accesses,
            )
            cache_fact = run_native(
                args.binary,
                case,
                PREP["cached"],
                count,
                1,
                args.accesses,
            )
            semantic_bits = int(packed_fact["semantic_bits"])
            unpacked_bytes = int(packed_fact["unpacked_bytes"])
            packed_bytes = int(packed_fact["packed_bytes"])
            offset_bytes = int(packed_fact["offset_index_bytes"])
            access_index_bytes = int(packed_fact["access_index_bytes"])
            cache_bytes = int(cache_fact["cache_bytes"])
            ops = args.accesses * args.scan_repeats

            row = {
                "case": case,
                "words": count,
                "random_accesses": args.accesses,
                "scan_repeats": args.scan_repeats,
                "avg_bits_per_word": semantic_bits / count,
                "unpacked_bytes": unpacked_bytes,
                "packed_bytes": packed_bytes,
                "offset_index_bytes": offset_bytes,
                "packed_plus_offset_bytes": packed_bytes + offset_bytes,
                "cache_bytes": cache_bytes,
                "access_index_bytes_common": access_index_bytes,
                "payload_density_gain": unpacked_bytes / packed_bytes,
                "packed_plus_offset_vs_unpacked": (packed_bytes + offset_bytes) / unpacked_bytes,
            }
            for lane in PREP:
                prep_mode = PREP[lane]
                scan_mode = SCAN[lane]
                irefs = paired_delta(grouped, key, scan_mode, prep_mode, "i_refs")
                d1 = paired_delta(grouped, key, scan_mode, prep_mode, "d1_misses")
                lld = paired_delta(grouped, key, scan_mode, prep_mode, "lld_misses")
                row[f"{lane}_random_i_per_access"] = irefs / ops
                row[f"{lane}_d1_misses_per_1k"] = d1 * 1000.0 / ops
                row[f"{lane}_lld_misses_per_1k"] = lld * 1000.0 / ops
            row["packed_vs_cached_i"] = (
                row["packed_random_i_per_access"] / row["cached_random_i_per_access"]
                if row["cached_random_i_per_access"]
                else math.inf
            )
            summary.append(row)

    with (args.out / "random-raw.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(
            ["case","words","lane","mode","rep","i_refs","d1_misses","lld_misses"]
        )
        writer.writerows(raw_rows)

    fields = list(summary[0].keys())
    with (args.out / "random-summary.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(summary)

    environment = {
        "git_sha": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "sizes": list(sizes),
        "cases": list(cases),
        "accesses": args.accesses,
        "scan_repeats": args.scan_repeats,
        "reps": args.reps,
        "cachegrind": subprocess.run(
            ["valgrind", "--version"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "rustc": subprocess.run(
            ["rustc", "--version"], check=True, capture_output=True, text=True
        ).stdout.strip(),
    }
    (args.out / "random-environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Random-access and size scaling — #2190",
        "",
        "Cachegrind scan deltas subtract the matching representation preparation path.",
        "Correctness parity is checked natively before measurement.",
        "",
        "| case | words | packed B | offset-index B | packed+index/u8 | "
        "u8 I/access | packed I/access | cache I/access | packed/cache | "
        "packed D1 miss/1k | cache D1 miss/1k |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['case']} | {row['words']:,} | {row['packed_bytes']:,} | "
            f"{row['offset_index_bytes']:,} | x{row['packed_plus_offset_vs_unpacked']:.3f} | "
            f"{row['unpacked_random_i_per_access']:.2f} | "
            f"{row['packed_random_i_per_access']:.2f} | "
            f"{row['cached_random_i_per_access']:.2f} | "
            f"x{row['packed_vs_cached_i']:.2f} | "
            f"{row['packed_d1_misses_per_1k']:.2f} | "
            f"{row['cached_d1_misses_per_1k']:.2f} |"
        )
    lines += [
        "",
        "Boundary accounting:",
        "- homogeneous W1/W2/W3/W8 derives offset as index*width, so offset-index bytes are zero;",
        "- mixed variable-width cases use an explicit host usize offset-index proxy;",
        "- cached hot random access needs only the decoded u8 cache; the packed payload may be cold/discarded;",
        "- access-index bytes are common benchmark workload data and are reported separately.",
        "",
        "These are mechanism measurements, not a framing decision. A future grammar/index may encode mixed boundaries more compactly than the host usize proxy.",
    ]
    report = "\n".join(lines) + "\n"
    (args.out / "random-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
