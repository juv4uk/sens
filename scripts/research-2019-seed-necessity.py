#!/usr/bin/env python3
"""Validate 2019-seed-necessity.tsv foundational invariants."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SEEDS = {"000", "001", "010", "011", "100", "101", "110", "111"}


def main() -> int:
    path = Path("docs/research/2019-seed-necessity.tsv")
    if not path.is_file():
        print(f"missing {path}", file=sys.stderr)
        return 1
    rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
    ids = {r["seed"] for r in rows}
    if ids != SEEDS:
        print(f"seed set mismatch: {sorted(ids)} vs {sorted(SEEDS)}", file=sys.stderr)
        return 1
    errors = 0
    for r in rows:
        if r.get("status_lock") != "premise":
            print(f"{r['seed']}: status_lock must be premise", file=sys.stderr)
            errors += 1
        if r.get("independence_in_declared_graph") != "not_derived":
            # Current declared graphs do not derive seeds from seeds (#2031).
            print(f"{r['seed']}: unexpected independence flag", file=sys.stderr)
            errors += 1
    if errors:
        return 1
    print(f"OK: 8 seeds, all status_lock=premise, none marked derived in declared graph")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
