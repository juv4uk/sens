#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
review=json.loads((root/"knowledge/d10-wsm-os-lisp-ownership-v1.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))

assert review["schema"]=="d10-wsm-os-lisp-ownership-v1/v1"
assert review["authority"]=="#4045"
assert review["wsm_issue"]=="#74"
assert review["accounting"]["new_d10_candidates_selected"]==0
assert len(review["core_review"])==4
assert len(review["wsm_owned"])==24
assert len(review["mechanism_only"])==8
selected_names={row["semantic_name"] for row in inventory["rows"]}
assert not (selected_names & {row["semantic_name"] for row in review["wsm_owned"]})

target=state["target"]
selected_total=target["selected_semantic_candidates"]
remaining_total=target["remaining_semantic_candidates"]
assert selected_total>=256
assert remaining_total==1024-selected_total
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==selected_total-256
assert target["ratified_residents"]==0
assert len(inventory["rows"])==selected_total
assert len({r["stable_id"] for r in inventory["rows"]})==selected_total
assert len({r["semantic_name"] for r in inventory["rows"]})==selected_total

assert state["wsm_os_lisp_ownership"]["selected_d10_candidates"]==0
print("D10-WSM-OS-LISP-OWNERSHIP=PASS")
print(f"core-new=0 wsm-owned=24 mechanism-only=8 inventory={selected_total}/1024 remaining={remaining_total}")
