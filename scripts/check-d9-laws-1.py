#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
laws=json.loads((root/"knowledge/d9-laws-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))

assert laws["schema"]=="d9-laws-v1/v1"
assert laws["status"]=="RESEARCH-UNRATIFIED"
assert laws["authority"]=="#3970"
assert laws["accounting"]=={
    "candidates_reviewed":20,
    "proved_family_members":7,
    "proved_distinct_independent":1,
    "underdetermined":12,
    "fixed_coordinates":0,
    "orbit_coordinates":0,
    "ratified_d9_residents":0,
}

proved=set()
for family in laws["proved_families"]:
    assert family["result"]=="PROVED"
    assert family["placement_consequence"]=="NONE"
    proved.update(family["members"])
for row in laws["proved_distinctions"]:
    assert row["result"]=="PROVED"
    assert row["placement_consequence"]=="NONE"
    proved.add(row["semantic_name"])

under={row["semantic_name"] for row in laws["underdetermined"]}
assert len(proved)==8
assert len(under)==12
assert not (proved & under)

selected=[
    row for row in inventory["rows"]
    if row["source_class"]=="D8-OVERFLOW-RECOVERY"
]
assert len(selected)==20
assert {row["semantic_name"] for row in selected}==proved|under

for row in selected:
    assert row["coordinate"] is None
    assert row["coordinate_basis"]=="UNPLACED"
    assert row["ratified_resident"] is False
    if row["semantic_name"] in proved:
        assert row["law_status"]=="PROVED-RESEARCH"
        assert row["law_family"]
        assert "#3970" in row["law_evidence"]
    else:
        assert row["law_status"]=="UNDERDETERMINED"

assert state["target"]["selected_semantic_candidates"]>=148
assert state["target"]["remaining_semantic_candidates"]==512-state["target"]["selected_semantic_candidates"]
assert state["target"]["ratified_residents"]==0
assert state["law_mining"]=={
    "artifact":"knowledge/d9-laws-v1.json",
    "witness":"scripts/research-d9-laws-1.py",
    "reviewed_non_selector_candidates":20,
    "proved_family_members":7,
    "proved_distinct_independent":1,
    "underdetermined":12,
    "coordinate_assignments":0,
    "ratification_effect":"NONE",
}

print("D9-LAWS-1-AUTHORITY=PASS")
print("proved=8 underdetermined=12 coordinates=0 ratified=0")
