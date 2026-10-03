#!/usr/bin/env python3
"""#2410 — D8 historical full-map constitutional guard.

Checks only facts that follow from the ratified D3-D6 occupancy rule plus the
already admitted D3 selector law:

- exact width and capacity;
- complete coordinate coverage, unique coordinates, unique resident names;
- `parent_d7` is the mechanical one-bit prefix;
- `parent_d6` is the lineage parent and the D6 parent set is the full D6 map;
- exactly four D8 children per D6 parent (two children per D7 prefix);
- all 64 selector coordinates are the CAR/CDR generator output and are exactly
  the children of the 16 D6 selector parents;
- every row carries a behaviour, a provenance and an evidence class;
- no resident name collides with the D5 or D6 maps;
- full occupancy (unallocated = 0);
- the D7 rung is really occupied by a different law, so crossing it is a fact
  and not an assumption.

It deliberately does NOT claim that historical residency implies semantic
irreducibility. Derivability is tracked separately under #2765. The 192
historical rows are an agent-derived chronological continuation, and the guard
labels them as such instead of promoting them to authority.
"""

from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D5_PATH = ROOT / "knowledge" / "d5-historical-full-map.json"
D6_PATH = ROOT / "knowledge" / "d6-historical-full-map.json"
D7_PATH = ROOT / "knowledge" / "d7-full-map.json"
D8_PATH = ROOT / "knowledge" / "d8-historical-full-map.json"

SELECTOR_ROOTS = ("101", "110")
SELECTOR_EVIDENCE = "generated-by-admitted-d3-selector-law-2322"
HISTORICAL_EVIDENCE = "agent-derived-historical-continuation"


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
    require(word.startswith(SELECTOR_ROOTS), f"not a selector descendant: {word}")
    letters = "A" if word[:3] == "101" else "D"
    letters += "".join("A" if bit == "0" else "D" for bit in word[3:])
    return f"C{letters}R"


