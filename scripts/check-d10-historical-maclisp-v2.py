#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
h=json.loads((root/"knowledge/d10-historical-maclisp-v2.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
sens8=json.loads((root/"knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8"))

assert h["schema"]=="d10-historical-maclisp-v2/v1"
assert h["authority"]=="#4042"
assert h["accounting"]["selected_d10_candidates"]==12
assert len(h["selected"])==12 and len(h["projections"])==9 and len(h["excluded_or_held"])==11
by_id={r["stable_id"]:r for r in inventory["rows"]}
for r in h["selected"]:
    current=by_id[r["stable_id"]]
    assert current["semantic_name"]==r["semantic_name"]
    assert current["source_class"]=="HISTORICAL-MACLISP-RECOVERY-V2"
    assert current["ownership"]=="CORE-OWNED-CANDIDATE"
    assert current["coordinate"] is None

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

assert state["historical_maclisp_v2"]["selected"]==12
assert sens8["accounting"]["donor_coverage_percent"]==100
print("D10-HISTORICAL-MACLISP-2=PASS")
print(f"historical-selected=12 inventory={selected_total}/1024 remaining={remaining_total} sens8=preserved")
