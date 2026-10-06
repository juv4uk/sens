#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
laws=json.loads((root/"knowledge/d9-geometry-laws-s3.json").read_text(encoding="utf-8"))
geometry=json.loads((root/"knowledge/d9-v1-geometry-state.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))

assert laws["schema"]=="d9-geometry-laws-s3/v1"
assert laws["status"]=="RESEARCH-S3"
assert laws["authority"]=="#4003"
assert laws["accounting"]=={
    "families_tested":7,
    "semantic_members_covered":38,
    "proved_families":7,
    "fixed_coordinate_consequences":0,
    "orbit_coordinate_consequences":0,
    "none_coordinate_consequences":7,
    "ratified_d9_residents":0,
}

by_name={row["semantic_name"]:row for row in inventory["rows"]}
covered=set()
for family in laws["families"]:
    assert family["result"]=="PROVED"
    assert family["placement_consequence"]=="NONE"
    assert family["coordinate_permutation_attack"]["result"]=="INVARIANT"
    for name in family["members"]:
        assert name in by_name
        assert by_name[name]["coordinate"] is None
        assert by_name[name]["coordinate_basis"]=="UNPLACED"
        covered.add(name)

assert len(covered)==38

# S3 must not mutate S2 geometry.
assert geometry["accounting"]=={
    "selected_meanings":512,
    "fixed_coordinate_meanings":128,
    "selector_fixed":128,
    "free_coordinates_after_fixed":384,
    "fully_unplaced_meanings":384,
    "ratified_d9_residents":0,
}
assert laws["conclusion"]=={
    "geometry_change":"NONE",
    "fixed_coordinates_remain":128,
    "free_coordinates_remain":384,
    "unplaced_meanings_remain":384,
    "next_step":"If no stronger coordinate-sensitive law is recovered, emit a deterministic S4 gauge representative over the residual 384-coordinate equivalence class.",
}

assert "permutations" in laws["theorem_boundary"]
assert laws["accounting"]["ratified_d9_residents"]==0

print("D9-GEOMETRY-LAWS-S3-AUTHORITY=PASS")
print("families=7 covered=38 fixed-consequence=0 orbit-consequence=0 geometry=128/384 ratified=0")
