#!/usr/bin/env python3
"""#2724 — standing D5 fill watchdog.

This is coordination/proof plumbing, not a resident allocator.

It composes existing authoritative artifacts:
- #2510 current D5 closure map;
- #2616 D5 eligibility ledger;
- #2617 post-D4 root minimization;
- #2703 historical semantic placement.

The watchdog stays GREEN while current evidence yields no exact new D5
candidate. It turns RED with REVIEW-REQUIRED when a new historical row appears
without placement, when any factor becomes D5-eligible YES, or when semantic
placement starts naming D5 without a separately updated ratified baseline.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
D5_MAP = ROOT / "benchmarks" / "d5-closure-map" / "run.py"
ELIGIBILITY = ROOT / "benchmarks" / "d5-sens-derivation-closeout" / "factor-eligibility.json"
ROOT_MIN = ROOT / "benchmarks" / "post-d4-root-min-closeout" / "run.py"
HISTORY = ROOT / "docs" / "research" / "2344-post-d4-historical-ledger.json"
PLACEMENT = ROOT / "benchmarks" / "post-d4-semantic-placement" / "placement.json"

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
    d5_rows = d5_ns["build_map"]()
    generated = {r["coordinate"] for r in d5_rows if r["status"] == "generated"}
    unknown = {r["coordinate"] for r in d5_rows if r["status"] == "UNKNOWN/free"}

    if generated != EXPECTED_GENERATED:
        review(f"selector generated set drifted: {sorted(generated)}")
    if len(generated) != 8 or len(unknown) != 24:
        review(f"ratified 8/24 baseline drifted: generated={len(generated)} unknown={len(unknown)}")
    if any(r["manual_resident_required"] for r in d5_rows):
        review("closure map contains manual resident requirement")
    if any(r["placement_ref"] for r in d5_rows):
        review("closure map contains pre-placement reference")

    eligibility = load_json(ELIGIBILITY)
    invariant = eligibility["map_invariant"]
    expected_invariant = {
        "capacity": 32,
        "selector_generated": 8,
        "unknown_free": 24,
        "manual_nonselector_residents": 0,
        "source": "#2510/#2414",
    }
    if invariant != expected_invariant:
        review(f"eligibility baseline invariant drifted: {invariant}")

    yes_factors = [
        row["factor_id"]
        for row in eligibility["factors"]
        if row["d5_eligible"] == "YES"
    ]
    if yes_factors:
        review("new D5-eligible factor(s): " + ",".join(sorted(yes_factors)))

    yes_controls = [
        row["control_id"]
        for row in eligibility.get("composite_controls", [])
        if row["d5_eligible"] == "YES"
    ]
    if yes_controls:
        review("new D5-eligible composite control(s): " + ",".join(sorted(yes_controls)))

    root_ns = runpy.run_path(str(ROOT_MIN))
    root_rows = root_ns["ROWS"]
    unresolved_root_rows = [
        row["factor"]
        for row in root_rows
        if row["root_status"] == "UNRESOLVED"
    ]
    if unresolved_root_rows:
        review("root-min ledger reopened: " + ",".join(sorted(unresolved_root_rows)))

    history = load_json(HISTORY)
    placement = load_json(PLACEMENT)
    historical_ops = {row["operation"] for row in history["rows"]}
    placement_ops = {row["operation"] for row in placement["rows"]}

    missing_placement = sorted(historical_ops - placement_ops)
    if missing_placement:
        review("historical row(s) need semantic placement: " + ",".join(missing_placement))

    orphan_placement = sorted(placement_ops - historical_ops)
    if orphan_placement:
        review("placement row(s) have no historical source: " + ",".join(orphan_placement))

    invariants = placement["invariants"]
    if invariants.get("d5_selector_generated") != 8:
        review("semantic-placement selector count drifted")
    if invariants.get("d5_unknown_free") != 24:
        review("semantic-placement UNKNOWN count drifted")
    if invariants.get("d5_manual_nonselector_residents") != 0:
        review("semantic-placement manual D5 residents appeared")
    if invariants.get("new_nonselector_d5_candidates") != 0:
        review("semantic-placement reports new nonselector D5 candidate")

    direct_d5_rows = []
    candidate_d5_rows = []
    for row in placement["rows"]:
        exact_domain = str(row.get("exact_domain", ""))
        coordinate = str(row.get("coordinate", ""))
        candidate = row.get("candidate_coordinate")
        if exact_domain == "D5" or (coordinate not in {"", "NONE", "UNPLACED"} and len(coordinate) == 5):
            direct_d5_rows.append(row["operation"])
        if isinstance(candidate, str) and candidate.startswith("D5:"):
            candidate_d5_rows.append(row["operation"])

    if direct_d5_rows:
        review("historical placement now claims D5 resident(s): " + ",".join(sorted(direct_d5_rows)))
    if candidate_d5_rows:
        review("historical placement now nominates D5 candidate(s): " + ",".join(sorted(candidate_d5_rows)))

    unknown_eligibility = sorted(
        row["factor_id"]
        for row in eligibility["factors"]
        if row["d5_eligible"] == "UNKNOWN"
    )

    summary = {
        "schema": "d5-fill-watch/v1",
        "issue": "#2724",
        "status": "PASS",
        "width": 5,
        "capacity": 32,
        "generated_residents": sorted(generated),
        "generated_count": len(generated),
        "unknown_coordinates": sorted(unknown),
        "unknown_count": len(unknown),
        "manual_nonselector_residents": 0,
        "new_d5_eligible_factors": [],
        "historical_rows": len(historical_ops),
        "semantic_placement_rows": len(placement_ops),
        "unresolved_d5_eligibility_factors_in_legacy_ledger": unknown_eligibility,
        "root_min_unresolved": [],
        "review_required": False,
        "fill_rule": "semantic-family-first; never enumerate UNKNOWN coordinates",
    }

    print("D5-FILL-WATCH=PASS")
    print("width=5")
    print("generated=8")
    print("unknown=24")
    print("manual=0")
    print("new-d5-candidates=0")
    print(f"historical-rows={len(historical_ops)}")
    print("review-required=no")
    if unknown_eligibility:
        print("legacy-eligibility-unknown=" + ",".join(unknown_eligibility))
        print("note=root-min closeout is authoritative for those factor statuses")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "d5-fill-watch.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
