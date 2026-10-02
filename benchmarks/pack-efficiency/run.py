#!/usr/bin/env python3
"""#2190: production Bits<1..8> packing density versus CPU cost."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

CASES = ("w1","w2","w3","w4","w5","w6","w7","w8","d1234","mixed18")
MODES = (
    "prepare-logical",
    "prepare-unpacked",
    "prepare-packed",
    "prepare-cached",
    "scan-unpacked",
    "scan-packed",
    "scan-cached",
)
IREF_RE = re.compile(r"I\s+refs:\s*([0-9,]+)")
BRANCH_RE = re.compile(r"Branches:\s*([0-9,]+)")
FIELD_RE = re.compile(r"([a-z_]+)=([^\s]+)")


def run_native(binary: Path, case: str, mode: str, count: int, scan_repeats: int):
    proc = subprocess.run(
        [str(binary), case, mode, str(count), str(scan_repeats)],
        check=True, capture_output=True, text=True,
    )
    line = proc.stdout.strip().splitlines()[-1]
    return {key: value for key, value in FIELD_RE.findall(line)}


def cachegrind(binary: Path, case: str, mode: str, count: int, scan_repeats: int):
    proc = subprocess.run(
        [
            "valgrind", "--tool=cachegrind", "--cache-sim=no", "--branch-sim=yes",
            "--cachegrind-out-file=/dev/null",
            str(binary), case, mode, str(count), str(scan_repeats),
        ],
        check=True, capture_output=True, text=True,
    )
    im = IREF_RE.search(proc.stderr)
    bm = BRANCH_RE.search(proc.stderr)
    if not im or not bm:
        raise RuntimeError(f"missing Cachegrind counters:\n{proc.stderr[-2000:]}")
    return int(im.group(1).replace(",", "")), int(bm.group(1).replace(",", ""))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_fact(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def median(values):
    return statistics.median(values)


def paired_delta(grouped, case, left, right, field):
    a = grouped[(case, left, field)]
    b = grouped[(case, right, field)]
    return median([x - y for x, y in zip(a, b)])


def positive(value: float) -> float:
    return max(0.0, value)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--count", type=int, default=65_536)
    ap.add_argument("--scan-repeats", type=int, default=4)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--only", default=",".join(CASES))
    args = ap.parse_args()

    if min(args.count, args.scan_repeats, args.reps) < 1:
        ap.error("count, scan-repeats and reps must be positive")
    selected = tuple(x for x in args.only.split(",") if x)
    unknown = set(selected) - set(CASES)
    if unknown:
        ap.error(f"unknown cases: {sorted(unknown)}")

    for case in selected:
        checksums = {}
        for mode in MODES:
            fact = run_native(args.binary, case, mode, min(args.count, 2048), 2)
            if mode.startswith("scan-"):
                checksums[mode] = fact["checksum"]
        if len(set(checksums.values())) != 1:
            raise RuntimeError(f"{case}: scan parity failed: {checksums}")
        print(f"[verify] {case}: checksum={next(iter(checksums.values()))}")
    raw_rows = []
    grouped = defaultdict(list)
    for rep in range(1, args.reps + 1):
        for case in selected:
            for mode in MODES:
                irefs, branches = cachegrind(
                    args.binary, case, mode, args.count, args.scan_repeats
                )
                raw_rows.append((case, mode, rep, irefs, branches))
                grouped[(case, mode, "i_refs")].append(irefs)
                grouped[(case, mode, "branches")].append(branches)
        print(f"[measure] repetition {rep}/{args.reps}")

    facts = {
        case: run_native(args.binary, case, "prepare-packed", args.count, args.scan_repeats)
        for case in selected
    }

    summary = []
    for case in selected:
        fact = facts[case]
        words = args.count
        semantic_bits = int(fact["semantic_bits"])
        unpacked_bytes = int(fact["unpacked_bytes"])
        packed_bytes = int(fact["packed_bytes"])

        enc_i = positive(paired_delta(grouped, case, "prepare-packed", "prepare-logical", "i_refs"))
        mat_i = positive(paired_delta(grouped, case, "prepare-unpacked", "prepare-logical", "i_refs"))
        dec_i = positive(paired_delta(grouped, case, "prepare-cached", "prepare-packed", "i_refs"))

        unpack_scan_i = positive(paired_delta(grouped, case, "scan-unpacked", "prepare-unpacked", "i_refs"))
        pack_scan_i = positive(paired_delta(grouped, case, "scan-packed", "prepare-packed", "i_refs"))
        cache_scan_i = positive(paired_delta(grouped, case, "scan-cached", "prepare-cached", "i_refs"))

        unpack_scan_b = positive(paired_delta(grouped, case, "scan-unpacked", "prepare-unpacked", "branches"))
        pack_scan_b = positive(paired_delta(grouped, case, "scan-packed", "prepare-packed", "branches"))
        cache_scan_b = positive(paired_delta(grouped, case, "scan-cached", "prepare-cached", "branches"))

        scan_ops = words * args.scan_repeats
        packed_one_pass = pack_scan_i / args.scan_repeats
        cached_one_pass = cache_scan_i / args.scan_repeats
        if packed_one_pass > cached_one_pass:
            crossover = dec_i / (packed_one_pass - cached_one_pass)
        else:
            crossover = math.inf

        summary.append({
            "case": case,
            "words": words,
            "avg_bits_per_word": semantic_bits / words,
            "unpacked_bytes": unpacked_bytes,
            "packed_bytes": packed_bytes,
            "density_gain": unpacked_bytes / packed_bytes,
            "payload_utilization": semantic_bits / (packed_bytes * 8),
            "materialize_i_per_word": mat_i / words,
            "encode_i_per_word": enc_i / words,
            "decode_once_i_per_word": dec_i / words,
            "unpacked_scan_i_per_word": unpack_scan_i / scan_ops,
            "packed_scan_i_per_word": pack_scan_i / scan_ops,
            "cached_scan_i_per_word": cache_scan_i / scan_ops,
            "packed_scan_slowdown": (pack_scan_i / unpack_scan_i) if unpack_scan_i else math.nan,
            "cached_scan_slowdown": (cache_scan_i / unpack_scan_i) if unpack_scan_i else math.nan,
            "cache_crossover_passes": crossover,
            "unpacked_branches_per_word": unpack_scan_b / scan_ops,
            "packed_branches_per_word": pack_scan_b / scan_ops,
            "cached_branches_per_word": cache_scan_b / scan_ops,
        })

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "raw.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["case","mode","rep","i_refs","branches"])
        writer.writerows(raw_rows)

    fields = list(summary[0].keys())
    with (args.out / "summary.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(summary)

    versions = {}
    for name, cmd in {
        "valgrind": ["valgrind", "--version"],
        "rustc": ["rustc", "--version"],
    }.items():
        versions[name] = subprocess.run(
            cmd, check=True, capture_output=True, text=True
        ).stdout.strip()

    environment = {
        "git_sha": git_fact("rev-parse", "HEAD"),
        "binary_sha256": sha256(args.binary),
        "cpu": cpu_model(),
        "platform": platform.platform(),
        "count": args.count,
        "scan_repeats": args.scan_repeats,
        "reps": args.reps,
        "cases": list(selected),
        **versions,
    }
    (args.out / "environment.json").write_text(
        json.dumps(environment, indent=2, ensure_ascii=False) + "\n"
    )
    lines = [
        "# Dense packing efficiency — #2190",
        "",
        f"Cachegrind median of {args.reps} paired runs; {args.count:,} words/case; "
        f"{args.scan_repeats} scans for scan lanes.",
        "",
        "Widths are supplied out-of-band to both representations. This measures "
        "payload mechanics only; it does not choose #2189 framing.",
        "",
        "| case | bits/word | bytes u8 | bytes packed | density | encode I/word | "
        "decode-once I/word | scan u8 I/word | scan packed I/word | scan cache I/word | "
        "packed/u8 | cache crossover passes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        cross = row["cache_crossover_passes"]
        cross_text = "never" if math.isinf(cross) else f"{cross:.2f}"
        lines.append(
            f"| {row['case']} | {row['avg_bits_per_word']:.3f} | "
            f"{row['unpacked_bytes']:,} | {row['packed_bytes']:,} | "
            f"x{row['density_gain']:.3f} | {row['encode_i_per_word']:.3f} | "
            f"{row['decode_once_i_per_word']:.3f} | "
            f"{row['unpacked_scan_i_per_word']:.3f} | "
            f"{row['packed_scan_i_per_word']:.3f} | "
            f"{row['cached_scan_i_per_word']:.3f} | "
            f"x{row['packed_scan_slowdown']:.3f} | {cross_text} |"
        )

    lines += [
        "",
        "Interpretation:",
        "- bytes u8 is one payload byte per logical word; width schedule is external.",
        "- bytes packed is the production sequential BitPacker payload lower bound.",
        "- encode cost is prepare-packed minus prepare-logical.",
        "- decode-once cost is prepare-cached minus prepare-packed.",
        "- scan costs subtract their representation-specific preparation path.",
        "- cache crossover asks when one packed-to-u8 decode is cheaper than repeatedly bit-reading packed data.",
        "- raw branch counts and all repetitions are in raw.tsv / summary.tsv.",
        "",
    ]
    report = "\n".join(lines).rstrip() + "\n"
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
