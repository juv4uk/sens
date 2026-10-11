#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
geometry=json.loads((root/"knowledge/d9-v1-geometry-state.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))

assert geometry["schema"]=="d9-v1-geometry-state/v1"
assert geometry["status"]=="RESEARCH-S2"
assert geometry["authority"]=="#3999"
assert geometry["width"]==9 and geometry["capacity"]==512
assert geometry["accounting"]=={
    "selected_meanings":512,
    "fixed_coordinate_meanings":128,
    "selector_fixed":128,
    "free_coordinates_after_fixed":384,
    "fully_unplaced_meanings":384,
    "ratified_d9_residents":0,
}

assert inventory["status"]=="RESEARCH-UNRATIFIED-COMPLETE"
assert len(inventory["rows"])==512
selected={row["semantic_name"] for row in inventory["rows"]}
assert len(selected)==512

fixed=geometry["fixed_assignments"]
fixed_coords={row["coordinate"] for row in fixed}
fixed_names={row["semantic_name"] for row in fixed}
assert len(fixed)==128
assert len(fixed_coords)==128
assert len(fixed_names)==128
assert all(len(coord)==9 and set(coord)<=set("01") for coord in fixed_coords)
assert all(row["status"]=="LAW-FORCED-CANDIDATE" for row in fixed)
assert all(row["placement_basis"]=="PROVED-SELECTOR-GENERATOR" for row in fixed)
assert all(row["source_class"]=="SELECTOR-GENERATOR" for row in fixed)

# Current selector family inherits the D3 selector roots through D8.
assert all(coord.startswith(("011","100")) for coord in fixed_coords)

unplaced=geometry["fully_unplaced_meanings"]
unplaced_ids={row["stable_id"] for row in unplaced}
unplaced_names={row["semantic_name"] for row in unplaced}
assert len(unplaced)==384
assert len(unplaced_ids)==384
assert len(unplaced_names)==384
assert all(row["status"]=="UNPLACED" for row in unplaced)

assert not (fixed_names & unplaced_names)
assert fixed_names | unplaced_names == selected

free=geometry["free_coordinates_after_fixed"]
assert len(free)==384
assert len(set(free))==384
assert all(len(coord)==9 and set(coord)<=set("01") for coord in free)
assert not (set(free) & fixed_coords)
assert set(free) | fixed_coords == {f"{i:09b}" for i in range(512)}

# Exact replay from semantic inventory.
inventory_fixed={
    row["coordinate"]:row["semantic_name"]
    for row in inventory["rows"]
    if row["coordinate"] is not None
}
geometry_fixed={row["coordinate"]:row["semantic_name"] for row in fixed}
assert geometry_fixed==inventory_fixed

inventory_unplaced={
    row["stable_id"]:row["semantic_name"]
    for row in inventory["rows"]
    if row["coordinate"] is None
}
geometry_unplaced={row["stable_id"]:row["semantic_name"] for row in unplaced}
assert geometry_unplaced==inventory_unplaced

assert geometry["accounting"]["ratified_d9_residents"]==0

print("D9-GEOMETRY-S2=PASS")
print("selected=512 fixed=128 free=384 unplaced=384 ratified=0")
