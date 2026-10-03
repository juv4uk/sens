#!/usr/bin/env python3
"""#2763 — standing OD-005 Core D5 current-baseline guard.

Current occupancy authority is the owner map, not the pre-OD005 sparse closure
snapshot. Semantic derivability remains an independent axis.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
CLOSURE = REPO / "benchmarks" / "d5-closure-map" / "run.py"
OWNER_MAP = REPO / "knowledge" / "d5-historical-full-map.json"
SEMANTIC_LEDGER = REPO / "knowledge" / "d5-d6-semantic-ledger.json"

WIDTH = 5
CAPACITY = 1 << WIDTH
SELECTOR_GENERATED = {
    "10100", "10101", "10110", "10111",
    "11000", "11001", "11010", "11011",
}


def fail(message: str) -> None:
    raise AssertionError(f"D5 OD-005 baseline drift: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_result() -> dict[str, Any]:
    closure = runpy.run_path(str(CLOSURE))
    rows = closure["build_map"]()
    acct = closure["accounting"](rows)
    owner = load(OWNER_MAP)
    ledger = load(SEMANTIC_LEDGER)

    require(len(rows) == CAPACITY, f"expected {CAPACITY} rows, got {len(rows)}")
    require(len({row["coordinate"] for row in rows}) == CAPACITY, "duplicate coordinate")
    require(all(row["width"] == WIDTH for row in rows), "row width drift")
    require(all(row["residency"] == "YES" for row in rows), "current D5 contains non-resident row")

    generated = [row for row in rows if row["status"] == "generated"]
    historical = [row for row in rows if row["status"] == "owner-historical"]
    unknown = [row for row in rows if "UNKNOWN" in row["status"]]

    require({row["coordinate"] for row in generated} == SELECTOR_GENERATED, "selector set drift")
    require(len(generated) == 8, "selector-generated count drift")
    require(len(historical) == 24, "owner-historical count drift")
    require(not unknown, "current OD-005 baseline must have UNKNOWN=0")

    owner_by = {row["coordinate"]: row for row in owner["coordinates"]}
    ledger_rows = [row for row in ledger["rows"] if row["domain"] == "Core.D5"]
    ledger_by = {row["coordinate"]: row for row in ledger_rows}
    require(len(owner_by) == CAPACITY, "owner map must contain 32 coordinates")
    require(len(ledger_by) == CAPACITY, "semantic ledger must contain 32 D5 coordinates")

    for row in rows:
        coordinate = row["coordinate"]
        require(row["display_name"] == owner_by[coordinate]["name"], f"{coordinate}: owner name drift")
        require(row["parent_d4"] == owner_by[coordinate]["parent_d4"], f"{coordinate}: parent drift")
        require(ledger_by[coordinate]["residency"] == "YES", f"{coordinate}: ledger residency drift")
        require(row["semantic_class"] == ledger_by[coordinate]["semantic_class"], (
            f"{coordinate}: semantic class drift"
        ))
        require(row["collision"] is False, f"{coordinate}: collision")

    for row in generated:
        require(row["semantic_family"] == "selector", f"{row['coordinate']}: not selector")
        require(row["semantic_law"] == "selector projection composition", (
            f"{row['coordinate']}: selector law drift"
        ))
        require(row["certificate_replay_ok"] is True, (
            f"{row['coordinate']}: selector certificate no longer replays"
        ))

    require(acct["owner_resident_count"] == 32, "accounting resident count drift")
    require(acct["generated_coordinate_count"] == 8, "accounting selector count drift")
    require(acct["owner_historical_count"] == 24, "accounting historical count drift")
    require(acct["unknown_free_count"] == 0, "accounting UNKNOWN must be zero")

    semantic_classes: dict[str, int] = {}
    for row in rows:
        semantic_classes[row["semantic_class"]] = semantic_classes.get(row["semantic_class"], 0) + 1

    return {
        "schema": "d5-ratified-baseline-guard/v2",
        "authority": "OD-005/#2538/#2750/#2763",
        "domain": "Core.D5",
        "width": WIDTH,
        "capacity": CAPACITY,
        "domain_ratified": True,
        "baseline_ratified": True,
        "resident_count": 32,
        "generated_selector_count": 8,
        "owner_historical_nonselector_count": 24,
        "unknown_count": 0,
        "collision_count": 0,
        "semantic_classes": semantic_classes,
        "occupancy_change_requires_owner_map_revision": True,
        "derivability_does_not_erase_residency": True,
        "pre_od005_sparse_model": "ARCHIVED-RESEARCH",
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = build_result()
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print("D5-RATIFIED-BASELINE=PASS")
    print("width=5")
    print("capacity=32")
    print("resident=32")
    print("selector-generated=8")
    print("owner-historical=24")
    print("unknown=0")
    print("collisions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
