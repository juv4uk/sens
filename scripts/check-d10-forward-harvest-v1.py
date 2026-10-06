#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-forward-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
source=(root/"lib/forward.lisp").read_text(encoding="utf-8")

assert harvest["schema"]=="d10-forward-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4028"
assert harvest["accounting"]=={
    "selected_d10_candidates":26,
    "jtms_state_algebra":3,
    "jtms_condition_matching":4,
    "rule_condition_recognizers":6,
    "rule_condition_matching":10,
    "multi_forward_execution":3,
    "d10_selected_before_harvest":304,
    "d10_selected_after_harvest":330,
    "d10_remaining_after_harvest":694,
    "law_forced_coordinates":256,
    "unplaced_selected_after_harvest":74,
    "ratified_d10_residents":0,
}

rows=harvest["rows"]
assert len(rows)==26
assert len({r["stable_id"] for r in rows})==26
assert len({r["semantic_name"] for r in rows})==26
assert all(r["coordinate"] is None for r in rows)
assert all(r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["legacy_coordinate_authority"]=="NONE" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)

defs={m.group(1) for m in re.finditer(r'^\([01]{8}\s+([^\s()]+)\s+',source,re.MULTILINE)}
claimed={r["source_name"] for r in rows}
assert claimed <= defs

excluded={
    "*working-memory*","*justified-memory*","*jtms-memory*",
    "find-entry","map-apply-head","map-apply-head-jtms",
}
assert set(harvest["excluded_no_slot"])==excluded
assert not (claimed & excluded)

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).lower() for name in domain.get("residents",{}).values())
assert not (lower & {r["source_name"].lower() for r in rows})

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="FORWARD-JTMS-HARVEST"
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

assert len(inventory["rows"])==330
assert len({r["stable_id"] for r in inventory["rows"]})==330
assert len({r["semantic_name"] for r in inventory["rows"]})==330
assert inventory["accounting"]=={
    "selected_semantic_candidates":330,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":74,
    "remaining_semantic_inventory":694,
    "ratified_d10_residents":0,
}

assert state["target"]["selected_semantic_candidates"]==330
assert state["target"]["remaining_semantic_candidates"]==694
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==74
assert state["target"]["ratified_residents"]==0

print("D10-FORWARD-HARVEST-V1=PASS")
print("selected=26 inventory=330/1024 placed=256 unplaced=74 remaining=694 ratified=0")
