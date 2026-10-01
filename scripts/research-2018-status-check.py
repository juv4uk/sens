#!/usr/bin/env python3
"""Validate docs/research/2018-epistemic-status.tsv against #2018 vocabulary."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ALLOWED = {
    "premise",
    "conjecture",
    "witness",
    "theorem",
    "falsified",
    "falsified_as_axiom",
    "falsified_as_policy",
    "unknown",
}

REQUIRED = {
    "claim_id",
    "statement",
    "status",
    "assumptions",
    "scope",
    "positive_witness",
    "attempted_falsifiers",
    "surviving_counterexamples",
    "upgrade_condition",
    "downgrade_condition",
    "refs",
}


def main() -> int:
    path = Path("docs/research/2018-epistemic-status.tsv")
    if not path.is_file():
        print(f"missing {path}", file=sys.stderr)
        return 1
    rows = list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))
    if not rows:
        print("empty status table", file=sys.stderr)
        return 1
    missing_cols = REQUIRED - set(rows[0].keys())
    if missing_cols:
        print(f"missing columns: {sorted(missing_cols)}", file=sys.stderr)
        return 1
    errors = 0
    bija = None
    for r in rows:
        st = (r.get("status") or "").strip()
        if st not in ALLOWED:
            print(f"{r['claim_id']}: illegal status {st!r}", file=sys.stderr)
            errors += 1
        if r["claim_id"] == "bija3-seed":
            bija = st
    if bija is None:
        print("bija3-seed row missing", file=sys.stderr)
        errors += 1
    elif bija != "premise":
        print(
            f"bija3-seed must be status=premise (got {bija!r}) — #2018 hard rule",
            file=sys.stderr,
        )
        errors += 1
    if errors:
        return 1
    print(f"OK: {len(rows)} claims, vocabulary legal, bija3-seed=premise")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
