#!/usr/bin/env python3
"""Guard #3958: відтворюваний повний D8 S4 gauge representative.

Це research candidate, не owner-ratified D8 authority.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "knowledge" / "d8-v2-gauge-fixed-candidate.json"
GEOMETRY = ROOT / "knowledge" / "d8-v2-geometry-state.json"
INVENTORY = ROOT / "knowledge" / "d8-v2-semantic-inventory.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise AssertionError(msg)


def main() -> int:
    candidate = load(MAP)
    geometry = load(GEOMETRY)
    inventory = load(INVENTORY)

    req(candidate["schema"] == "d8-v2-gauge-fixed-candidate/v1", "schema drift")
    req(candidate["status"] == "RESEARCH-GAUGE-FIXED-CANDIDATE", "status drift")
    req(candidate["width"] == 8 and candidate["capacity"] == 256, "D8 shape drift")
    req(candidate["occupancy"] == 256, "candidate occupancy drift")
    req(candidate["ratified_residents"] == 0, "S4 candidate must not ratify D8")

    rows = candidate["rows"]
    req(len(rows) == 256, "expected 256 candidate rows")
    req(len({r["coordinate"] for r in rows}) == 256, "coordinate collision")
    req(len({r["stable_id"] for r in rows}) == 256, "stable-id collision")
    req(len({r["semantic_name"] for r in rows}) == 256, "semantic collision")
    req({r["coordinate"] for r in rows} == {f"{i:08b}" for i in range(256)}, "coordinate coverage drift")

    expected_basis = {
        "LAW-FORCED": 64,
        "PRODUCT-FIXED": 8,
        "GAUGE-ORIENTED": 7,
        "GAUGE-FIXED": 177,
    }
    req(candidate["basis_counts"] == expected_basis, f"basis drift: {candidate['basis_counts']}")

    inv_by_name = {r["semantic_name"]: r for r in inventory["rows"]}
    req(len(inv_by_name) == 256, "inventory name set drift")
    req({r["semantic_name"] for r in rows} == set(inv_by_name), "S4 map != semantic inventory")

    by_coord = {r["coordinate"]: r for r in rows}

    # Усі S2 fixed assignments мають пережити S4 без руху.
    for fixed in geometry["fixed_assignments"]:
        got = by_coord.get(fixed["coordinate"])
        req(got is not None, f"fixed coordinate lost: {fixed['coordinate']}")
        req(got["semantic_name"] == fixed["semantic_name"], f"fixed semantic moved: {fixed['semantic_name']}")

    # Кожний unresolved two-coordinate orbit орієнтується тільки канонічним
    # lexicographic tie-break, без semantic score.
    for orbit in geometry["gauge_orbits"]:
        expected_coord = sorted(orbit["candidate_coordinates"])[0]
        got = by_coord.get(expected_coord)
        req(got is not None, f"orbit coordinate absent: {expected_coord}")
        req(got["semantic_name"] == orbit["semantic_name"], f"orbit orientation drift: {orbit['semantic_name']}")
        req(got["basis"] == "GAUGE-ORIENTED", f"orbit basis drift: {orbit['semantic_name']}")

    # Перерахувати залишковий S4 zip незалежно від checked-in rows.
    fixed_coords = {r["coordinate"] for r in rows if r["basis"] in {"LAW-FORCED", "PRODUCT-FIXED", "GAUGE-ORIENTED"}}
    free = sorted({f"{i:08b}" for i in range(256)} - fixed_coords)
    unplaced = sorted(
        geometry["fully_unplaced_meanings"],
        key=lambda r: r["stable_id"],
    )
    req(len(free) == 177 and len(unplaced) == 177, "S4 residue shape drift")
    for coord, semantic in zip(free, unplaced):
        got = by_coord[coord]
        req(got["stable_id"] == semantic["stable_id"], f"S4 stable-id replay drift at {coord}")
        req(got["semantic_name"] == semantic["semantic_name"], f"S4 semantic replay drift at {coord}")
        req(got["basis"] == "GAUGE-FIXED", f"S4 basis replay drift at {coord}")

    # Historical opaque IDs не можуть містити стару donor-координату.
    for row in inventory["rows"]:
        if row["source_class"] == "HISTORICAL-DONOR":
            req(row["stable_id"].startswith("d8.hist."), "historical stable-id prefix drift")
            req(
                row["historical_donor_coordinate"] not in row["stable_id"],
                f"donor coordinate leaked into stable id: {row['semantic_name']}",
            )

    print("D8-V2-GAUGE-S4=PASS")
    print("candidate-map=256/256")
    print("law-forced=64")
    print("product-fixed=8")
    print("gauge-oriented=7")
    print("gauge-fixed=177")
    print("ratified-d8=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
