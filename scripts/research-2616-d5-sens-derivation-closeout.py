#!/usr/bin/env python3
"""#2616 — conservative D5 SENS-derivation eligibility validator.

Research-only. This script cannot allocate coordinates. It validates the
boundary between structural factors and D5 placement candidates.

A factor is D5-eligible only when all of these are explicit:
- exact 4-bit D4 same-base parent;
- exactly one independently witnessed semantic delta;
- not already D1-D4-derived;
- not a residue/root without parent;
- evidence + falsifier are present.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_CLASSIFICATIONS = {
    "DERIVED-D1-D4",
    "HISTORICAL-MECHANISM-ONLY",
    "ROOT-RESIDUE",
    "SAME-PARENT-ONE-DELTA",
    "SAME-PARENT-MULTI-DELTA",
    "NO-PROVED-SAME-BASE-PARENT",
    "UNKNOWN",
}
ALLOWED_ELIGIBILITY = {"YES", "NO", "UNKNOWN"}


def fail(message: str) -> None:
    raise SystemExit(f"D5-SENS-DERIVATION-CLOSEOUT=FAIL\n{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def exact_d4_parent(value: object) -> bool:
    return isinstance(value, str) and len(value) == 4 and set(value) <= {"0", "1"}


def validate_row(row: dict) -> None:
    fid = row["factor_id"]
    require(row["classification"] in ALLOWED_CLASSIFICATIONS, f"{fid}: bad classification")
    require(row["d5_eligible"] in ALLOWED_ELIGIBILITY, f"{fid}: bad eligibility")
    require(isinstance(row["evidence"], list) and row["evidence"], f"{fid}: missing evidence")
    require(bool(row["falsifier"].strip()), f"{fid}: missing falsifier")

    if row["d5_eligible"] == "YES":
        require(
            row["classification"] == "SAME-PARENT-ONE-DELTA",
            f"{fid}: YES requires SAME-PARENT-ONE-DELTA",
        )
        require(exact_d4_parent(row["strongest_same_base_parent"]), f"{fid}: YES needs exact D4 parent")
        require(row["delta_count"] == 1, f"{fid}: YES requires exactly one delta")
        require(row["root_theorem"] is False, f"{fid}: root theorem cannot itself justify D5 child")
        require(row["derivable_from_d1_d4"] is False, f"{fid}: derived factor cannot consume D5")
        require(row["cross_family_shortcuts_rejected"] is True, f"{fid}: cross-family shortcuts not closed")

    if row["classification"] == "SAME-PARENT-MULTI-DELTA":
        require(exact_d4_parent(row["strongest_same_base_parent"]), f"{fid}: multi-delta row needs D4 parent")
        require(isinstance(row["delta_count"], int) and row["delta_count"] >= 2, f"{fid}: multi-delta count <2")
        require(row["d5_eligible"] == "NO", f"{fid}: multi-delta factor cannot be D5 eligible")

    if row["classification"] == "ROOT-RESIDUE":
        require(row["root_theorem"] is True, f"{fid}: residue/root row missing root theorem")
        require(row["d5_eligible"] == "NO", f"{fid}: roothood does not imply D5 residency")

    if row["classification"] in {"DERIVED-D1-D4", "HISTORICAL-MECHANISM-ONLY"}:
        require(row["d5_eligible"] == "NO", f"{fid}: derived/historical-only row cannot consume D5")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ledger",
        nargs="?",
        default="benchmarks/d5-sens-derivation-closeout/factor-eligibility.json",
    )
    parser.add_argument("--summary-json", default="")
    args = parser.parse_args()

    data = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    require(data["schema"] == "d5-sens-derivation-closeout/v1", "wrong schema")
    require(data["phase"] == "SENS-DERIVATION", "wrong phase")
    require(data["domain"] == "Core.D5", "wrong domain")

    invariant = data["map_invariant"]
    require(invariant == {
        "capacity": 32,
        "selector_generated": 8,
        "unknown_free": 24,
        "manual_nonselector_residents": 0,
        "source": "#2510/#2414",
    }, "ratified D5 map invariant drifted")

    factors = data["factors"]
    require(len(factors) == 7, f"expected seven current factors, got {len(factors)}")
    ids = [row["factor_id"] for row in factors]
    require(len(ids) == len(set(ids)), "duplicate factor id")

    for row in factors:
        validate_row(row)

    for control in data["composite_controls"]:
        require(exact_d4_parent(control["parent"]), f"{control['control_id']}: bad D4 parent")
        require(control["delta_count"] >= 2, f"{control['control_id']}: expected multi-delta control")
        require(control["d5_eligible"] == "NO", f"{control['control_id']}: multi-delta control cannot enter D5")

    yes = [r["factor_id"] for r in factors if r["d5_eligible"] == "YES"]
    no = [r["factor_id"] for r in factors if r["d5_eligible"] == "NO"]
    unknown = [r["factor_id"] for r in factors if r["d5_eligible"] == "UNKNOWN"]

    # Current evidence snapshot. This is intentionally conservative and should
    # change only when a separate theorem supplies a one-delta D4 parent.
    require(yes == [], f"unexpected D5-eligible factor(s): {yes}")
    require(sorted(no) == ["non-local-exit", "shared-location-update"], f"proved-NO set drifted: {no}")
    require(len(unknown) == 5, f"expected five unresolved special-call factors, got {unknown}")

    summary = {
        "d5_eligible_yes": len(yes),
        "d5_eligible_no": len(no),
        "d5_eligible_unknown": len(unknown),
        "yes_factors": yes,
        "no_factors": no,
        "unknown_factors": unknown,
        "new_nonselector_d5_candidates": len(yes),
        "coordinates_allocated": 0,
        "ratified_d5_map_unchanged": True,
    }

    if args.summary_json:
        target = Path(args.summary_json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("D5-SENS-DERIVATION-CLOSEOUT=PASS")
    print(f"D5-ELIGIBLE-YES={len(yes)}")
    print(f"D5-ELIGIBLE-NO={len(no)}")
    print(f"D5-ELIGIBLE-UNKNOWN={len(unknown)}")
    print("NEW-NONSELECTOR-D5-CANDIDATES=0")
    print("COORDINATES-ALLOCATED=0")
    print("D5-MAP=8-GENERATED+24-UNKNOWN")


if __name__ == "__main__":
    main()
