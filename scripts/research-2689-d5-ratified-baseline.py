#!/usr/bin/env python3
"""Standing guard for the current owner-ratified Core D5 baseline.

OD-005 / merged #2750 supersedes the earlier sparse 8+24 occupancy model.

Canonical input:
    knowledge/d5-historical-full-map.json

This guard validates the owner baseline as binary-domain structure. Historical
selector-closure research remains useful evidence, but is not occupancy
authority after OD-005.

No D6 state is changed here.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
FULL_MAP = REPO / "knowledge" / "d5-historical-full-map.json"

WIDTH = 5
CAPACITY = 1 << WIDTH
ALL_COORDS = {format(i, "05b") for i in range(CAPACITY)}
ALL_PARENTS = {format(i, "04b") for i in range(1 << 4)}
SELECTORS = {
    "10100", "10101", "10110", "10111",
    "11000", "11001", "11010", "11011",
}

EXPECTED_STATUS_COUNTS = {
    "selector": 8,
    "arithmetic": 4,
    "predicate": 4,
    "state_and_control": 4,
    "evaluation_and_abstraction": 6,
    "list_and_tree_structure": 6,
    "total": 32,
    "unallocated": 0,
}

# OD-005 owner groups are coarser than each row's descriptive category.
# Validate them by exact binary coordinates rather than guessing from names.
EXPECTED_GROUPS = {
    "evaluation_and_abstraction": {
        "00000", "00001", "00010", "00011", "00100", "00101",
    },
    "state_and_control": {
        "00110", "00111", "01100", "01101",
    },
    "predicate": {
        "01000", "01001", "01110", "01111",
    },
    "arithmetic": {
        "01010", "01011", "10010", "10011",
    },
    "selector": SELECTORS,
    "list_and_tree_structure": {
        "10000", "10001", "11100", "11101", "11110", "11111",
    },
}


def fail(message: str) -> None:
    raise AssertionError(f"D5 OD-005 baseline drift: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load_map() -> dict[str, Any]:
    return json.loads(FULL_MAP.read_text(encoding="utf-8"))



def build_result() -> dict[str, Any]:
    data = load_map()

    require(data["schema"] == "d5-historical-full-map/v1", "schema")
    require(data["domain"] == "Core.D5", "domain")
    require(data["width"] == WIDTH, "width")
    require(data["capacity"] == CAPACITY, "capacity")
    require(
        data["authority"] == "owner-directive-2026-10-03",
        "owner authority",
    )

    rows = data["coordinates"]
    require(len(rows) == CAPACITY, f"expected 32 rows, got {len(rows)}")

    coords = [row["coordinate"] for row in rows]
    require(len(set(coords)) == CAPACITY, "duplicate coordinate")
    require(set(coords) == ALL_COORDS, "coordinate coverage is not exact 00000..11111")

    by_parent: dict[str, list[str]] = defaultdict(list)
    selector_coords = set()

    for row in rows:
        coord = row["coordinate"]
        parent = row["parent_d4"]

        require(
            isinstance(coord, str)
            and len(coord) == WIDTH
            and set(coord) <= {"0", "1"},
            f"{coord!r}: not exact 5-bit coordinate",
        )
        require(
            isinstance(parent, str)
            and len(parent) == 4
            and set(parent) <= {"0", "1"},
            f"{coord}: invalid D4 parent {parent!r}",
        )
        require(
            coord[:4] == parent,
            f"{coord}: parent-prefix mismatch {parent}",
        )
        require(
            coord == parent + coord[-1],
            f"{coord}: not exact one-bit extension of {parent}",
        )
        require(row.get("name"), f"{coord}: missing projection name")
        require(row.get("behavior"), f"{coord}: missing behavior")
        require(row.get("provenance"), f"{coord}: missing historical provenance")

        by_parent[parent].append(coord)
        if row["category"] == "selector":
            selector_coords.add(coord)

    require(set(by_parent) == ALL_PARENTS, "not all D4 parents represented")
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

    # Owner status groups are exact coordinate partitions.
    group_union: set[str] = set()
    for group, expected_coords in EXPECTED_GROUPS.items():
        require(
            not (group_union & expected_coords),
            f"owner status groups overlap at {sorted(group_union & expected_coords)}",
        )
        group_union |= expected_coords
        require(
            len(expected_coords) == EXPECTED_STATUS_COUNTS[group],
            f"{group}: coordinate group count drift",
        )
    require(group_union == ALL_COORDS, "owner status groups do not partition D5")

    require(
        data["status_counts"] == EXPECTED_STATUS_COUNTS,
        f"declared status counts drifted: {data['status_counts']}",
    )

    return {
        "schema": "d5-owner-baseline-guard/v2",
        "authority": "#2750/OD-005",
        "domain": "Core.D5",
        "width": WIDTH,
        "capacity": CAPACITY,
        "resident_count": len(rows),
        "unallocated_count": 0,
        "unique_coordinate_count": len(set(coords)),
        "d4_parent_count": len(by_parent),
        "children_per_d4_parent": 2,
        "parent_extension_law": "child = parent_d4 || one_suffix_bit",
        "selector_coordinates": sorted(selector_coords),
        "selector_count": len(selector_coords),
        "historical_nonselector_count": len(rows) - len(selector_coords),
        "status_counts": EXPECTED_STATUS_COUNTS,
        "owner_coordinate_groups": {
            key: sorted(value)
            for key, value in sorted(EXPECTED_GROUPS.items())
        },
        "core_math_occupancy_donation": False,
        "d6_mutation": False,
        "legacy_sparse_baseline_authority": False,
        "status": "PASS",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    result = build_result()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.json_out:
        args.json_out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
