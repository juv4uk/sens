#!/usr/bin/env python3
"""Guard #3955: D8 S2 geometry state.

Перевіряє лише research-геометрію. D8 не ратифікується.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "knowledge" / "d8-v2-geometry-state.json"
INVENTORY = ROOT / "knowledge" / "d8-v2-semantic-inventory.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise AssertionError(msg)


def main() -> int:
    state = load(STATE)
    inv = load(INVENTORY)

    req(state["schema"] == "d8-v2-geometry-state/v1", "schema drift")
    req(state["accounting"]["selected_meanings"] == 256, "selected count drift")
    req(state["accounting"]["fixed_coordinate_meanings"] == 72, "fixed count drift")
    req(state["accounting"]["selector_fixed"] == 64, "selector fixed drift")
    req(state["accounting"]["product_invariant_fixed"] == 8, "product fixed drift")
    req(state["accounting"]["gauge_orbit_meanings"] == 7, "orbit count drift")
    req(state["accounting"]["fully_unplaced_meanings"] == 177, "unplaced count drift")
    req(state["accounting"]["free_coordinates_after_fixed"] == 184, "free coordinate drift")
    req(state["accounting"]["ratified_d8_residents"] == 0, "research state must not ratify D8")

    selected = {row["semantic_name"] for row in inv["rows"]}
    req(len(selected) == 256, "inventory is not 256 distinct meanings")

    fixed = state["fixed_assignments"]
    fixed_coords = {row["coordinate"] for row in fixed}
    fixed_names = {row["semantic_name"] for row in fixed}
    req(len(fixed) == 72, "fixed row count drift")
    req(len(fixed_coords) == 72, "fixed coordinate collision")
    req(len(fixed_names) == 72, "fixed semantic collision")
    req(fixed_names <= selected, "fixed semantic outside selected inventory")

    selector = [row for row in fixed if row["status"] == "LAW-FORCED-CANDIDATE"]
    req(len(selector) == 64, "selector fixed count drift")
    req(
        all(row["coordinate"].startswith(("011", "100")) for row in selector),
        "stale selector roots reappeared",
    )

    product = [
        row for row in fixed
        if row["status"] == "PRODUCT-INVARIANT-FIXED-CANDIDATE"
    ]
    req(len(product) == 8, "product fixed count drift")

    orbits = state["gauge_orbits"]
    req(len(orbits) == 7, "gauge orbit count drift")
    orbit_names = {row["semantic_name"] for row in orbits}
    req(len(orbit_names) == 7, "duplicate orbit semantic")
    req(orbit_names <= selected, "orbit semantic outside selected inventory")
    for row in orbits:
        coords = row["candidate_coordinates"]
        req(len(coords) == 2 and len(set(coords)) == 2, "malformed two-coordinate orbit")
        req(not (set(coords) & fixed_coords), "gauge orbit collides with fixed coordinate")

    unplaced = state["fully_unplaced_meanings"]
    unplaced_names = {row["semantic_name"] for row in unplaced}
    req(len(unplaced_names) == 177, "unplaced semantic count drift")

    req(not (fixed_names & orbit_names), "fixed/orbit semantic overlap")
    req(not (fixed_names & unplaced_names), "fixed/unplaced semantic overlap")
    req(not (orbit_names & unplaced_names), "orbit/unplaced semantic overlap")
    req(fixed_names | orbit_names | unplaced_names == selected, "selected inventory not fully partitioned")

    free = state["free_coordinates_after_fixed"]
    req(len(free) == 184 and len(set(free)) == 184, "free coordinate set drift")
    req(not (set(free) & fixed_coords), "fixed coordinate listed as free")

    print("D8-V2-GEOMETRY-S2=PASS")
    print("fixed=72")
    print("selector-fixed=64")
    print("product-fixed=8")
    print("gauge-orbit-meanings=7")
    print("fully-unplaced=177")
    print("free-coordinates=184")
    print("ratified-d8=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
