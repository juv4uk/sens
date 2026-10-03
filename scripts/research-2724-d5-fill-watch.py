#!/usr/bin/env python3
"""#2763 — D5 owner-map remap watchdog.

This file keeps the historical name "fill watch", but OD-005 changed its job.
There are no current free D5 coordinates to fill.

The watchdog now protects:
- exact 32/32 owner residency;
- zero UNKNOWN current occupancy;
- eight selector-law generated residents;
- exact owner coordinate/name/parent mapping;
- orthogonal semantic-class ledger;
- explicit owner-map revision for any remap.

PRE-OD005 sparse eligibility/placement studies remain research evidence and do
not veto current owner residency.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
D5_MAP = ROOT / "benchmarks" / "d5-closure-map" / "run.py"
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
SEMANTIC_LEDGER = ROOT / "knowledge" / "d5-d6-semantic-ledger.json"

EXPECTED_GENERATED = {
    "10100", "10101", "10110", "10111",
    "11000", "11001", "11010", "11011",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def review(reason: str) -> None:
    raise SystemExit(f"D5-FILL-WATCH=REVIEW-REQUIRED\nreason={reason}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    d5_ns = runpy.run_path(str(D5_MAP))
    rows = d5_ns["build_map"]()
    generated = {r["coordinate"] for r in rows if r["status"] == "generated"}
    historical = {r["coordinate"] for r in rows if r["status"] == "owner-historical"}
    unknown = {r["coordinate"] for r in rows if "UNKNOWN" in r["status"]}

    if generated != EXPECTED_GENERATED:
        review(f"selector generated set drifted: {sorted(generated)}")
    if len(rows) != 32 or len(generated) != 8 or len(historical) != 24 or unknown:
        review(
            "OD-005 occupancy drifted: "
            f"rows={len(rows)} generated={len(generated)} "
            f"owner-historical={len(historical)} unknown={len(unknown)}"
        )

    owner = load_json(OWNER_MAP)
    owner_by = {row["coordinate"]: row for row in owner["coordinates"]}
    if len(owner_by) != 32:
        review("owner map is not exact 32/32")

    ledger = load_json(SEMANTIC_LEDGER)
    ledger_rows = [row for row in ledger["rows"] if row["domain"] == "Core.D5"]
    ledger_by = {row["coordinate"]: row for row in ledger_rows}
    if len(ledger_by) != 32:
        review("semantic ledger is not exact 32-row D5 coverage")

    for row in rows:
        coordinate = row["coordinate"]
        owner_row = owner_by.get(coordinate)
        ledger_row = ledger_by.get(coordinate)
        if owner_row is None or ledger_row is None:
            review(f"{coordinate}: missing owner/semantic row")
        if row["display_name"] != owner_row["name"]:
            review(f"{coordinate}: unauthorized owner-name remap")
        if row["parent_d4"] != owner_row["parent_d4"]:
            review(f"{coordinate}: unauthorized parent remap")
        if ledger_row["residency"] != "YES":
            review(f"{coordinate}: semantic ledger lost owner residency")
        if row["semantic_class"] != ledger_row["semantic_class"]:
            review(f"{coordinate}: semantic class disagrees with #2765 ledger")

    summary = {
        "schema": "d5-fill-watch/v2",
        "issue": "#2724/#2763",
        "status": "PASS",
        "width": 5,
        "capacity": 32,
        "resident_count": 32,
        "generated_residents": sorted(generated),
        "generated_count": 8,
        "owner_historical_coordinates": sorted(historical),
        "owner_historical_count": 24,
        "unknown_coordinates": [],
        "unknown_count": 0,
        "review_required": False,
        "fill_rule": "owner-map-guard; there is no current free D5 occupancy",
        "remap_rule": "coordinate/name/parent changes require explicit owner-map revision",
        "semantic_rule": "derivability/classification remains orthogonal to residency",
        "pre_od005_sparse_research": "ARCHIVED-NOT-CURRENT-OCCUPANCY",
    }

    print("D5-FILL-WATCH=PASS")
    print("width=5")
    print("resident=32")
    print("generated=8")
    print("owner-historical=24")
    print("unknown=0")
    print("review-required=no")
    print("rule=guard-owner-map-not-find-occupant")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "d5-fill-watch.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
