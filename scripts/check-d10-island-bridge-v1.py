#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
art=json.loads((root/"knowledge/d10-island-bridge-factorization-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert art["schema"]=="d10-island-bridge-factorization-v1/v1"
assert art["status"]=="RESEARCH-UNRATIFIED"
assert art["authority"]=="#4094"
assert art["accounting"]=={
    "execution_repositories_reviewed":11,
    "selected_d10_candidates":6,
    "derived_no_separate_resident":8,
    "mechanism_only":1,
    "d10_before":428,
    "d10_after":434,
    "placed_after":256,
    "unplaced_after":178,
    "remaining_after":590,
    "ratified_d10_residents":0,
}

selected={r["semantic_name"] for r in art["selected"]}
assert selected=={
    "ISLAND-CALL","EXECUTION-WITNESS","NATIVE-OBSERVATION",
    "RESULT-COUNT","BRIDGE","MISSING-CAPABILITY"
}
assert all(r["coordinate"] is None for r in art["selected"])
assert all(r["coordinate_basis"]=="UNPLACED" for r in art["selected"])
assert all(r["ratified_resident"] is False for r in art["selected"])

reviews=art["repository_reviews"]
assert len(reviews)==11
assert len({r["repository"] for r in reviews})==11
assert all(r["native_core_rows_selected"]==0 for r in reviews)
assert all(r["decision"]=="REVIEWED-FOR-UNIVERSAL-SEAM-ONLY" for r in reviews)

decisions={r["name"]:r["decision"] for r in art["decisions"]}
for name in ("ZERO-RESULTS","ONE-RESULT","MANY-RESULTS","EXPLICIT-PROJECTION",
             "ISLAND-PROVENANCE","MISSING-BRIDGE","MISSING-KERNEL","ISLAND-SELECT"):
    assert decisions[name]=="DERIVED-NO-SEPARATE-RESIDENT"
assert decisions["RAW-ISLAND-INVOKE"]=="MECHANISM-ONLY"

# Lower Core already owns APPLY and PROVENANCE; don't duplicate them.
assert foundation["domains"]["D4"]["residents"]["0000"]=="APPLY"
assert foundation["domains"]["D9"]["residents"]["101101111"]=="PROVENANCE"

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in art["selected"]:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="ISLAND-BRIDGE-FACTORIZATION"
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

assert inventory["accounting"]=={
    "selected_semantic_candidates":434,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":178,
    "remaining_semantic_inventory":590,
    "ratified_d10_residents":0,
}
assert state["target"]["selected_semantic_candidates"]==434
assert state["target"]["remaining_semantic_candidates"]==590
assert state["target"]["ratified_residents"]==0
assert state["island_bridge_v1"]["selected"]==6
assert state["island_bridge_v1"]["coordinates_assigned"]==0

print("D10-ISLAND-BRIDGE-V1=PASS")
print("selected=6 inventory=434/1024 placed=256 unplaced=178 remaining=590 ratified=0")
