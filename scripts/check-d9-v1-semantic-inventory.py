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

target=state["target"]
selected_count=target["selected_semantic_candidates"]
remaining=target["remaining_semantic_candidates"]
assert selected_count>=148
assert remaining==512-selected_count
assert target["ratified_residents"]==0

assert inventory["accounting"]=={
    "selected_semantic_candidates":selected_count,
    "law_forced_coordinates":128,
    "unplaced_selected_candidates":selected_count-128,
    "remaining_semantic_inventory":remaining,
    "ratified_d9_residents":0,
}

rows=inventory["rows"]
assert len(rows)==selected_count
assert len({r["stable_id"] for r in rows})==selected_count
assert len({r["semantic_name"] for r in rows})==selected_count
assert all(r["ratified_resident"] is False for r in rows)

placed=[r for r in rows if r["coordinate"] is not None]
unplaced=[r for r in rows if r["coordinate"] is None]
assert len(placed)==128
assert len(unplaced)==selected_count-128
assert len({r["coordinate"] for r in placed})==128
assert all(len(r["coordinate"])==9 and set(r["coordinate"])<=set("01") for r in placed)
assert all(r["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR" for r in placed)
assert all(r["coordinate_basis"]=="UNPLACED" for r in unplaced)

seed_ids={r["stable_id"] for r in seed["rows"]}
review_ids={r["stable_id"] for r in review["rows"] if r["selected_d9_candidate"]}
placed_ids={r["stable_id"] for r in placed}
unplaced_ids={r["stable_id"] for r in unplaced}
assert placed_ids==seed_ids
assert review_ids <= unplaced_ids

surface_path=root/"knowledge/d9-surface-harvest-v1.json"
if surface_path.exists():
    surface=json.loads(surface_path.read_text(encoding="utf-8"))
    surface_ids={r["stable_id"] for r in surface["rows"] if r["selected_d9_candidate"]}
    assert surface_ids <= unplaced_ids

library_path=root/"knowledge/d9-library-harvest-v1.json"
if library_path.exists():
    library=json.loads(library_path.read_text(encoding="utf-8"))
    library_ids={r["stable_id"] for r in library["rows"] if r["selected_d9_candidate"]}
    assert library_ids <= unplaced_ids

tail_path=root/"knowledge/d9-registry-tail-v1.json"
if tail_path.exists():
    tail=json.loads(tail_path.read_text(encoding="utf-8"))
    tail_ids={r["stable_id"] for r in tail["rows"] if r["selected_d9_candidate"]}
    assert tail_ids <= unplaced_ids

for name in ("APPLY","COMPOSE","REDUCE"):
    assert name not in {r["semantic_name"] for r in rows}

assert state["semantic_inventory"]=={
    "artifact":"knowledge/d9-v1-semantic-inventory.json",
    "selected":selected_count,
    "law_forced_coordinates":128,
    "unplaced_selected":selected_count-128,
    "remaining":remaining,
}

print("D9-V1-SEMANTIC-INVENTORY: PASS")
print(f"selected={selected_count}/512 placed=128 unplaced={selected_count-128} remaining={remaining} ratified=0")
