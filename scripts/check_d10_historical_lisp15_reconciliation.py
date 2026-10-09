#!/usr/bin/env python3
"""Fail-closed validation for the historical Lisp 1.5 D10 reconciliation."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "knowledge/d10-historical-lisp15-reconciliation-20261009.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"

def verify(review: dict, foundation: dict, inventory: dict) -> dict:
    if review.get("schema") != "d10-historical-lisp15-reconciliation/v1":
        raise ValueError("wrong reconciliation schema")
    if review.get("status") != "RESEARCH-ONLY-NO-RESIDENTS":
        raise ValueError("unexpected review authority")
    rows = review.get("rows")
    if not isinstance(rows, list) or len(rows) != 31 or review["snapshot"]["rows_reconciled"] != 31:
        raise ValueError("expected 30 recovered families plus one MAPATOMS/OBARRAY review lead")
    if review["snapshot"]["selected_added"] or review["snapshot"]["coordinates_added"] or review["snapshot"]["ratifications_added"]:
        raise ValueError("a historical audit must not change semantic authority")
    if review["snapshot"]["d10_selected"] != inventory["accounting"]["selected_semantic_candidates"]:
        raise ValueError("selected candidate count drift")
    if review["snapshot"]["d10_ratified"] != inventory["accounting"]["ratified_d10_residents"]:
        raise ValueError("ratification count drift")
    if review["snapshot"]["foundation_blob"] != review["lineage"].get("expected_foundation_blob", review["snapshot"]["foundation_blob"]):
        raise ValueError("foundation pin mismatch")
    if len({row.get("review_id") for row in rows}) != len(rows):
        raise ValueError("duplicate review_id")
    for row in rows:
        if row.get("selected_d10") is not False or row.get("coordinate") is not None or row.get("ratified") is not False:
            raise ValueError(f"authority leak in {row.get('review_id')}")
    ob = next((r for r in rows if r.get("review_id") == "L15-31"), None)
    if not ob or ob.get("exact_d1_d9_name_matches") or ob.get("exact_selected_d10_name_matches"):
        raise ValueError("MAPATOMS/OBARRAY is not an exact-name match; behavioral dedup remains mandatory")
    selected_names = {r["semantic_name"].upper() for r in inventory["rows"]}
    lower_names = {str(name).upper() for dom in foundation["domains"].values() for name in dom["residents"].values()}
    if any(n in selected_names or n in lower_names for n in ("MAPATOMS", "OBARRAY")):
        raise ValueError("new exact-name collision: update research disposition before review")
    return {"rows": len(rows), "d10_selected": inventory["accounting"]["selected_semantic_candidates"],
            "selected_added": 0, "coordinates_added": 0, "ratifications_added": 0}

def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    print(json.dumps(verify(review, foundation, inventory), ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
