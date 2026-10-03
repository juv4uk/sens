#!/usr/bin/env python3
"""#2265 compact mixed-boundary index benchmark."""

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

IREF_RE = re.compile(r"I\s+refs:\s*([0-9,]+)")
D1_RE = re.compile(r"D1\s+misses:\s*([0-9,]+)")
LLD_RE = re.compile(r"LLd\s+misses:\s*([0-9,]+)")
FIELD_RE = re.compile(r"([a-z_]+)=([^\s]+)")


def run_native(binary: Path, case: str, candidate: str, mode: str,
               count: int, queries: int, repeats: int):
    proc = subprocess.run(
        [str(binary), case, candidate, mode, str(count), str(queries), str(repeats)],
        check=True, capture_output=True, text=True,
    )
    line = proc.stdout.strip().splitlines()[-1]
    return {key: value for key, value in FIELD_RE.findall(line)}


def cachegrind(binary: Path, case: str, candidate: str, mode: str,
               count: int, queries: int, repeats: int):
    proc = subprocess.run(
        [
            "valgrind", "--tool=cachegrind", "--cache-sim=yes", "--branch-sim=no",
            "--cachegrind-out-file=/dev/null",
            str(binary), case, candidate, mode, str(count), str(queries), str(repeats),
        ],
        check=True, capture_output=True, text=True,
    )
    im = IREF_RE.search(proc.stderr)
    dm = D1_RE.search(proc.stderr)
    lm = LLD_RE.search(proc.stderr)
    if not im or not dm or not lm:
        raise RuntimeError(f"missing Cachegrind counters:\n{proc.stderr[-3000:]}")
    value = lambda match: int(match.group(1).replace(",", ""))
    return value(im), value(dm), value(lm)


def candidates_for(case: str, ks: tuple[int, ...], explicit: tuple[str, ...] | None):
    if explicit is not None:
        return explicit
    out = ["usize", "u32"]
    if not case.startswith("w"):
        for k in ks:
            out.append(f"cp8-{k}")
        if case == "d1234":
            for k in ks:
                out.append(f"cp2-{k}")
            for k in ks:
                if k <= 64:
                    out.append(f"t2-{k}")
        for k in ks:
            out.append(f"sel-{k}")
        for k in ks:
            out.append(f"cp3-{k}")
    else:
        out.append("formula")
    out.append("cache2")
    return tuple(out)


def median(values):
    return statistics.median(values)


def paired(grouped, key, left, right, field):
    a = grouped[(key, left, field)]
    b = grouped[(key, right, field)]
    return max(0.0, median([x - y for x, y in zip(a, b)]))


