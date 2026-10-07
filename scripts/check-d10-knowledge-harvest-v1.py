#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-knowledge-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
ledger=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-knowledge-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4030"
assert harvest["accounting"]["selected_d10_candidates"]==37
rows=harvest["rows"]
assert len(rows)==37 and len({r["stable_id"] for r in rows})==37
assert all(r["coordinate"] is None for r in rows)

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
historical={r["stable_id"]:r for r in ledger["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"

assert sum(r["stable_id"] in historical for r in rows)==23

target=state["target"]
assert target["selected_semantic_candidates"]==504
assert target["remaining_semantic_candidates"]==520
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==248
assert target["ratified_residents"]==0

print("D10-KNOWLEDGE-HARVEST-V1=PASS")
print("harvest=37 selected=37 historical-cleanup-v1=23 inventory=504/1024 remaining=520")
