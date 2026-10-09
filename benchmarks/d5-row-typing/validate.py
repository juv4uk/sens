#!/usr/bin/env python3
"""#2758 review guard: validate D5 historical occupancy vs semantic-residency sidecar.

The owner-ratified OD-005 map remains occupancy authority.  The sidecar may
classify semantic evidence, but it may not add/remove/rename/reparent any D5
historical coordinate.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL = ROOT / "knowledge" / "d5-historical-full-map.json"
STATUS = ROOT / "knowledge" / "d5-historical-semantic-status.json"

PHASES = {"HISTORICAL-INGEST", "STRUCTURAL-DISCOVERY", "SENS-DERIVATION"}
RESIDENCY = {"YES", "NO", "UNKNOWN"}

SELECTORS = {
    "10100", "10101", "10110", "10111",
    "11000", "11001", "11010", "11011",
}

DERIVED_CONTROLS = {
    "00000": "EVALQUOTE",
    "00100": "LABEL",
    "10000": "APPEND",
    "11110": "PAIRLIS",
}


def require(cond: bool, message: str) -> None:
    if not cond:
        raise AssertionError(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    historical = load(HISTORICAL)
    sidecar = load(STATUS)

    require(historical["schema"] == "d5-historical-full-map/v1", "historical schema drift")
    require(historical["domain"] == "Core.D5", "historical domain drift")
    require(historical["width"] == 5 and historical["capacity"] == 32, "D5 width/capacity drift")
    require(sidecar["schema"] == "d5-historical-semantic-status/v1", "sidecar schema drift")
    require(sidecar["source_historical_map"] == str(HISTORICAL.relative_to(ROOT)), "source map ref drift")

    hrows = historical["coordinates"]
    srows = sidecar["rows"]
    require(len(hrows) == 32, "owner map must remain 32 rows")
    require(len(srows) == 32, "sidecar must type all 32 rows")

    hby = {row["coordinate"]: row for row in hrows}
    sby = {row["coordinate"]: row for row in srows}
    require(len(hby) == len(sby) == 32, "duplicate coordinate")
    require(set(hby) == set(sby) == {format(i, "05b") for i in range(32)}, "coordinate coverage drift")

    for coord, srow in sby.items():
        hrow = hby[coord]
        require(srow["historical_name"] == hrow["name"], f"{coord}: historical name drift")
        require(srow["historical_parent_d4"] == hrow["parent_d4"], f"{coord}: parent drift")
        require(srow["historical_category"] == hrow["category"], f"{coord}: category drift")
        require(srow["historical_provenance"] == hrow["provenance"], f"{coord}: provenance drift")
        require(coord.startswith(hrow["parent_d4"]), f"{coord}: no longer child of recorded D4 parent")
        require(srow["phase"] in PHASES, f"{coord}: invalid phase")
        require(srow["semantic_resident"] in RESIDENCY, f"{coord}: invalid semantic_resident")
        require(isinstance(srow["status"], str) and srow["status"], f"{coord}: missing status")
        require(isinstance(srow["law_ref"], str) and srow["law_ref"], f"{coord}: missing law_ref")
        require(isinstance(srow["falsifier_ref"], str) and srow["falsifier_ref"], f"{coord}: missing falsifier_ref")
        require(isinstance(srow["witness_refs"], list), f"{coord}: witness_refs must be a list")

        # Strong classifications need row-specific evidence. UNKNOWN is the
        # conservative default and is allowed to carry either no evidence or
        # partial evidence that has not closed placement.
        if srow["semantic_resident"] in {"YES", "NO"}:
            require(srow["law_ref"] != "UNRESOLVED", f"{coord}: strong residency with unresolved law")
            require(len(srow["witness_refs"]) > 0, f"{coord}: strong residency without witness refs")

    # Positive SENS-resident controls: exact selector descendants are generated
    # independently of their historical names.
    for coord in SELECTORS:
        row = sby[coord]
        require(row["semantic_resident"] == "YES", f"{coord}: selector must be semantic resident")
        require(row["status"] == "generated", f"{coord}: selector status must be generated")
        require(row["phase"] == "SENS-DERIVATION", f"{coord}: selector phase drift")

    # Historical names whose post-D4 derivation has already closed must not
    # silently become independent D5 semantic residents merely because OD-005
    # gave them historical coordinates.
    for coord, name in DERIVED_CONTROLS.items():
        row = sby[coord]
        require(row["historical_name"] == name, f"{coord}: derived control name drift")
        require(row["semantic_resident"] == "NO", f"{coord}: derived control gained D5 residency")
        require(len(row["witness_refs"]) > 0, f"{coord}: derived control lacks evidence")

    # SETQ is deliberately unresolved here. #2759/#2761 own the D5-vs-D6
    # relation. This guard must reopen when that relation is resolved.
    setq = sby["00111"]
    require(setq["historical_name"] == "SETQ", "00111 must remain the historical SETQ row")
    require(setq["semantic_resident"] == "UNKNOWN", "SETQ D5 residency changed before relation audit")

    counts = Counter(row["semantic_resident"] for row in srows)
    expected = sidecar["counts"]
    require(expected["historical_rows"] == 32, "sidecar historical row count drift")
    require(expected["semantic_resident_yes"] == counts["YES"], "YES count drift")
    require(expected["semantic_resident_no"] == counts["NO"], "NO count drift")
    require(expected["semantic_resident_unknown"] == counts["UNKNOWN"], "UNKNOWN count drift")
    require(sum(counts.values()) == 32, "residency count total drift")

    result = {
        "schema": "d5-row-typing-guard/v1",
        "historical_occupancy_rows": 32,
        "historical_coordinates_mutated": 0,
        "semantic_resident_yes": counts["YES"],
        "semantic_resident_no": counts["NO"],
        "semantic_resident_unknown": counts["UNKNOWN"],
        "selector_positive_controls": len(SELECTORS),
        "derived_negative_controls": len(DERIVED_CONTROLS),
        "setq_d5_semantic_residency": setq["semantic_resident"],
        "status": "PASS",
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for key, value in result.items():
        print(f"{key.upper().replace('_','-')}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
