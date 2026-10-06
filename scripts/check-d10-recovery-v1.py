#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
recovery=json.loads((root/"knowledge/d10-recovery-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
d9=json.loads((root/"knowledge/d9-ratified.json").read_text(encoding="utf-8"))

assert recovery["schema"]=="d10-recovery-v1/v1"
assert recovery["status"]=="RESEARCH-UNRATIFIED"
assert recovery["authority"]=="#4016"
assert recovery["accounting"]=={
    "source_rows":19,
    "selected_d10_candidates":8,
    "lower_surface_or_mechanism_projection":4,
    "hold_semantic_review":7,
    "d10_selected_before_review":256,
    "d10_selected_after_review":264,
    "d10_remaining_after_review":760,
    "ratified_d10_residents":0,
}

rows=recovery["rows"]
assert len(rows)==19
assert len({r["stable_id"] for r in rows})==19
assert len({r["source_name"] for r in rows})==19

selected=[r for r in rows if r["selected_d10_candidate"]]
holds=[r for r in rows if r["decision"]=="HOLD-SEMANTIC-REVIEW"]
projections=[r for r in rows if "PROJECTION" in r["decision"] or r["decision"]=="MECHANISM-OR-SURFACE-PROJECTION"]
assert len(selected)==8
assert len(holds)==7
assert len(projections)==4

expected_selected={
    "COMPILE-FILE",
    "LDB",
    "MASK-FIELD",
    "BOOLE",
    "MONO-NS",
    "UNIX-TIME-NOW",
    "NTP-QUERY-RAW",
    "TIMEZONE-DECLARATIONS-RAW",
}
assert {r["semantic_name"] for r in selected}==expected_selected
assert all(r["coordinate"] is None for r in selected)
assert all(r["coordinate_basis"]=="UNPLACED" for r in selected)
assert all(r["ratified_resident"] is False for r in selected)

d9_names={str(r["resident"]).upper() for r in d9["rows"]}
assert not (expected_selected & d9_names)

by_source={r["source_name"]:r for r in rows}
assert by_source["codepoint->string"]["lower_identity"]=="D8 CODE-CHAR"
assert by_source["string->codepoint"]["lower_identity"]=="D8 CHAR-CODE"
assert by_source["defmacro"]["lower_identity"]=="D5 MACRO + D4 DEFINE"
assert by_source["THE"]["decision"]=="MECHANISM-OR-SURFACE-PROJECTION"
assert by_source["invoke"]["decision"]=="HOLD-SEMANTIC-REVIEW"

inventory_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in selected:
    got=inventory_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="D9-HOLD-RECOVERY"
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"

assert state["target"]["selected_semantic_candidates"]==264
assert state["target"]["remaining_semantic_candidates"]==760
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==8
assert state["target"]["ratified_residents"]==0
assert state["recovery_v1"]=={
    "artifact":"knowledge/d10-recovery-v1.json",
    "source_rows":19,
    "selected":8,
    "projection":4,
    "hold":7,
    "coordinates_assigned":0,
}

print("D10-RECOVERY-V1: PASS")
print("selected=8 projection=4 hold=7 inventory=264/1024 remaining=760 ratified=0")
