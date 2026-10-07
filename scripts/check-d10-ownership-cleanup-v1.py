#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ledger=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
gate=json.loads((root/"knowledge/island-ownership-gate-v1.json").read_text(encoding="utf-8"))

assert ledger["schema"]=="d10-noncore-reclassification-v1/v1"
assert ledger["status"]=="PRESERVED-RECLASSIFIED"
assert ledger["authority"]=="#4047"
assert ledger["accounting"]=={
    "reclassified_rows":55,
    "forward_clips":26,
    "knowledge_datalog_package":23,
    "world_package":6,
    "d10_before":400,
    "d10_after":345,
    "selector_coordinates_preserved":256,
    "ratified_d10_residents":0,
}

rows=ledger["rows"]
assert len(rows)==55
assert len({r["stable_id"] for r in rows})==55
assert len({r["semantic_name"] for r in rows})==55
assert all(r["decision"]=="RECLASSIFIED-NONCORE" for r in rows)
assert all(r["core_d10_selected"] is False for r in rows)
assert all(r["original_coordinate"] is None for r in rows)

inv_ids={r["stable_id"] for r in inventory["rows"]}
moved_ids={r["stable_id"] for r in rows}
assert not (inv_ids & moved_ids)

frozen=set(gate["d10"]["frozen_definite_stable_ids"])
assert moved_ids==frozen

review=set(gate["d10"]["frozen_review_stable_ids"])
current_ids=set(inv_ids)
review_ledger=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))
review_moved={r["stable_id"] for r in review_ledger["rows"]}
assert review_moved==review
assert not (review & current_ids)

target=state["target"]
selected_now=target["selected_semantic_candidates"]
remaining_now=target["remaining_semantic_candidates"]
assert selected_now>=345
assert remaining_now==1024-selected_now
assert target["domain"]=="D10"
assert target["width"]==10
assert target["capacity"]==1024
assert target["dense_target"]==1024
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==selected_now-256
assert target["ratified_residents"]==0
assert inventory["accounting"]=={
    "selected_semantic_candidates":selected_now,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":selected_now-256,
    "remaining_semantic_inventory":remaining_now,
    "ratified_d10_residents":0,
}
assert state["ownership_cleanup_v1"]=={
    "authority":"#4047",
    "artifact":"knowledge/d10-noncore-reclassification-v1.json",
    "removed_from_core":55,
    "selected_after":345,
    "selector_coordinates_preserved":256,
    "review_required_still_selected":15,
    "ratification_effect":"NONE",
}
assert state["ownership_gate"]["definite_noncore_selected"]==0
assert state["ownership_gate"]["definite_noncore_reclassified"]==55
assert state["ownership_gate"]["review_required_selected"]==0
assert state["target"]["ratified_residents"]==0

print("D10-OWNERSHIP-CLEANUP-1=PASS")
print(f"first-cleanup-preserved=55 final-review-reclassified=15 inventory={selected_now}/1024 placed=256 unplaced={selected_now-256} remaining={remaining_now} ratified=0")
