#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
review=json.loads((root/"knowledge/d10-wsm-os-lisp-ownership-v1.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))

assert review["schema"]=="d10-wsm-os-lisp-ownership-v1/v1"
assert review["status"]=="RESEARCH-UNRATIFIED"
assert review["authority"]=="#4045"
assert review["wsm_issue"]=="#74"

assert review["accounting"]=={
    "core_review_rows":4,
    "new_d10_candidates_selected":0,
    "wsm_owned_package_rows":24,
    "mechanism_only_rows":8,
    "d10_selected_after_review":400,
    "d10_remaining_after_review":624,
    "d10_coordinates_assigned":0,
    "ratified_d10_residents":0,
}

assert len(review["core_review"])==4
assert len(review["wsm_owned"])==24
assert len(review["mechanism_only"])==8
assert all(row["coordinate"] is None for row in review["core_review"])
assert all(row["d10_slot_effect"]==0 for row in review["core_review"])

selected_names={row["semantic_name"] for row in inventory["rows"]}
wsm_owned={row["semantic_name"] for row in review["wsm_owned"]}
assert not (selected_names & wsm_owned)

# Current WSM evidence is explicitly non-resumable; do not promote restart semantics.
by_name={row["semantic_name"]:row for row in review["core_review"]}
assert by_name["SIGNAL-CONDITION"]["decision"]=="HOLD-FUTURE-SEMANTIC-REVIEW"
assert by_name["RESTART-AVAILABLE?"]["decision"]=="HOLD-FUTURE-SEMANTIC-REVIEW"
assert by_name["INVOKE-RESTART"]["decision"]=="HOLD-FUTURE-SEMANTIC-REVIEW"
assert by_name["USE-VALUE"]["decision"]=="DERIVED-NAMED-RESTART-CONVENTION-HOLD"

target=state["target"]
assert target["selected_semantic_candidates"]==400
assert target["remaining_semantic_candidates"]==624
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==144
assert target["ratified_residents"]==0

assert state["wsm_os_lisp_ownership"]=={
    "artifact":"knowledge/d10-wsm-os-lisp-ownership-v1.json",
    "authority":"#4045",
    "wsm_issue":"juv4uk/wsm-os-lisp#74",
    "core_review_rows":4,
    "selected_d10_candidates":0,
    "wsm_owned_package_rows":24,
    "mechanism_only_rows":8,
    "coordinates_assigned":0,
    "inventory_count_unchanged":True,
}

print("D10-WSM-OS-LISP-OWNERSHIP=PASS")
print("core-new=0 wsm-owned=24 mechanism-only=8 restart-review=4")
print("D10=400/1024 placed=256 unplaced=144 remaining=624 ratified=0")
