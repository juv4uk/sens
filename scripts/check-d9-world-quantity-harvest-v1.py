#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d9-world-quantity-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d9-world-quantity-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#3992"
assert harvest["accounting"]=={
    "selected_d9_candidates":62,
    "world":32,
    "quantity":30,
    "d9_selected_before_harvest":313,
    "d9_selected_after_harvest":375,
    "d9_remaining_after_harvest":137,
    "ratified_d9_residents":0,
}

rows=harvest["rows"]
assert len(rows)==62
assert len({row["stable_id"] for row in rows})==62
assert len({row["semantic_name"] for row in rows})==62
assert len({(row["source_file"],row["source_name"]) for row in rows})==62
assert all(row["decision"]=="SELECT-D9-CANDIDATE" for row in rows)
assert all(row["selected_d9_candidate"] is True for row in rows)
assert all(row["coordinate"] is None for row in rows)
assert all(row["coordinate_basis"]=="UNPLACED" for row in rows)
assert all(row["ratified_resident"] is False for row in rows)

expected_sources={
    "lib/world.lisp":32,
    "lib/quantity.lisp":30,
}
actual_sources={}
for row in rows:
    actual_sources[row["source_file"]]=actual_sources.get(row["source_file"],0)+1
assert actual_sources==expected_sources

for source_file,count in expected_sources.items():
    text=(root/source_file).read_text(encoding="utf-8")
    defs={m.group(1) for m in re.finditer(r'^\([01]{8}\s+([^\s()]+)\s+', text, re.MULTILINE)}
    claimed={row["source_name"] for row in rows if row["source_file"]==source_file}
    assert len(claimed)==count
    assert claimed <= defs

lower_names=set()
for domain in foundation["domains"].values():
    lower_names.update(str(name).lower() for name in domain.get("residents",{}).values())
assert not (lower_names & {row["source_name"].lower() for row in rows})

assert set(harvest["constant_boundary"]["excluded_sources"])=={"lib/si.lisp","lib/si-derived.lisp"}
assert all(not row["source_file"].startswith("lib/si") for row in rows)

for row in rows:
    assert "legacy_code" not in row
    assert "legacy_coordinate" not in row
    assert "sid" not in row
assert "zero D9 placement authority" in harvest["coordinate_policy"]

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in rows:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="WORLD-QUANTITY-HARVEST"
    assert candidate["source_name"]==row["source_name"]
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=375
assert target["remaining_semantic_candidates"]==512-target["selected_semantic_candidates"]
assert target["ratified_residents"]==0

assert len(inventory["rows"])==target["selected_semantic_candidates"]
assert len({row["stable_id"] for row in inventory["rows"]})==target["selected_semantic_candidates"]
assert len({row["semantic_name"] for row in inventory["rows"]})==target["selected_semantic_candidates"]

assert state["world_quantity_harvest"]=={
    "artifact":"knowledge/d9-world-quantity-harvest-v1.json",
    "selected":62,
    "coordinates_assigned":0,
    "concrete_si_constants_excluded":True,
}

print("D9-WORLD-QUANTITY-HARVEST-1=PASS")
selected_total=target["selected_semantic_candidates"]\nremaining_total=target["remaining_semantic_candidates"]\nprint(f"selected=62 inventory={selected_total}/512 placed=128 unplaced={selected_total-128} remaining={remaining_total} ratified=0")
