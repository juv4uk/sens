#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
seed=json.loads((root/"knowledge/d9-selector-seed.json").read_text(encoding="utf-8"))
review=json.loads((root/"knowledge/d9-overflow-review-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))

assert inventory["schema"]=="d9-v1-semantic-inventory/v1"
assert inventory["status"]=="RESEARCH-UNRATIFIED-PARTIAL"
assert inventory["domain"]=="D9" and inventory["width"]==9 and inventory["capacity"]==512
assert inventory["accounting"]=={
    "selected_semantic_candidates":148,
    "law_forced_coordinates":128,
    "unplaced_selected_candidates":20,
    "remaining_semantic_inventory":364,
    "ratified_d9_residents":0,
}

rows=inventory["rows"]
assert len(rows)==148
assert len({r["stable_id"] for r in rows})==148
assert len({r["semantic_name"] for r in rows})==148
assert all(r["ratified_resident"] is False for r in rows)

placed=[r for r in rows if r["coordinate"] is not None]
unplaced=[r for r in rows if r["coordinate"] is None]
assert len(placed)==128
assert len(unplaced)==20
assert len({r["coordinate"] for r in placed})==128
assert all(len(r["coordinate"])==9 and set(r["coordinate"])<=set("01") for r in placed)
assert all(r["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR" for r in placed)
assert all(r["coordinate_basis"]=="UNPLACED" for r in unplaced)

seed_ids={r["stable_id"] for r in seed["rows"]}
review_ids={r["stable_id"] for r in review["rows"] if r["selected_d9_candidate"]}
assert {r["stable_id"] for r in placed}==seed_ids
assert {r["stable_id"] for r in unplaced}==review_ids

for name in ("APPLY","COMPOSE","REDUCE"):
    assert name not in {r["semantic_name"] for r in rows}

assert state["target"]["selected_semantic_candidates"]==148
assert state["target"]["remaining_semantic_candidates"]==364
assert state["target"]["ratified_residents"]==0
assert state["semantic_inventory"]=={
    "artifact":"knowledge/d9-v1-semantic-inventory.json",
    "selected":148,
    "law_forced_coordinates":128,
    "unplaced_selected":20,
    "remaining":364,
}

print("D9-V1-SEMANTIC-INVENTORY: PASS")
print("selected=148/512 placed=128 unplaced=20 remaining=364 ratified=0")
