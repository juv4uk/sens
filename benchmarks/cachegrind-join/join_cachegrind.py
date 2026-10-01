#!/usr/bin/env python3
"""#2045 [BENCH][CACHEGRIND-JOIN-1] — join pinned-environment instruction counts
onto benchmark-lane raw rows by `case_id`.

Benchmark-only tooling. It never invents a number: it only merges a measurement
file into lane rows, leaves absent fields blank, and reports exactly what did
and did not match.

Measurement file format (tab-separated, header required)
--------------------------------------------------------
    case_id <TAB> i_refs [<TAB> cpu <TAB> valgrind_version <TAB> guix_channels_sha
                          <TAB> git_sha <TAB> machine_insts <TAB> code_bytes ...]

`case_id` (alias `key` or `case`) is mandatory; every other column is optional
and is copied through into the joined output when it names a schema column.
A row counts as **provenance-complete** only when `cpu`, `valgrind_version`,
`guix_channels_sha` and `git_sha` are all non-empty (#1987 requires provenance
for any cross-run comparison); otherwise it is marked `provenance-incomplete`.

Usage
-----
    join_cachegrind.py --lane LANE.tsv [--lane ...] \
        --measurements M.tsv --out JOINED.tsv [--require-all]

    join_cachegrind.py --lane LANE.tsv --make-synthetic-example OUT.tsv

`--make-synthetic-example` writes a clearly-labelled *synthetic* measurement
file from a lane's case_ids, so the join is demonstrable and reproducible. It
is NOT evidence and must never be cited as a measurement.
"""

from __future__ import annotations

import argparse
import csv
import sys

# canonical #1987 column order (raw rows are primary evidence)
SCHEMA_1987 = [
    "case_id", "candidate", "family", "semantic_depth", "mode", "rep", "i_refs",
    "tree_steps", "root_selections", "bits_consumed", "generator_apps",
    "registry_lookups", "residue_lookups", "cache_hits", "cache_misses",
    "allocations", "allocated_bytes", "object_bytes", "wire_bits",
    "compiler_phase", "machine_insts", "code_bytes", "loads", "stores",
    "branches", "calls", "spills", "corpus_sha", "binary_sha", "git_sha",
    "guix_channels_sha", "cpu", "valgrind_version",
]

PROVENANCE = ["cpu", "valgrind_version", "guix_channels_sha", "git_sha"]
CASE_ALIASES = ["case_id", "key", "case"]


def read_tsv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        raise SystemExit(f"empty table: {path}")
    return rows


def case_column(fieldnames):
    for alias in CASE_ALIASES:
        if alias in fieldnames:
            return alias
    raise SystemExit(f"no case id column (tried {CASE_ALIASES}) in {fieldnames}")


def load_measurements(path):
    rows = read_tsv(path)
    key = case_column(rows[0].keys())
    out = {}
    for r in rows:
        cid = (r.get(key) or "").strip()
        if not cid:
            continue
        out[cid] = {k: (v or "").strip() for k, v in r.items() if k != key}
    return out


def make_synthetic(lane_path, out_path):
    rows = read_tsv(lane_path)
    key = case_column(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["case_id", "i_refs", "cpu", "valgrind_version",
                    "guix_channels_sha", "git_sha", "note"])
        for i, r in enumerate(rows):
            cid = r[key]
            # deterministic pseudo values; explicitly NOT measurements
            w.writerow([cid, str(1000 + (i * 37) % 500), "SYNTHETIC-cpu",
                        "SYNTHETIC-valgrind", "SYNTHETIC-guix", "SYNTHETIC-git",
                        "synthetic-not-evidence"])
    print(f"wrote synthetic example ({len(rows)} rows) -> {out_path}")


def join(lanes, measurements, out_path, require_all):
    joined = []
    used = set()
    stats = {"lane_rows": 0, "matched": 0, "unmatched": 0, "incomplete": 0}
    for lane_path in lanes:
        rows = read_tsv(lane_path)
        lane_cols = list(rows[0].keys())
        for r in rows:
            stats["lane_rows"] += 1
            cid = (r.get("case_id") or "").strip()
            meas = measurements.get(cid)
            if meas is None:
                r["join_status"] = "unmatched-measurement"
                stats["unmatched"] += 1
            else:
                used.add(cid)
                for col in SCHEMA_1987:
                    if col in meas and meas[col] != "":
                        r[col] = meas[col]
                complete = all(meas.get(p, "") for p in PROVENANCE)
                r["join_status"] = "matched" if complete else "provenance-incomplete"
                stats["matched"] += 1
                if not complete:
                    stats["incomplete"] += 1
            joined.append(r)

    orphans = sorted(set(measurements) - used)
    cols = [c for c in SCHEMA_1987 if any(c in r for r in joined)]
    extra = [c for c in joined[0].keys() if c not in cols and c != "join_status"]
    cols = cols + extra + ["join_status"]
    # keep every lane column that exists in any row
    for r in joined:
        for c in r:
            if c not in cols:
                cols.append(c)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in joined:
            w.writerow(r)

    print(f"lane rows:      {stats['lane_rows']}")
    print(f"matched:        {stats['matched']}  (provenance-incomplete: {stats['incomplete']})")
    print(f"unmatched:      {stats['unmatched']}")
    print(f"orphan measure: {len(orphans)}")
    if orphans:
        for cid in orphans[:10]:
            print(f"   orphan: {cid}")
    print(f"joined -> {out_path}")

    if require_all and stats["unmatched"]:
        print("FAIL (--require-all): some lane rows have no measurement", file=sys.stderr)
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", action="append", default=[], required=True)
    ap.add_argument("--measurements")
    ap.add_argument("--out", default="joined.tsv")
    ap.add_argument("--require-all", action="store_true")
    ap.add_argument("--make-synthetic-example")
    args = ap.parse_args()

    if args.make_synthetic_example:
        make_synthetic(args.lane[0], args.make_synthetic_example)
        return 0
    if not args.measurements:
        print("--measurements is required (or use --make-synthetic-example)", file=sys.stderr)
        return 2
    measurements = load_measurements(args.measurements)
    return join(args.lane, measurements, args.out, args.require_all)


if __name__ == "__main__":
    sys.exit(main())
