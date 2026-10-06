#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d9-semantic-layer-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d9-semantic-layer-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#3990"
assert harvest["accounting"]=={
    "selected_d9_candidates":65,
    "content_store":6,
    "result_status":14,
    "narrate":9,
    "understand":7,
    "utf8":5,
    "translation":16,
    "guard":8,
    "d9_selected_before_harvest":248,
    "d9_selected_after_harvest":313,
    "d9_remaining_after_harvest":199,
    "ratified_d9_residents":0,
}

rows=harvest["rows"]
assert len(rows)==65
assert len({row["stable_id"] for row in rows})==65
assert len({row["semantic_name"] for row in rows})==65
assert len({(row["source_file"],row["source_name"]) for row in rows})==65
assert all(row["decision"]=="SELECT-D9-CANDIDATE" for row in rows)
assert all(row["selected_d9_candidate"] is True for row in rows)
assert all(row["coordinate"] is None for row in rows)
assert all(row["coordinate_basis"]=="UNPLACED" for row in rows)
assert all(row["ratified_resident"] is False for row in rows)

expected_sources={
    "lib/content-store.lisp":6,
    "lib/result-status.lisp":14,
    "lib/narrate.lisp":9,
    "lib/understand.lisp":7,
    "lib/utf8.lisp":5,
    "lib/translation.lisp":16,
    "lib/guard.lisp":8,
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

for row in rows:
    assert "legacy_code" not in row
    assert "legacy_coordinate" not in row
    assert "sid" not in row
assert "zero D9 placement authority" in harvest["coordinate_policy"]

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in rows:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="CANONICAL-SEMANTIC-LAYER-HARVEST"
    assert candidate["source_name"]==row["source_name"]
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=313
assert target["remaining_semantic_candidates"]==512-target["selected_semantic_candidates"]
assert target["ratified_residents"]==0

assert len(inventory["rows"])==target["selected_semantic_candidates"]
assert len({row["stable_id"] for row in inventory["rows"]})==target["selected_semantic_candidates"]
assert len({row["semantic_name"] for row in inventory["rows"]})==target["selected_semantic_candidates"]

assert state["semantic_layer_harvest"]=={
    "artifact":"knowledge/d9-semantic-layer-harvest-v1.json",
    "selected":65,
    "coordinates_assigned":0,
    "internal_helpers_excluded":True,
}

print("D9-SEMANTIC-LAYER-HARVEST-1=PASS")
selected_total=target["selected_semantic_candidates"]
remaining_total=target["remaining_semantic_candidates"]
print(f"selected=65 inventory={selected_total}/512 placed=128 unplaced={selected_total-128} remaining={remaining_total} ratified=0")
