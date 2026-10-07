#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
review=json.loads((root/"knowledge/d10-crossrepo-early-lisp-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))

assert review["schema"]=="d10-crossrepo-early-lisp-v1/v1"
assert review["status"]=="RESEARCH-UNRATIFIED"
assert review["authority"]=="#4071"
assert review["accounting"]=={
    "donors_reviewed":4,
    "selected_d10_candidates":6,
    "current_projections":17,
    "hold_semantic_review":1,
    "no_semantic_slot":1,
    "d10_selected_before":367,
    "d10_selected_after":373,
    "d10_remaining_after":651,
    "ratified_d10_residents":0,
}

assert len(review["donors"])==4
assert {d["repository"] for d in review["donors"]}=={
    "juv4uk/mccarthy-eval","juv4uk/lisp","juv4uk/lisp-1","juv4uk/LISP-2"
}
assert all(d["review_status"]=="EXHAUSTED-FOR-THIS-SLICE" for d in review["donors"])

selected=review["selected_rows"]
assert len(selected)==6
assert {r["semantic_name"] for r in selected}=={
    "APPQ","DEFINE-BATCH","CALL/CC","READTABLE","IF","NUMERIC-NOT-EQUAL"
}
assert len({r["stable_id"] for r in selected})==6
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in selected)
assert all(r["ownership"]=="CORE-CANDIDATE" for r in selected)
assert all(r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED" for r in selected)
assert all(r["ratified_resident"] is False for r in selected)

nonselect=review["reviewed_nonselect"]
assert len(nonselect)==19
assert sum(r["decision"]=="CURRENT-PROJECTION" for r in nonselect)==17
assert sum(r["decision"]=="HOLD-SEMANTIC-REVIEW" for r in nonselect)==1
assert sum(r["decision"]=="NO-SEMANTIC-SLOT" for r in nonselect)==1

by={r["semantic_name"]:r for r in nonselect}
assert by["DEFINE-SYNTAX"]["current_target"]=="D5 MACRO + D4 DEFINE"
assert by["READ-MANY"]["current_target"]=="D9 READ-ALL"
assert by["SLURP"]["current_target"]=="D9 READ-FILE"
assert by["SPIT"]["current_target"]=="D9 WRITE-FILE"
assert by["MOD"]["decision"]=="HOLD-SEMANTIC-REVIEW"
assert by["DEBUG"]["decision"]=="NO-SEMANTIC-SLOT"

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in selected:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="CROSSREPO-EARLY-LISP-HISTORICAL-HARVEST"
    assert got["coordinate"] is None
    assert got["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=373
assert target["remaining_semantic_candidates"]==1024-target["selected_semantic_candidates"]
assert target["law_forced_coordinates"]==256
assert target["ratified_residents"]==0

print("D10-CROSSREPO-EARLY-LISP-1=PASS")
print(f"selected=6 global={target['selected_semantic_candidates']}/1024 remaining={target['remaining_semantic_candidates']} ratified=0")
