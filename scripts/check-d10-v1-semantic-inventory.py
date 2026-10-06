#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
seed=json.loads((root/"knowledge/d10-selector-seed.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

target=state["target"]
selected=target["selected_semantic_candidates"]
remaining=target["remaining_semantic_candidates"]

assert inventory["schema"]=="d10-v1-semantic-inventory/v1"
assert inventory["status"]=="RESEARCH-UNRATIFIED-PARTIAL"
assert inventory["domain"]=="D10"
assert inventory["width"]==10
assert inventory["capacity"]==1024
assert selected>=256
assert remaining==1024-selected
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==selected-256
assert target["ratified_residents"]==0

assert inventory["accounting"]=={
    "selected_semantic_candidates":selected,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":selected-256,
    "remaining_semantic_inventory":remaining,
    "ratified_d10_residents":0,
}

rows=inventory["rows"]
assert len(rows)==selected
assert len({r["stable_id"] for r in rows})==selected
assert len({r["semantic_name"] for r in rows})==selected
assert all(r["ratified_resident"] is False for r in rows)

placed=[r for r in rows if r["coordinate"] is not None]
unplaced=[r for r in rows if r["coordinate"] is None]
assert len(placed)==256
assert len(unplaced)==selected-256
assert len({r["coordinate"] for r in placed})==256
assert all(len(r["coordinate"])==10 and set(r["coordinate"])<=set("01") for r in placed)
assert all(r["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR" for r in placed)
assert all(r["coordinate_basis"]=="UNPLACED" for r in unplaced)

seed_ids={r["stable_id"] for r in seed["rows"]}
assert {r["stable_id"] for r in placed}==seed_ids

recovery_path=root/"knowledge/d10-recovery-v1.json"
if recovery_path.exists():
    recovery=json.loads(recovery_path.read_text(encoding="utf-8"))
    recovery_ids={r["stable_id"] for r in recovery["rows"] if r["selected_d10_candidate"]}
    assert recovery_ids <= {r["stable_id"] for r in unplaced}

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (lower & {r["semantic_name"].upper() for r in rows})

print("D10-V1-SEMANTIC-INVENTORY: PASS")
print(f"selected={selected}/1024 placed=256 unplaced={selected-256} remaining={remaining} ratified=0")
