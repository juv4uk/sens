#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
inv=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
rest=json.loads((root/"knowledge/d10-single-stream-restoration-v1.json").read_text(encoding="utf-8"))
r1=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))
r2=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))
matrix=json.loads((root/"knowledge/d10-owner-repo-donor-matrix-v3.json").read_text(encoding="utf-8"))

assert rest["schema"]=="d10-single-stream-restoration-v1/v1"
assert rest["authority"]=="#4162"
assert rest["accounting"]=={
    "d10_before":434,
    "restored_cleanup_v1":55,
    "restored_cleanup_v2":15,
    "restored_total":70,
    "d10_after":504,
    "law_forced_coordinates":256,
    "unplaced_selected":248,
    "remaining":520,
    "ratified_d10_residents":0,
}

rows=rest["rows"]
assert len(rows)==70
assert len({r["stable_id"] for r in rows})==70
assert len({r["semantic_name"] for r in rows})==70
assert all(r["coordinate"] is None for r in rows)
assert all(r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["decision"]=="RESTORED-D10-CANDIDATE" for r in rows)

historical={r["stable_id"] for r in r1["rows"]}|{r["stable_id"] for r in r2["rows"]}
restored={r["stable_id"] for r in rows}
assert historical==restored

inv_ids={r["stable_id"] for r in inv["rows"]}
inv_names={r["semantic_name"] for r in inv["rows"]}
assert restored <= inv_ids
assert len(inv_ids)==len(inv["rows"])
assert len(inv_names)==len(inv["rows"])

selected_now=state["target"]["selected_semantic_candidates"]
remaining_now=state["target"]["remaining_semantic_candidates"]
assert selected_now>=504
assert remaining_now==1024-selected_now
assert inv["accounting"]=={
    "selected_semantic_candidates":selected_now,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":selected_now-256,
    "remaining_semantic_inventory":remaining_now,
    "ratified_d10_residents":0,
}
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==selected_now-256
assert state["target"]["ratified_residents"]==0

assert matrix["schema"]=="d10-owner-repo-donor-matrix/v3"
assert matrix["repository_count"]==87
assert matrix["authority"]=="#4162"
assert matrix["policy_counts"]=={
    "EVIDENCE-DONOR":33,
    "DIRECT-SEMANTIC-DONOR":43,
    "SEMANTIC-DONOR-WITH-MECHANISM-GATE":11,
}
assert all(r["no_slot_by_ownership"] is False for r in matrix["rows"])
assert state["owner_repo_donor_matrix"]["repositories"]==87
assert state["owner_repo_donor_matrix"]["namespace_rule"]=="ONE-GLOBAL-D10-BITSTREAM"

print("D10-SINGLE-STREAM-RESTORATION=PASS")
print(f"restored=70 inventory={selected_now}/1024 placed=256 unplaced={selected_now-256} remaining={remaining_now} ratified=0")
print("owner-repos=87 direct=43 mechanism-gated=11 evidence=33")
