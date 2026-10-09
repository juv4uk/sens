#!/usr/bin/env python3
"""#2763 — current owner-ratified Core D5 baseline.

OD-005 changed occupancy policy from the former sparse selector closure to a
full 32/32 historical Core projection.

This guard deliberately keeps two axes separate:

    residency  = owner-ratified exact D5 coordinate
    derivation = whether SENS can reproduce the behavior from lower domains

A resident may therefore still be DERIVED/HISTORICAL-MECHANISM in semantic
research.  This script does not erase or reinterpret those proofs.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
SELECTOR_CLOSURE = ROOT / "benchmarks" / "d5-closure-map" / "run.py"

WIDTH = 5
CAPACITY = 1 << WIDTH
OD005 = "#2538/OD-005"
OD005_MERGE = "8d6341d5b4b4cfb54cc05e74f80752c1943b17a0"

EXPECTED_SELECTORS = {
    "10100": "CAAAR",
    "10101": "CAADR",
    "10110": "CADAR",
    "10111": "CADDR",
    "11000": "CDAAR",
    "11001": "CDADR",
    "11010": "CDDAR",
    "11011": "CDDDR",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(f"OD-005 D5 baseline drift: {message}")


def load_owner_map() -> dict[str, Any]:
    return json.loads(OWNER_MAP.read_text(encoding="utf-8"))


def build_result() -> dict[str, Any]:
    data = load_owner_map()
    rows = data["coordinates"]

    require(data["width"] == WIDTH, "width != 5")
    require(data["capacity"] == CAPACITY, "capacity != 32")
    require(data["status_counts"]["total"] == CAPACITY, "owner map total != 32")
    require(data["status_counts"]["unallocated"] == 0, "owner map has unallocated rows")
    require(data["authority"] == "owner-directive-2026-10-03", "authority drift")

    coordinates = [row["coordinate"] for row in rows]
    names = [row["name"] for row in rows]
    exact = {f"{value:05b}" for value in range(CAPACITY)}

    require(len(rows) == CAPACITY, f"row count={len(rows)}")
    require(set(coordinates) == exact, "coordinate coverage is not exact")
    require(len(coordinates) == len(set(coordinates)), "duplicate coordinate")
    require(len(names) == len(set(names)), "duplicate resident name")

    by_coord = {row["coordinate"]: row for row in rows}
    for coordinate, row in by_coord.items():
        require(row["parent_d4"] == coordinate[:-1],
                f"{coordinate}: D4 parent-prefix drift")

    # The old sparse closure remains a positive-control theorem for the eight
    # selector-generated residents.  It no longer decides total occupancy.
    closure = runpy.run_path(str(SELECTOR_CLOSURE))
    generated_rows = closure["selector_rows"]()
    require(set(generated_rows) == set(EXPECTED_SELECTORS),
            "selector generator coordinate set drift")

    for coordinate, expected_name in EXPECTED_SELECTORS.items():
        generated = generated_rows[coordinate]
        owner = by_coord[coordinate]
        require(generated["display_name"] == expected_name,
                f"{coordinate}: selector generator name drift")
        require(owner["name"] == expected_name,
                f"{coordinate}: owner map disagrees with selector generator")
        require(owner["category"] == "selector",
                f"{coordinate}: selector category drift")
        require(generated["certificate_replay_ok"] is True,
                f"{coordinate}: selector certificate does not replay")

    historical_nonselectors = sorted(exact - set(EXPECTED_SELECTORS))
    require(len(historical_nonselectors) == 24,
            "expected exactly 24 non-selector historical residents")

    result_rows = []
    for coordinate in sorted(exact):
        owner = by_coord[coordinate]
        selector_generated = coordinate in EXPECTED_SELECTORS
        result_rows.append({
            "coordinate": coordinate,
            "name": owner["name"],
            "parent_d4": owner["parent_d4"],
            "category": owner["category"],
            "historical_provenance": owner["provenance"],
            "resident": True,
            "residency_kind": (
                "selector-generated"
                if selector_generated
                else "owner-historical"
            ),
            "residency_authority": (
                "#2158 + OD-005"
                if selector_generated
                else OD005
            ),
            "semantic_derivability": "SEPARATE-AXIS",
        })

    return {
        "schema": "od005-d5-ratified-baseline/v2",
        "authority": OD005,
        "ratification_merge": OD005_MERGE,
        "domain": "Core D5",
        "width": WIDTH,
        "capacity": CAPACITY,
        "occupied": CAPACITY,
        "unknown": 0,
        "selector_generated": len(EXPECTED_SELECTORS),
        "owner_historical_nonselector": len(historical_nonselectors),
        # Compatibility field for consumers that previously called these
        # "manual"; semantic meaning is now owner-historical residency.
        "manual_nonselector_count": len(historical_nonselectors),
        "pre_od005_sparse_model": {
            "status": "ARCHIVED-STRUCTURAL-EVIDENCE",
            "selector_generated": 8,
            "unknown": 24,
            "authority_period": "before OD-005 2026-10-03",
            "artifact": "benchmarks/d5-closure-map/run.py",
        },
        "residency_implies_irreducible": False,
        "derivability_tracked_separately": True,
        "rows": result_rows,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = build_result()

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print("OD005-D5-RATIFIED-BASELINE=PASS")
    print("width=5")
    print("capacity=32")
    print("occupied=32")
    print("unknown=0")
    print("selector-generated=8")
    print("owner-historical-nonselector=24")
    print("residency-implies-irreducible=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
