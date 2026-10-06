#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d9-library-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d9-library-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#3983"
assert harvest["accounting"]=={
    "selected_d9_candidates":58,
    "persistent_map":5,
    "persistent_vector":6,
    "reasoning":7,
    "unification":6,
    "epistemic":11,
    "knowledge":9,
    "time":14,
    "d9_selected_before_harvest":168,
    "d9_selected_after_harvest":226,
    "d9_remaining_after_harvest":286,
    "ratified_d9_residents":0,
}

rows=harvest["rows"]
assert len(rows)==58
assert len({row["stable_id"] for row in rows})==58
assert len({row["semantic_name"] for row in rows})==58
assert len({(row["source_file"],row["source_name"]) for row in rows})==58
assert all(row["decision"]=="SELECT-D9-CANDIDATE" for row in rows)
assert all(row["selected_d9_candidate"] is True for row in rows)
assert all(row["coordinate"] is None for row in rows)
assert all(row["coordinate_basis"]=="UNPLACED" for row in rows)
assert all(row["old_registry_coordinate_authority"]=="NONE" for row in rows)
assert all(row["ratified_resident"] is False for row in rows)

expected_sources={
    "lib/persistent-map.lisp":5,
    "lib/persistent-vector.lisp":6,
    "lib/reason.lisp":7,
    "lib/unify.lisp":6,
    "lib/epistemic.lisp":11,
    "lib/knowledge.lisp":9,
    "lib/time.lisp":14,
}
actual_sources={}
for row in rows:
    actual_sources[row["source_file"]]=actual_sources.get(row["source_file"],0)+1
assert actual_sources==expected_sources

# Every selected source name must be an actual top-level semantic definition
# in the claimed Lisp file.
for source_file,count in expected_sources.items():
    text=(root/source_file).read_text(encoding="utf-8")
    defs={m.group(1) for m in re.finditer(r'^\([01]{8}\s+([^\s()]+)\s+', text, re.MULTILINE)}
    claimed={row["source_name"] for row in rows if row["source_file"]==source_file}
    assert len(claimed)==count
    assert claimed <= defs

# Do not silently reintroduce exact resident names from D1-D8.
lower_names=set()
for domain in foundation["domains"].values():
    lower_names.update(str(name).lower() for name in domain.get("residents",{}).values())
assert not (lower_names & {row["source_name"].lower() for row in rows})

# Raw host mechanisms are explicitly outside this language-owned tranche.
excluded=set(harvest["host_boundary"]["excluded_raw_mechanisms"])
assert excluded=={"unix-time-now","ntp-query-raw","timezone-declarations-raw"}
assert not (excluded & {row["source_name"] for row in rows})

# Old semantic-registry coordinates must not be carried as placement facts.
for row in rows:
    assert "legacy_code" not in row
    assert "legacy_coordinate" not in row
    assert "sid" not in row
assert "zero D9 placement authority" in harvest["coordinate_policy"]

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in rows:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="CANONICAL-LISP-LIBRARY-HARVEST"
    assert candidate["source_name"]==row["source_name"]
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["ratified_resident"] is False

assert len(inventory["rows"])==226
assert len({row["stable_id"] for row in inventory["rows"]})==226
assert len({row["semantic_name"] for row in inventory["rows"]})==226
assert inventory["accounting"]=={
    "selected_semantic_candidates":226,
    "law_forced_coordinates":128,
    "unplaced_selected_candidates":98,
    "remaining_semantic_inventory":286,
    "ratified_d9_residents":0,
}

assert state["target"]["selected_semantic_candidates"]==226
assert state["target"]["remaining_semantic_candidates"]==286
assert state["target"]["ratified_residents"]==0
assert state["library_harvest"]=={
    "artifact":"knowledge/d9-library-harvest-v1.json",
    "selected":58,
    "coordinates_assigned":0,
    "raw_host_mechanisms_excluded":3,
}

print("D9-LIBRARY-HARVEST-1=PASS")
print("selected=58 inventory=226/512 placed=128 unplaced=98 remaining=286 ratified=0")
