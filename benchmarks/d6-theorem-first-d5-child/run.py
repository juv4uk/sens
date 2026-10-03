#!/usr/bin/env python3
"""#2701 theorem-first D5 -> D6 one-delta search.

This witness asks a semantic question, not an occupancy question:

    Does the current generator-backed D5 population contain any semantic
    parent whose newly observed same-base + exactly-one-delta child is not
    already explained by an admitted generator law?

OD-005 owner residency is 32/32.  Residency alone does not create a generator
edge; historical residents require their own same-domain theorem before they
become parents in this search.

Current expected result:
    NO-NEW-D5-ONE-DELTA-CHILD

The selector family is a positive control.  Every generator-backed D5 selector
has exactly two generated D6 selector children under the same extension law.
The other 24 OD-005 D5 residents remain historical residents here, not implicit
generator parents.
"""

from __future__ import annotations

import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D5_MAP = ROOT / "benchmarks" / "d5-closure-map" / "run.py"
D6_MAP = ROOT / "benchmarks" / "d6-closure-map" / "run.py"
D5_ELIGIBILITY = ROOT / "benchmarks" / "d5-sens-derivation-closeout" / "factor-eligibility.json"


def load_rows(script: Path) -> list[dict]:
    ns = runpy.run_path(str(script))
    return ns["build_map"]()


def main() -> int:
    d5_rows = load_rows(D5_MAP)
    d6_rows = load_rows(D6_MAP)
    eligibility = json.loads(D5_ELIGIBILITY.read_text(encoding="utf-8"))

    d5_owner_residents = [r for r in d5_rows if r.get("residency") == "YES"]
    d5_members = [r for r in d5_rows if r["status"] == "generated"]
    d5_owner_historical = [r for r in d5_rows if r["status"] == "owner-historical"]

    # D6 closure-map is still a generator/derivability artifact in this lane.
    # Select generator-backed children explicitly so OD-006 full residency can
    # migrate independently under #2764.
    d6_members = [r for r in d6_rows if r["status"] == "generated"]

    assert len(d5_owner_residents) == 32, (
        f"expected 32 OD-005 owner residents, got {len(d5_owner_residents)}"
    )
    assert len(d5_members) == 8, f"expected 8 D5 generator parents, got {len(d5_members)}"
    assert len(d5_owner_historical) == 24, (
        f"expected 24 owner-historical D5 residents, got {len(d5_owner_historical)}"
    )
    assert len(d6_members) == 16, f"expected 16 generated D6 selector children, got {len(d6_members)}"

    assert all(r["semantic_family"] == "selector" for r in d5_members)
    assert all(r.get("residency") == "YES" for r in d5_owner_historical)

    expected_children = {
        parent["coordinate"] + bit
        for parent in d5_members
        for bit in ("0", "1")
    }
    actual_d6 = {r["coordinate"] for r in d6_members}

    assert expected_children == actual_d6, (
        "current D5 selector members do not generate exactly the current D6 selector closure: "
        f"missing={sorted(expected_children-actual_d6)} "
        f"extra={sorted(actual_d6-expected_children)}"
    )

    for child in d6_members:
        parent = child["coordinate"][:-1]
        parent_row = next(r for r in d5_members if r["coordinate"] == parent)
        assert parent_row["semantic_family"] == child["semantic_family"] == "selector"
        assert child["semantic_law"] == parent_row["semantic_law"]
        assert child["semantic_law_authority"] == parent_row["semantic_law_authority"]

    yes_rows = [
        row for row in eligibility["factors"]
        if row.get("d5_eligible") == "YES"
    ]
    assert not yes_rows, f"new D5-eligible factors exist and require D6 child analysis: {yes_rows}"

    # Owner-historical residency is not free capacity and not automatic theorem
    # parenthood.  It remains visible without being fed into this selector law.
    assert not any(r["status"] == "UNKNOWN/free" for r in d5_rows)

    print("D6-THEOREM-FIRST-D5-CHILD=PASS")
    print(f"d5-owner-residents={len(d5_owner_residents)}")
    print(f"d5-generator-parents={len(d5_members)}")
    print(f"d5-owner-historical-nonparents={len(d5_owner_historical)}")
    print(f"known-d6-one-delta-children={len(actual_d6)}")
    print("unexplained-d6-one-delta-children=0")
    print("d5-unknown-current-occupancy=0")
    print("new-d5-eligible-factors=0")
    print("RESULT=NO-NEW-D5-ONE-DELTA-CHILD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
