#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
candidate=json.loads((root/"knowledge/d9-v1-gauge-fixed-candidate.json").read_text(encoding="utf-8"))
geometry=json.loads((root/"knowledge/d9-v1-geometry-state.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
laws=json.loads((root/"knowledge/d9-geometry-laws-s3.json").read_text(encoding="utf-8"))

assert candidate["schema"]=="d9-v1-gauge-fixed-candidate/v1"
assert candidate["status"]=="RESEARCH-GAUGE-FIXED-CANDIDATE"
assert candidate["authority"]=="#4005"
assert candidate["width"]==9 and candidate["capacity"]==512
assert candidate["occupancy"]==512
assert candidate["ratified_residents"]==0
assert candidate["basis_counts"]=={
    "GAUGE-FIXED":384,
    "LAW-FORCED":128,
}

rows=candidate["rows"]
assert len(rows)==512
assert len({row["coordinate"] for row in rows})==512
assert len({row["stable_id"] for row in rows})==512
assert len({row["semantic_name"] for row in rows})==512
assert {row["coordinate"] for row in rows}=={f"{i:09b}" for i in range(512)}

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
assert len(inventory_by_id)==512
assert {row["stable_id"] for row in rows}==set(inventory_by_id)

by_coord={row["coordinate"]:row for row in rows}

# 128 theorem-fixed selectors must survive exactly.
for fixed in geometry["fixed_assignments"]:
    got=by_coord[fixed["coordinate"]]
    assert got["stable_id"]==fixed["stable_id"]
    assert got["semantic_name"]==fixed["semantic_name"]
    assert got["basis"]=="LAW-FORCED"

fixed_coords={row["coordinate"] for row in rows if row["basis"]=="LAW-FORCED"}
assert len(fixed_coords)==128

# Recompute residual S4 zip from coordinate-independent semantic IDs.
free=sorted({f"{i:09b}" for i in range(512)}-fixed_coords)
unplaced=sorted(
    geometry["fully_unplaced_meanings"],
    key=lambda row: row["stable_id"],
)
assert len(free)==384
assert len(unplaced)==384

for coord,semantic in zip(free,unplaced):
    got=by_coord[coord]
    assert got["stable_id"]==semantic["stable_id"]
    assert got["semantic_name"]==semantic["semantic_name"]
    assert got["basis"]=="GAUGE-FIXED"
    assert got["placement_evidence"].startswith("S4 deterministic")

# Gauge rows cannot be selector seed rows.
assert all(
    not row["stable_id"].startswith("d9.sel.")
    for row in rows
    if row["basis"]=="GAUGE-FIXED"
)

assert laws["accounting"]["fixed_coordinate_consequences"]==0
assert laws["accounting"]["orbit_coordinate_consequences"]==0
assert laws["accounting"]["none_coordinate_consequences"]==7
assert geometry["accounting"]["free_coordinates_after_fixed"]==384
assert candidate["ratified_residents"]==0

print("D9-GAUGE-S4=PASS")
print("candidate=512/512 law-forced=128 gauge-fixed=384 ratified=0")
