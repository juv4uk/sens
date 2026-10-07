#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
h=json.loads((root/"knowledge/d10-crossrepo-mal-v1.json").read_text(encoding="utf-8"))
inv=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert h["schema"]=="d10-crossrepo-mal-v1/v1"
assert h["status"]=="RESEARCH-UNRATIFIED"
assert h["authority"]=="#4053"
assert h["donor"]["repository"]=="juv4uk/mal"
assert h["donor"]["path"]=="impls/common-lisp/src/core.lisp"
assert h["accounting"]=={
    "builtins_reviewed":62,
    "selected_d10_candidates":22,
    "current_or_derived_projections":38,
    "hold_semantic_review":2,
    "d10_before":345,
    "d10_after":367,
    "law_forced_coordinates":256,
    "unplaced_after":111,
    "remaining_after":657,
    "ratified_d10_residents":0,
}

rows=h["rows"]
assert len(rows)==62
counts={}
for r in rows:
    counts[r["decision"]]=counts.get(r["decision"],0)+1
assert counts=={
    "SELECT-D10-CANDIDATE":22,
    "CURRENT-OR-DERIVED-PROJECTION":38,
    "HOLD-SEMANTIC-REVIEW":2,
}
assert all(r["donor_implementation_authority"]=="NONE" for r in rows)
assert all(r["donor_coordinate_authority"]=="NONE" for r in rows)

selected=[r for r in rows if r["selected_d10_candidate"]]
assert len(selected)==22
assert len({r["stable_id"] for r in selected})==22
assert len({r["semantic_name"] for r in selected})==22
assert all(r["coordinate"] is None for r in selected)
assert all(r["coordinate_basis"]=="UNPLACED" for r in selected)
assert all(r["ratified_resident"] is False for r in selected)

expected={
    "LISTP","SEQUENCE-EMPTY?","SEQUENCE-COUNT",
    "REF-CELL","REF-CELLP","DEREF","RESET-REF!","SWAP-REF!",
    "KEYWORD","KEYWORDP","VECTORP","FUNCTIONP","MACROP",
    "MAP-FROM-PAIRS","MAPP","MAP-DISSOC","MAP-KEYS","MAP-VALUES",
    "SEQUENTIALP","SEQ-VIEW","WITH-META","META",
}
assert {r["semantic_name"] for r in selected}==expected

holds={r["donor_name"] for r in rows if r["decision"]=="HOLD-SEMANTIC-REVIEW"}
assert holds=={"readline","cl-eval"}

# No exact ratified D1-D9 resident name may be reintroduced.
lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (lower & expected)

by_id={r["stable_id"]:r for r in inv["rows"]}
for r in selected:
    got=by_id[r["stable_id"]]
    assert got["semantic_name"]==r["semantic_name"]
    assert got["source_class"]=="CROSSREPO-MAL-HISTORICAL-HARVEST"
    assert got["ownership"]=="CORE-OWNED-CANDIDATE"
    assert got["coordinate"] is None
    assert got["ratified_resident"] is False

assert inv["accounting"]=={
    "selected_semantic_candidates":367,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":111,
    "remaining_semantic_inventory":657,
    "ratified_d10_residents":0,
}
assert state["target"]["selected_semantic_candidates"]==367
assert state["target"]["remaining_semantic_candidates"]==657
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==111
assert state["target"]["ratified_residents"]==0
assert state["crossrepo_mal_v1"]=={
    "authority":"#4053",
    "artifact":"knowledge/d10-crossrepo-mal-v1.json",
    "reviewed":62,
    "selected":22,
    "projections":38,
    "hold":2,
    "coordinates_assigned":0,
}

print("D10-CROSSREPO-MAL-1=PASS")
print("reviewed=62 selected=22 projections=38 hold=2 inventory=367/1024 placed=256 unplaced=111 remaining=657")
