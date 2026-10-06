#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=(root/"lib/surface/function-signatures.lisp").read_text(encoding="utf-8")
harvest=json.loads((root/"knowledge/d9-surface-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))

signatures=[
    {"surface":m.group(1),"doc":m.group(2)}
    for m in re.finditer(r'\(sig\s+"\\?\(([^()\s]+)[^"]*"\)\s+\(doc\s+"([^"]*)"\)', source)
]
assert len(signatures)==57

assert harvest["schema"]=="d9-surface-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#3977"
assert harvest["source"]=="lib/surface/function-signatures.lisp"
assert harvest["accounting"]=={
    "source_signatures":57,
    "selected_d9_candidates":20,
    "lower_domain_or_surface_projection":30,
    "hold_semantic_review":7,
    "d9_selected_before_harvest":148,
    "d9_selected_after_harvest":168,
    "d9_remaining_after_harvest":344,
    "ratified_d9_residents":0,
}

rows=harvest["rows"]
assert len(rows)==57
assert len({row["stable_id"] for row in rows})==57
assert len({row["surface"] for row in rows})==57
assert {row["surface"] for row in rows}=={row["surface"] for row in signatures}

counts={}
for row in rows:
    counts[row["decision"]]=counts.get(row["decision"],0)+1
assert counts=={
    "SELECT-D9-CANDIDATE":20,
    "LOWER-DOMAIN-OR-SURFACE-PROJECTION":30,
    "HOLD-SEMANTIC-REVIEW":7,
}

selected=[row for row in rows if row["selected_d9_candidate"]]
assert len(selected)==20
assert all(row["decision"]=="SELECT-D9-CANDIDATE" for row in selected)
assert all(row["semantic_name"] for row in selected)
assert all(row["d9_coordinate"] is None for row in selected)

# Старі registry-коди не можуть просочитися у harvest artifact.
assert "coordinate_policy" in harvest
assert "ignored" in harvest["coordinate_policy"].lower()
for row in rows:
    assert "legacy_coordinate" not in row
    assert "sid" not in row

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in selected:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="PUBLIC-SIGNATURE-HARVEST"
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=168
assert target["remaining_semantic_candidates"]==512-target["selected_semantic_candidates"]
assert target["ratified_residents"]==0

assert len(inventory["rows"])==target["selected_semantic_candidates"]
assert len({row["stable_id"] for row in inventory["rows"]})==target["selected_semantic_candidates"]
assert len({row["semantic_name"] for row in inventory["rows"]})==target["selected_semantic_candidates"]

assert state["surface_harvest"]=={
    "artifact":"knowledge/d9-surface-harvest-v1.json",
    "source_signatures":57,
    "selected":20,
    "lower_or_surface_projection":30,
    "hold":7,
    "coordinates_assigned":0,
}

print("D9-SURFACE-HARVEST-1=PASS")
print("signatures=57 selected=20 lower/projection=30 hold=7")
selected_total=target["selected_semantic_candidates"]
remaining_total=target["remaining_semantic_candidates"]
print(f"inventory={selected_total}/512 placed=128 unplaced={selected_total-128} remaining={remaining_total} ratified=0")
