#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
h=json.loads((root/"knowledge/d10-historical-maclisp-v2.json").read_text(encoding="utf-8"))
inv=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
sens8=json.loads((root/"knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8"))

assert h["schema"]=="d10-historical-maclisp-v2/v1"
assert h["status"]=="RESEARCH-UNRATIFIED"
assert h["authority"]=="#4042"
assert h["accounting"]=={
    "selected_d10_candidates":12,
    "current_projections":9,
    "explicit_boundary_holds":11,
    "d10_selected_before_harvest":388,
    "d10_selected_after_harvest":400,
    "law_forced_coordinates":256,
    "unplaced_selected_after_harvest":144,
    "d10_remaining_after_harvest":624,
    "ratified_d10_residents":0,
}

selected=h["selected"]
projections=h["projections"]
held=h["excluded_or_held"]

assert len(selected)==12
assert len(projections)==9
assert len(held)==11
assert len({r["stable_id"] for r in selected})==12
assert len({r["semantic_name"] for r in selected})==12
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in selected)
assert all(r["selected_d10_candidate"] is True for r in selected)
assert all(r["coordinate"] is None for r in selected)
assert all(r["coordinate_basis"]=="UNPLACED" for r in selected)
assert all(r["ownership"]=="CORE-OWNED-CANDIDATE" for r in selected)
assert all(r["historical_address_authority"]=="NONE" for r in selected)
assert all(r["implementation_class_authority"]=="NONE" for r in selected)
assert all(r["ratified_resident"] is False for r in selected)

expected={
    "MAKNAM","IMPLODE","READLIST","EXPLODE","EXPLODEC","EXPLODEN",
    "FLATSIZE","FLATC","MAPATOMS","MAKE-ARRAY","REARRAY","SORTCAR"
}
assert {r["semantic_name"] for r in selected}==expected

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (lower & expected)

# Explicit projections are preserved as history, not accidentally selected.
assert all(r["decision"]=="CURRENT-PROJECTION" for r in projections)
assert all(r["selected_d10_candidate"] is False for r in projections)
projection_names={r["historical_name"] for r in projections}
assert projection_names=={
    "ASCII","GET_PNAME","CATENATE","STRINGLENGTH","SUBSTR",
    "GETCHAR","GETCHARN","SAMEPNAMEP","ALPHALESSP"
}

# Implementation, host, carrier/Core-Math and nondeterminism boundaries remain outside selection.
assert all(r["decision"]!="SELECT-D10-CANDIDATE" for r in held)
held_names={r["historical_name"] for r in held}
assert {"SUBRCALL","LSUBRCALL","ARRAYCALL","DUMPARRAYS","LOADARRAYS"} <= held_names
assert {"FIX","FLOATP","BIGP","COS","RANDOM","SIGNP"} <= held_names

by_id={r["stable_id"]:r for r in inv["rows"]}
for r in selected:
    current=by_id[r["stable_id"]]
    assert current["semantic_name"]==r["semantic_name"]
    assert current["source_class"]=="HISTORICAL-MACLISP-RECOVERY-V2"
    assert current["coordinate"] is None
    assert current["coordinate_basis"]=="UNPLACED"
    assert current["ownership"]=="CORE-OWNED-CANDIDATE"
    assert current["ratified_resident"] is False

assert inv["accounting"]=={
    "selected_semantic_candidates":400,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":144,
    "remaining_semantic_inventory":624,
    "ratified_d10_residents":0,
}
assert state["target"]["selected_semantic_candidates"]==400
assert state["target"]["unplaced_selected_candidates"]==144
assert state["target"]["remaining_semantic_candidates"]==624
assert state["target"]["ratified_residents"]==0
assert state["historical_maclisp_v2"]["selected"]==12
assert state["historical_maclisp_v2"]["projections"]==9
assert state["historical_maclisp_v2"]["held_or_excluded"]==11
assert state["historical_maclisp_v2"]["coordinates_assigned"]==0
assert state["historical_maclisp_v2"]["sens8_preservation"]=="UNCHANGED"

# Sens8 archaeology stays complete and untouched.
assert sens8["accounting"]["total_legacy_cells"]==256
assert sens8["accounting"]["named_rows_accounted"]==182
assert sens8["accounting"]["donor_coverage_percent"]==100

print("D10-HISTORICAL-MACLISP-2=PASS")
print("selected=12 projections=9 holds=11 inventory=400/1024")
print("placed=256 unplaced=144 remaining=624 ratified=0 sens8=preserved")
