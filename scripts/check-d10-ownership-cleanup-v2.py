#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ledger=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
audit=json.loads((root/"knowledge/island-ownership-gate-v1.json").read_text(encoding="utf-8"))

assert ledger["schema"]=="d10-review-reclassification-v2/v1"
assert ledger["status"]=="PRESERVED-RECLASSIFIED"
assert ledger["authority"]=="#4092"
assert ledger["accounting"]=={
    "reclassified_rows":15,
    "translation_package":11,
    "science_core_math_package":4,
    "d10_before":443,
    "d10_after":428,
    "selector_coordinates_preserved":256,
    "review_required_after":0,
    "ratified_d10_residents":0,
}

rows=ledger["rows"]
assert len(rows)==15
assert len({r["stable_id"] for r in rows})==15
assert all(r["decision"]=="RECLASSIFIED-NONCORE" for r in rows)
assert all(r["coordinate"] is None for r in rows)
assert sum(r["semantic_name"].startswith("TRANSLATION-") for r in rows)==11
assert sum(r["semantic_name"].startswith("SCIENCE-") for r in rows)==4

removed={r["stable_id"] for r in rows}
current={r["stable_id"] for r in inventory["rows"]}
assert not (removed & current)

frozen=set(audit["d10"]["frozen_review_stable_ids"])
assert removed==frozen

selected_now=state["target"]["selected_semantic_candidates"]
remaining_now=state["target"]["remaining_semantic_candidates"]
assert selected_now>=428
assert remaining_now==1024-selected_now
assert inventory["accounting"]=={
    "selected_semantic_candidates":selected_now,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":selected_now-256,
    "remaining_semantic_inventory":remaining_now,
    "ratified_d10_residents":0,
}
assert len(inventory["rows"])==selected_now
assert len({r["stable_id"] for r in inventory["rows"]})==selected_now
assert len({r["semantic_name"] for r in inventory["rows"]})==selected_now

gate=state["ownership_gate"]
assert gate["status"]=="OWNERSHIP-DEBT-CLEARED"
assert gate["definite_noncore_selected"]==0
assert gate["definite_noncore_reclassified"]==55
assert gate["review_required_selected"]==0
assert gate["no_new_definite_noncore"] is True

assert state["target"]["selected_semantic_candidates"]>=428
assert state["target"]["remaining_semantic_candidates"]==1024-state["target"]["selected_semantic_candidates"]
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==state["target"]["selected_semantic_candidates"]-256
assert state["target"]["ratified_residents"]==0

print("D10-OWNERSHIP-CLEANUP-V2=PASS")
print(f"reclassified=15 ownership-review-debt=0 inventory={selected_now}/1024 placed=256 unplaced={selected_now-256} remaining={remaining_now}")
