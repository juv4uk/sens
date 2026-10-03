#!/usr/bin/env python3
"""OD-005 / OD-006 constitutional full-map guard.

Checks only owner-ratified occupancy/shape facts:
- exact width and capacity;
- complete coordinate coverage;
- unique names/coordinates;
- parent-prefix continuity;
- selector subtrees still agree with the admitted CAR/CDR generator law.

It deliberately does NOT claim historical residency implies semantic
irreducibility. Derivability is tracked separately under #2765.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D5_PATH = ROOT / "knowledge" / "d5-historical-full-map.json"
D6_PATH = ROOT / "knowledge" / "d6-historical-full-map.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def all_words(width: int) -> set[str]:
    return {f"{value:0{width}b}" for value in range(1 << width)}


def selector_name(word: str) -> str:
    """Derive composite CAR/CDR selector name for 101/110 descendants.

    101 = CAR => initial selector letter A
    110 = CDR => initial selector letter D
    each appended 0 => compose CAR (A)
    each appended 1 => compose CDR (D)
    """
    require(word.startswith(("101", "110")), f"not a selector descendant: {word}")
    letters = ("A" if word[:3] == "101" else "D")
    letters += "".join("A" if bit == "0" else "D" for bit in word[3:])
    return f"C{letters}R"


def check_map(data: dict, width: int, parent_key: str | None) -> dict[str, dict]:
    require(data["width"] == width, f"D{width} width drift")
    require(data["capacity"] == 1 << width, f"D{width} capacity drift")
    require(data["status_counts"]["total"] == 1 << width, f"D{width} total drift")
    require(data["status_counts"]["unallocated"] == 0, f"D{width} must be fully occupied")

    rows = data["coordinates"]
    require(len(rows) == 1 << width, f"D{width} row count drift")

    coords = [row["coordinate"] for row in rows]
    names = [row["name"] for row in rows]

    require(set(coords) == all_words(width), f"D{width} coordinate coverage is not exact")
    require(len(coords) == len(set(coords)), f"D{width} duplicate coordinate")
    require(len(names) == len(set(names)), f"D{width} duplicate resident name")
    require(all(len(word) == width and set(word) <= {"0", "1"} for word in coords),
            f"D{width} malformed binary coordinate")

    by_coord = {row["coordinate"]: row for row in rows}

    if parent_key is not None:
        for row in rows:
            require(
                row[parent_key] == row["coordinate"][:-1],
                f"{row['coordinate']} parent-prefix drift: "
                f"{row[parent_key]} != {row['coordinate'][:-1]}",
            )

    return by_coord


def check_selectors(by_coord: dict[str, dict], width: int, expected_count: int) -> None:
    selector_rows = [
        row
        for coord, row in by_coord.items()
        if coord.startswith(("101", "110"))
    ]
    require(len(selector_rows) == expected_count, f"D{width} selector count drift")

    for row in selector_rows:
        coord = row["coordinate"]
        expected = selector_name(coord)
        require(row["name"] == expected, f"{coord}: {row['name']} != generated {expected}")
        require(row["category"] == "selector", f"{coord}: selector category drift")


def main() -> None:
    d5 = load(D5_PATH)
    d6 = load(D6_PATH)

    require(d5["authority"] == "owner-directive-2026-10-03", "D5 owner authority drift")
    require(d6["authority"] == "owner-directive-2026-10-03", "D6 owner authority drift")

    d5_rows = check_map(d5, 5, "parent_d4")
    d6_rows = check_map(d6, 6, "parent_d5")

    # Every D4 word has exactly two D5 children; every D5 word has exactly two D6 children.
    d5_parent_counts = Counter(row["parent_d4"] for row in d5_rows.values())
    require(set(d5_parent_counts.values()) == {2} and len(d5_parent_counts) == 16,
            "D5 must contain exactly two children per D4 parent")

    d6_parent_counts = Counter(row["parent_d5"] for row in d6_rows.values())
    require(set(d6_parent_counts.values()) == {2} and len(d6_parent_counts) == 32,
            "D6 must contain exactly two children per D5 parent")
    require(set(d6_parent_counts) == set(d5_rows), "D6 parent set must equal full D5 map")

    # Preserve the strongest pre-existing generator theorem independently of owner fill.
    check_selectors(d5_rows, 5, 8)
    check_selectors(d6_rows, 6, 16)

    # Critical owner-map coordinates whose former sparse meaning is now superseded.
    require(d5_rows["00111"]["name"] == "SETQ", "OD-005 SETQ coordinate drift")
    require(d6_rows["001111"]["name"] == "DEFVAR", "OD-006 001111 coordinate drift")

    print("OD005-OD006-FULL-MAP-GUARD=PASS")
    print("D5 width=5 capacity=32 occupied=32 unknown=0")
    print("D6 width=6 capacity=64 occupied=64 unknown=0")
    print("D5 selector-generated compatibility=8/8")
    print("D6 selector-generated compatibility=16/16")
    print("D5:00111=SETQ")
    print("D6:001111=DEFVAR")
    print("NON-CONCLUSION: residency does not imply semantic irreducibility")


if __name__ == "__main__":
    main()
