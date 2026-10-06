#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
recovery=json.loads((root/"knowledge/d10-recovery-v2.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert recovery["schema"]=="d10-recovery-v2/v1"
assert recovery["status"]=="RESEARCH-UNRATIFIED"
assert recovery["authority"]=="#4024"
assert recovery["accounting"]=={
    "source_hold_rows":7,
    "selected_d10_candidates":1,
    "current_projection":1,
    "hold_semantic_review":5,
    "d10_selected_before_review":264,
    "d10_selected_after_review":265,
    "d10_remaining_after_review":759,
    "law_forced_coordinates":256,
    "unplaced_selected_after_review":9,
    "ratified_d10_residents":0,
}

rows=recovery["rows"]
assert len(rows)==7
assert len({r["stable_id"] for r in rows})==7
assert len({r["source_name"] for r in rows})==7

by={r["source_name"]:r for r in rows}
assert by["GENERATE-EXPANSION"]["decision"]=="CURRENT-PROJECTION"
assert by["GENERATE-EXPANSION"]["current_target"]=="D9:110001010 MACRO-FUNCTION"
assert by["GENERATE-EXPANSION"]["coordinate"] is None

schar=by["SCHAR"]
assert schar["decision"]=="SELECT-D10-CANDIDATE"
assert schar["semantic_name"]=="SCHAR"
assert schar["corrected_behavior"]=="access the character at INDEX in a simple string"
assert schar["coordinate"] is None
assert schar["coordinate_basis"]=="UNPLACED"
assert schar["relation_class"]=="STRING-INDEX-ACCESS"
assert schar["ratified_resident"] is False

for name in ("BACKQUANTIZE","COUNT-LEADING-ZEROS","TABLESPACE","COLLECTION","invoke"):
    assert by[name]["decision"]=="HOLD-SEMANTIC-REVIEW"

# Current D9 already owns MACRO-FUNCTION; GENERATE-EXPANSION must not duplicate it.
assert foundation["domains"]["D9"]["residents"]["110001010"]=="MACRO-FUNCTION"

inv_by_name={r["semantic_name"]:r for r in inventory["rows"]}
assert "SCHAR" in inv_by_name
got=inv_by_name["SCHAR"]
assert got["source_class"]=="D9-HOLD-RECOVERY-V2"
assert got["coordinate"] is None
assert got["coordinate_basis"]=="UNPLACED"
assert got["behavior"]=="access the character at INDEX in a simple string"
assert got["ratified_resident"] is False

selected_total=state["target"]["selected_semantic_candidates"]
assert selected_total>=265
assert state["target"]["remaining_semantic_candidates"]==1024-selected_total
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==selected_total-256
assert state["target"]["ratified_residents"]==0
assert state["recovery_v2"]=={
    "artifact":"knowledge/d10-recovery-v2.json",
    "source_hold_rows":7,
    "selected":1,
    "projection":1,
    "hold":5,
    "coordinates_assigned":0,
}

print("D10-RECOVERY-V2=PASS")
print(f"SCHAR-selected=yes GENERATE-EXPANSION=projection holds=5 inventory={selected_total}/1024 remaining={1024-selected_total} ratified=0")