def add_pareto(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["case"], row["words"])].append(row)
    for group in groups.values():
        for row in group:
            dominated = False
            for other in group:
                if other is row:
                    continue
                bytes_better = other["active_bytes"] <= row["active_bytes"]
                cpu_better = other["query_i_per_access"] <= row["query_i_per_access"]
                strict = (
                    other["active_bytes"] < row["active_bytes"]
                    or other["query_i_per_access"] < row["query_i_per_access"]
                )
                if bytes_better and cpu_better and strict:
                    dominated = True
                    break
            row["pareto"] = "yes" if not dominated else "no"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--cases", default="d1234")
    ap.add_argument("--sizes", default="64,65536,1000000")
    ap.add_argument("--ks", default="8,16,32,64,256")
    ap.add_argument("--candidates", default=None)
    ap.add_argument("--queries", type=int, default=4096)
    ap.add_argument("--query-repeats", type=int, default=1)
    ap.add_argument("--reps", type=int, default=1)
    args = ap.parse_args()

    cases = tuple(x for x in args.cases.split(",") if x)
    sizes = tuple(int(x) for x in args.sizes.split(",") if x)
    ks = tuple(int(x) for x in args.ks.split(",") if x)
    explicit = (
        tuple(x for x in args.candidates.split(",") if x)
        if args.candidates is not None else None
    )
    if not cases or not sizes or min(*sizes, args.queries, args.query_repeats, args.reps) < 1:
        ap.error("cases/sizes/queries/repeats must be positive")
    if ks and min(ks) < 1:
        ap.error("checkpoint sizes must be positive")

    args.out.mkdir(parents=True, exist_ok=True)

    # Exact (width,bits) parity before measurement.
    for case in cases:
        cs = candidates_for(case, ks, explicit)
        for count in sizes:
            checksums = {}
            for candidate in cs:
                fact = run_native(
                    args.binary, case, candidate, "query", count,
                    min(args.queries, 4096), 1,
                )
                checksums[candidate] = fact["checksum"]
            if len(set(checksums.values())) != 1:
                raise RuntimeError(f"{case}/{count}: parity failed: {checksums}")
            print(f"[verify] {case}/{count}: {next(iter(checksums.values()))}")

    grouped = defaultdict(list)
    raw = []
    for rep in range(1, args.reps + 1):
        for case in cases:
            cs = candidates_for(case, ks, explicit)
            for count in sizes:
                base = cachegrind(
                    args.binary, case, "u32", "prepare-payload",
                    count, args.queries, args.query_repeats,
                )
                raw.append((case, count, "payload", "prepare-payload", rep, *base))
                key = (case, count, "payload")
                for field, value in zip(("i_refs","d1_misses","lld_misses"), base):
                    grouped[(key, "prepare-payload", field)].append(value)

                for candidate in cs:
                    key = (case, count, candidate)
                    for mode in ("prepare", "query"):
                        counters = cachegrind(
                            args.binary, case, candidate, mode,
                            count, args.queries, args.query_repeats,
                        )
                        raw.append((case, count, candidate, mode, rep, *counters))
                        for field, value in zip(("i_refs","d1_misses","lld_misses"), counters):
                            grouped[(key, mode, field)].append(value)
        print(f"[measure] repetition {rep}/{args.reps}")

    rows = []
    for case in cases:
        cs = candidates_for(case, ks, explicit)
        for count in sizes:
            base_key = (case, count, "payload")
            base_i = grouped[(base_key, "prepare-payload", "i_refs")]
            cache_query_i = None
            cache_prepare_i_per_word = None
            temporary = []
            for candidate in cs:
                fact = run_native(
                    args.binary, case, candidate, "query",
                    count, args.queries, args.query_repeats,
                )
                key = (case, count, candidate)
                prep_i_values = grouped[(key, "prepare", "i_refs")]
                prep_i = max(
                    0.0,
                    median([x - y for x, y in zip(prep_i_values, base_i)])
                )
                query_i = paired(grouped, key, "query", "prepare", "i_refs")
                query_d1 = paired(grouped, key, "query", "prepare", "d1_misses")
                query_lld = paired(grouped, key, "query", "prepare", "lld_misses")
                ops = args.queries * args.query_repeats
                row = {
                    "case": case,
                    "words": count,
                    "candidate": candidate,
                    "packed_bytes": int(fact["packed_bytes"]),
                    "metadata_bytes": int(fact["metadata_bytes"]),
                    "active_bytes": int(fact["active_bytes"]),
                    "active_bytes_per_word": int(fact["active_bytes"]) / count,
                    "prepare_i_per_word": prep_i / count,
                    "query_i_per_access": query_i / ops,
                    "d1_misses_per_1k": query_d1 * 1000.0 / ops,
                    "lld_misses_per_1k": query_lld * 1000.0 / ops,
                    "local_width_steps_per_access": int(fact["local_steps"]) / ops,
                }
                if candidate == "cache2":
                    cache_query_i = row["query_i_per_access"]
                    cache_prepare_i_per_word = row["prepare_i_per_word"]
                temporary.append(row)
            if cache_query_i is None or cache_prepare_i_per_word is None:
                cache_query_i = math.nan
                cache_prepare_i_per_word = math.nan
            for row in temporary:
                row["query_slowdown_vs_cache2"] = (
                    row["query_i_per_access"] / cache_query_i
                    if cache_query_i and not math.isnan(cache_query_i) else math.nan
                )
                if row["candidate"] == "cache2":
                    crossover = 0.0
                else:
                    candidate_prepare = row["prepare_i_per_word"] * count
                    cache_prepare = cache_prepare_i_per_word * count
                    candidate_query = row["query_i_per_access"]
                    denominator = candidate_query - cache_query_i
                    numerator = cache_prepare - candidate_prepare
                    if denominator > 0 and numerator > 0:
                        crossover = numerator / denominator
                    elif denominator <= 0 and candidate_prepare <= cache_prepare:
                        crossover = math.inf
                    else:
                        crossover = 0.0
                row["cache2_crossover_accesses"] = crossover
                row["cache2_crossover_accesses_per_word"] = (
                    crossover / count if not math.isinf(crossover) else math.inf
                )
                rows.append(row)

    add_pareto(rows)

    with (args.out / "raw.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(
            ["case","words","candidate","mode","rep","i_refs","d1_misses","lld_misses"]
        )
        writer.writerows(raw)

    fields = list(rows[0].keys())
    with (args.out / "summary.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    environment = {
        "git_sha": subprocess.run(
            ["git","rev-parse","HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cases": list(cases),
        "sizes": list(sizes),
        "ks": list(ks),
        "queries": args.queries,
        "query_repeats": args.query_repeats,
        "reps": args.reps,
        "rustc": subprocess.run(
            ["rustc","--version"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "valgrind": subprocess.run(
            ["valgrind","--version"], check=True, capture_output=True, text=True
        ).stdout.strip(),
    }
    (args.out / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Compact mixed-boundary index tournament — #2265",
        "",
        "Every candidate recovers exact (width,bits) on the same random query corpus before measurement.",
        "Query counters subtract the matching candidate preparation path.",
        "",
        "| case | words | candidate | active B/word | prep I/word | query I/access | "
        "vs cache2 | cache crossover access/word | width steps/access | D1 miss/1k | Pareto |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        crossover = row["cache2_crossover_accesses_per_word"]
        crossover_text = "never" if math.isinf(crossover) else f"{crossover:.3f}"
        lines.append(
            f"| {row['case']} | {row['words']:,} | {row['candidate']} | "
            f"{row['active_bytes_per_word']:.3f} | "
            f"{row['prepare_i_per_word']:.2f} | "
            f"{row['query_i_per_access']:.2f} | "
            f"x{row['query_slowdown_vs_cache2']:.2f} | "
            f"{crossover_text} | "
            f"{row['local_width_steps_per_access']:.2f} | "
            f"{row['d1_misses_per_1k']:.2f} | {row['pareto']} |"
        )
    lines += [
        "",
        "Candidate semantics:",
        "- formula: fixed-width negative control; no boundary metadata;",
        "- usize/u32: full per-word start-offset tables; width is inferred from adjacent offsets;",
        "- cp8-K: u32 checkpoint every K words + one-byte width stream;",
        "- cp2-K: D1-D4-only u32 checkpoint every K words + packed 2-bit (width-1) stream;",
        "- cp3-K: generic W1..W8 u32 checkpoint every K words + packed 3-bit (width-1) stream;",
        "- t2-K: D1-D4-only u32 checkpoint every K + one u8 local bit offset per word + packed 2-bit width stream; O(1) boundary recovery for K<=64;",
        "- sel-K: one boundary bit at each packed word start + u32 select checkpoint every K words; query uses bounded u64 popcount/select probes and derives width from the next boundary;",
        "- cache2: decoded exact hot cache storing one width byte + one raw byte per word; packed payload may be cold/discarded.",
        "",
        "Pareto means non-dominated on (active bytes, query I/access) only. No weighted score is used.",
        "Cache crossover is the random-access count per word where cache2's higher one-time preparation is repaid by its lower query I/access.",
        "A value below 1.0 means decode-to-cache becomes cheaper before one random lookup per logical word on average.",
        "No candidate is a framing or semantic authority.",
    ]
    report = "\n".join(lines) + "\n"
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
