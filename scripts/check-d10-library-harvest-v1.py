#!/usr/bin/env python3
import json, re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-library-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
ledger1=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))
ledger2=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-library-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4026"
assert harvest["accounting"]["selected_d10_candidates"]==39
rows=harvest["rows"]
assert len(rows)==39 and len({r["stable_id"] for r in rows})==39
assert all(r["coordinate"] is None for r in rows)

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
moved1={r["stable_id"]:r for r in ledger1["rows"]}
moved2={r["stable_id"]:r for r in ledger2["rows"]}
present=0
reclassified_v1=0
reclassified_v2=0
for row in rows:
    in_core=row["stable_id"] in inv_by_id
    in_v1=row["stable_id"] in moved1
    in_v2=row["stable_id"] in moved2
    assert sum((in_core,in_v1,in_v2))==1
    if in_core:
        present+=1
    elif in_v1:
        got=moved1[row["stable_id"]]
        assert got["semantic_name"]==row["semantic_name"]
        assert got["decision"]=="RECLASSIFIED-NONCORE"
        reclassified_v1+=1
    else:
        got=moved2[row["stable_id"]]
        assert got["semantic_name"]==row["semantic_name"]
        assert got["decision"]=="RECLASSIFIED-NONCORE"
        reclassified_v2+=1
assert present==18
assert reclassified_v1==6
assert reclassified_v2==15

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

assert state["library_harvest_v1"]["selected"]==39
print("D10-LIBRARY-HARVEST-V1=PASS")
print(f"harvest=39 core=18 reclassified-v1=6 reclassified-v2=15 inventory={selected_total}/1024 remaining={remaining_total}")