def main() -> None:
    d5 = load(D5_PATH)
    d6 = load(D6_PATH)
    d7 = load(D7_PATH)
    d8 = load(D8_PATH)

    # --- shape ---------------------------------------------------------------
    require(d8["width"] == 8, "D8 width drift")
    require(d8["capacity"] == 1 << 8, "D8 capacity drift")
    require(d8["domain"] == "Core.D8", "D8 domain drift")
    require(d8["status_counts"]["total"] == 256, "D8 total drift")
    require(d8["status_counts"]["unallocated"] == 0, "D8 must be fully occupied")

    rows = d8["coordinates"]
    require(len(rows) == 256, f"D8 row count drift: {len(rows)}")

    coords = [row["coordinate"] for row in rows]
    names = [row["name"] for row in rows]
    require(set(coords) == all_words(8), "D8 coordinate coverage is not exact")
    require(len(coords) == len(set(coords)), "D8 duplicate coordinate")
    require(len(names) == len(set(names)), "D8 duplicate resident name")
    require(
        all(len(word) == 8 and set(word) <= {"0", "1"} for word in coords),
        "D8 malformed binary coordinate",
    )

    by_coord = {row["coordinate"]: row for row in rows}

    # --- lineage -------------------------------------------------------------
    for row in rows:
        coord = row["coordinate"]
        require(
            row["parent_d7"] == coord[:-1],
            f"{coord} mechanical parent_d7 drift: {row['parent_d7']} != {coord[:-1]}",
        )
        require(
            row["parent_d6"] == coord[:-2],
            f"{coord} lineage parent_d6 drift: {row['parent_d6']} != {coord[:-2]}",
        )

    d6_rows = {row["coordinate"]: row for row in d6["coordinates"]}
    parent_counts = Counter(row["parent_d6"] for row in rows)
    require(
        set(parent_counts.values()) == {4} and len(parent_counts) == 64,
        "D8 must contain exactly four children per D6 parent",
    )
    require(set(parent_counts) == set(d6_rows), "D8 parent set must equal the full D6 map")

    d7_parent_counts = Counter(row["parent_d7"] for row in rows)
    require(
        set(d7_parent_counts.values()) == {2} and len(d7_parent_counts) == 128,
        "D8 must contain exactly two children per D7 mechanical prefix",
    )

    for row in rows:
        parent = d6_rows[row["parent_d6"]]
        require(
            row["lineage_parent_name"] == parent["name"],
            f"{row['coordinate']} lineage parent name drift: "
            f"{row['lineage_parent_name']} != {parent['name']}",
        )

    # --- selector law --------------------------------------------------------
    d6_selectors = {c for c in d6_rows if c.startswith(SELECTOR_ROOTS)}
    selector_rows = [row for row in rows if row["coordinate"].startswith(SELECTOR_ROOTS)]
    require(len(selector_rows) == 64, f"D8 selector count drift: {len(selector_rows)}")

    for row in selector_rows:
        coord = row["coordinate"]
        expected = selector_name(coord)
        require(row["name"] == expected, f"{coord}: {row['name']} != generated {expected}")
        require(row["category"] == "selector", f"{coord}: selector category drift")
        require(row["evidence"] == SELECTOR_EVIDENCE, f"{coord}: selector evidence drift")
        require(
            row["parent_d6"] in d6_selectors,
            f"{coord}: selector must descend from a D6 selector parent",
        )
        require(
            len(row["name"]) == 8,
            f"{coord}: selector name depth drift: {row['name']}",
        )

    selector_parents = {row["parent_d6"] for row in selector_rows}
    require(
        selector_parents == d6_selectors,
        "every D6 selector parent must have exactly four selector children",
    )

    # --- cross-check against the independent #2322 forecast ------------------
    # The forecast is research-only accounting, so it is used here as an
    # independent second witness of the selector word set, never as an
    # allocation authority.
    spec = importlib.util.spec_from_file_location(
        "forecast_2322", ROOT / "scripts" / "research-2322-generative-domain-forecast.py"
    )
    forecast = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(forecast)
    forecast_words = set(forecast.selector_words(8))
    map_words = {row["coordinate"] for row in selector_rows}
    require(
        forecast_words == map_words,
        "D8 selector word set disagrees with the #2322 generator forecast: "
        f"{sorted(forecast_words ^ map_words)[:8]}",
    )

    # --- historical rows -----------------------------------------------------
    historical_rows = [
        row for row in rows if not row["coordinate"].startswith(SELECTOR_ROOTS)
    ]
    require(len(historical_rows) == 192, f"D8 historical count drift: {len(historical_rows)}")

    for row in rows:
        for field in ("name", "category", "behavior", "provenance", "evidence"):
            require(bool(row[field]), f"{row['coordinate']}: empty {field}")
        require(
            not row["coordinate"].startswith(SELECTOR_ROOTS)
            or row["category"] == "selector",
            f"{row['coordinate']}: selector coordinate must be a selector",
        )
        if not row["coordinate"].startswith(SELECTOR_ROOTS):
            require(
                row["evidence"] == HISTORICAL_EVIDENCE,
                f"{row['coordinate']}: historical evidence drift",
            )
            require(
                row["parent_d6"] not in d6_selectors,
                f"{row['coordinate']}: non-selector coordinate under a selector parent",
            )

    # --- cross-domain uniqueness --------------------------------------------
    earlier_names = {row["name"] for row in d5["coordinates"]}
    earlier_names |= {row["name"] for row in d6["coordinates"]}
    collisions = sorted(earlier_names & set(names))
    require(not collisions, f"D8 resident name collides with D5/D6: {collisions}")

    # --- the crossed D7 rung is a checked fact, not an assumption -----------
    require(d7["width"] == 7, "D7 width drift")
    occupancy_rule = d7.get("occupancy_rule", "")
    require(
        "NOT a one-bit extension of a parent domain" in occupancy_rule,
        "D7 no longer documents that it is not part of the D5/D6 rung; "
        "the D8 lineage decision must be revisited",
    )
    require(len(d7["coordinates"]) == 128, "D7 coordinate count drift")

    # --- evidence accounting -------------------------------------------------
    evidence_counts = Counter(row["evidence"] for row in rows)
    require(
        evidence_counts[SELECTOR_EVIDENCE] == 64,
        "selector evidence accounting drift",
    )
    require(
        evidence_counts[HISTORICAL_EVIDENCE] == 192,
        "historical evidence accounting drift",
    )

    category_counts = Counter(row["category"] for row in rows)
    require(
        category_counts["selector"] == 64,
        "selector status count drift",
    )

    print("D8-HISTORICAL-FULL-MAP-GUARD=PASS")
    print("D8 width=8 capacity=256 occupied=256 unknown=0")
    print("D8 lineage: parent_d6 = full D6 map (4 children each)")
    print("D8 mechanical: parent_d7 = one-bit prefix (2 children each)")
    print("D8 selector-generated compatibility=64/64")
    print("D8 selector parents = 16 D6 selector parents x 4 children")
    print("D8 selector word set == #2322 generator forecast (independent witness)")
    print("D8 historical continuation rows=192 (agent-derived, not ratified)")
    print("D8 resident names unique within D8 and against D5/D6")
    print("D7 rung crossed by fact: d7-full-map.json documents D7 is not a one-bit extension")
    print("NON-CONCLUSION: residency does not imply semantic irreducibility")
    print("NON-CONCLUSION: the 192 historical coordinates are an agent-derived")
    print("              chronological continuation, not an owner-ratified allocation")
    print("NON-CONCLUSION: this map is an occupancy claim, not language authority")


if __name__ == "__main__":
    main()