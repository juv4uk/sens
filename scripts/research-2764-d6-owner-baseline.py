#!/usr/bin/env python3
"""#2764 — standing guard for the current owner-ratified Core D6 baseline.

OD-006 / merged #2753 supersedes the earlier sparse 16+48 occupancy model.

Canonical input:
    knowledge/d6-historical-full-map.json

This guard validates owner occupancy only.  Semantic derivability belongs to
#2765 and runtime executability belongs to #2766.

Pre-OD006 sparse closure/frontier experiments remain historical evidence, not
current occupancy authority.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
FULL_MAP = REPO / "knowledge" / "d6-historical-full-map.json"

WIDTH = 6
CAPACITY = 1 << WIDTH
ALL_COORDS = {format(i, "06b") for i in range(CAPACITY)}
ALL_PARENTS = {format(i, "05b") for i in range(1 << 5)}
SELECTORS = {
    format(i, "06b")
    for i in range(int("101000", 2), int("101111", 2) + 1)
} | {
    format(i, "06b")
    for i in range(int("110000", 2), int("110111", 2) + 1)
}

EXPECTED_STATUS_COUNTS = {
    "selector": 16,
    "arithmetic": 8,
    "predicate": 8,
    "physical_mutation_and_state": 4,
    "binding_and_loops": 4,
    "control_and_unwind": 4,
    "abstraction_and_macro": 4,
    "system_and_special": 4,
    "list_and_sets": 8,
    "tree_and_higher_order": 4,
    "total": 64,
    "unallocated": 0,
}


def fail(message: str) -> None:
    raise AssertionError(f"D6 OD-006 baseline drift: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_map() -> dict[str, Any]:
    return json.loads(FULL_MAP.read_text(encoding="utf-8"))


def build_result() -> dict[str, Any]:
    data = load_map()

    require(data["schema"] == "d6-historical-full-map/v1", "schema")
    require(data["domain"] == "Core.D6", "domain")
    require(data["width"] == WIDTH, "width")
    require(data["capacity"] == CAPACITY, "capacity")
    require(
        data["authority"] == "owner-directive-2026-10-03",
        "owner authority",
    )
    require(
        data["status_counts"] == EXPECTED_STATUS_COUNTS,
        f"declared status counts drifted: {data['status_counts']}",
    )

    rows = data["coordinates"]
    require(len(rows) == CAPACITY, f"expected {CAPACITY} rows, got {len(rows)}")

    coords = [row["coordinate"] for row in rows]
    require(len(set(coords)) == CAPACITY, "duplicate coordinate")
    require(set(coords) == ALL_COORDS, "coordinate coverage is not exact 000000..111111")

    by_parent: dict[str, list[str]] = defaultdict(list)
    selector_coords: set[str] = set()

    for row in rows:
        coord = row["coordinate"]
        parent = row["parent_d5"]

        require(
            isinstance(coord, str)
            and len(coord) == WIDTH
            and set(coord) <= {"0", "1"},
            f"{coord!r}: not exact 6-bit coordinate",
        )
        require(
            isinstance(parent, str)
            and len(parent) == 5
            and set(parent) <= {"0", "1"},
            f"{coord}: invalid D5 parent {parent!r}",
        )
        require(coord[:5] == parent, f"{coord}: parent-prefix mismatch {parent}")
        require(
            coord == parent + coord[-1],
            f"{coord}: not exact one-bit extension of {parent}",
        )
        require(row.get("name"), f"{coord}: missing projection name")
        require(row.get("category"), f"{coord}: missing category")
        require(row.get("behavior"), f"{coord}: missing behavior")
        require(row.get("provenance"), f"{coord}: missing historical provenance")

        by_parent[parent].append(coord)
        if row["category"] == "selector":
            selector_coords.add(coord)

    require(set(by_parent) == ALL_PARENTS, "not all D5 parents represented")
    for parent in sorted(ALL_PARENTS):
        children = sorted(by_parent[parent])
        require(
            children == [parent + "0", parent + "1"],
            f"{parent}: expected P0/P1, got {children}",
        )

    require(
        selector_coords == SELECTORS,
        f"selector coordinates drifted: {sorted(selector_coords)}",
    )
    require(len(selector_coords) == 16, "selector count is not 16")

    # The selector subfamily must be exactly the two canonical D3 selector
    # roots extended through three D5 suffix bits plus one D6 suffix bit.
    require(
        all(coord.startswith(("101", "110")) for coord in selector_coords),
        "selector family escaped canonical 101/110 roots",
    )

    return {
        "schema": "d6-owner-baseline-guard/v1",
        "authority": "#2753/OD-006",
        "domain": "Core.D6",
        "width": WIDTH,
        "capacity": CAPACITY,
        "resident_count": len(rows),
        "unallocated_count": 0,
        "unique_coordinate_count": len(set(coords)),
        "d5_parent_count": len(by_parent),
        "children_per_d5_parent": 2,
        "parent_extension_law": "child = parent_d5 || one_suffix_bit",
        "selector_coordinates": sorted(selector_coords),
        "selector_count": len(selector_coords),
        "historical_nonselector_count": len(rows) - len(selector_coords),
        "status_counts": EXPECTED_STATUS_COUNTS,
        "legacy_sparse_16_plus_48_current_authority": False,
        "legacy_pure_unknown_current_authority": False,
        "former_setq_001111_current_claim": False,
        "coordinate_001111_owner_name": next(
            row["name"] for row in rows if row["coordinate"] == "001111"
        ),
        "semantic_derivability_owned_elsewhere": "#2765",
        "runtime_executability_owned_elsewhere": "#2766",
        "core_math_occupancy_donation": False,
        "status": "PASS",
        "non_conclusions": [
            "owner residency does not imply semantic irreducibility",
            "owner residency does not imply runtime executable support",
            "selector generation evidence remains valid for the selector subfamily",
            "pre-OD006 UNKNOWN/PURE-UNKNOWN experiments remain historical evidence",
            "same width or same bits in another domain do not confer Core D6 meaning",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    result = build_result()
    require(
        result["coordinate_001111_owner_name"] == "DEFVAR",
        "001111 must be DEFVAR under OD-006",
    )

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(payload, end="")

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
