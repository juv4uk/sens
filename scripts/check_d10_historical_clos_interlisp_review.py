#!/usr/bin/env python3
"""Fail-closed historical D10 proposal audit; no admission, coordinates, or ratification."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSALS = "knowledge/d10-historical-clos-interlisp-residual-review-v1.json"
FOUNDATION = "knowledge/d1-d9-foundation.json"
INVENTORY = "knowledge/d10-v1-semantic-inventory.json"

def verify(proposals: dict, foundation: dict, inventory: dict) -> dict:
    if proposals.get("schema") != "d10-historical-clos-interlisp-residual-review/v1":
        raise ValueError("wrong schema")
    if proposals.get("status") != "RESEARCH-UNRATIFIED-NOT-ADMITTED":
        raise ValueError("unexpected authority")
    rows = proposals["rows"]
    if len(rows) != proposals["snapshot"]["rows_proposed"] or len(rows) != 9:
        raise ValueError("row count")
    if proposals["snapshot"]["selected_added"] != 0 or proposals["snapshot"]["coordinates_added"] != 0 or proposals["snapshot"]["ratified_d10"] != 0:
        raise ValueError("unauthorized semantic admission")
    if inventory["accounting"]["ratified_d10_residents"] != 0:
        raise ValueError("review original admission state before proceeding")
    if len(inventory["rows"]) < proposals["snapshot"]["selected_d10"]:
        raise ValueError("unexpected removal from canonical inventory")
    lower = {str(name).upper() for domain in foundation["domains"].values()
             for name in domain.get("residents", {}).values()}
    selected = {str(row["semantic_name"]).upper() for row in inventory["rows"]}
    if len(selected) != len(inventory["rows"]):
        raise ValueError("duplicate canonical D10 names")
    valid_status = {
        "REVIEW-SEMANTIC-CANDIDATE", "HOLD-DERIVABILITY",
        "HOLD-LIFECYCLE-HOOK", "HOLD-CONSTRUCTOR-DERIVED",
        "HOLD-D2-REWRITE-AND-DEDUP", "HOLD-TOOLING-NOT-CORE", "HOLD-D2-CONTROL",
    }
    ids, names = set(), set()
    sources = set(proposals["sources"].values())
    for row in rows:
        name = row["historical_name"].upper()
        rid = row["proposal_id"]
        if not rid or rid in ids or name in names or name in lower or name in selected:
            raise ValueError("name/id collision: " + name)
        ids.add(rid)
        names.add(name)
        if row["triage_status"] not in valid_status:
            raise ValueError("unreviewed status for " + name)
        if row["historical_source"] not in sources or not row["historical_source"].startswith("https://"):
            raise ValueError("missing primary source")
        for field in ("observable_law", "positive_witness", "falsifier", "dedup_or_owner_question", "surface_uk", "surface_ukr"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError("incomplete behavioral witness: " + field)
        if row["coordinate"] is not None or row["selected_in_d10"] is not False or row["ratified"] is not False or row["physical_t5_authorized"] is not False or row["owner_review"] != "PENDING":
            raise ValueError("forbidden research promotion: " + name)
    candidate_count = sum(r["triage_status"] == "REVIEW-SEMANTIC-CANDIDATE" for r in rows)
    if candidate_count != 3 or len(rows)-candidate_count != 6:
        raise ValueError("candidate/HOLD accounting drift")
    return {"proposals": len(rows), "review_candidates": candidate_count, "holds": 6,
            "selected_main": len(inventory["rows"]), "new_ratified": 0}

def main() -> None:
    load = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))
    print("D10 HISTORICAL CLOS/INTERLISP REVIEW PASS", json.dumps(
        verify(load(PROPOSALS), load(FOUNDATION), load(INVENTORY)), sort_keys=True))

if __name__ == "__main__":
    main()
