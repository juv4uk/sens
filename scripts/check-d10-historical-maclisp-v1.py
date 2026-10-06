#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-historical-maclisp-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
sens8=json.loads((root/"knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-historical-maclisp-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4039"
assert harvest["accounting"]=={
    "selected_d10_candidates":21,
    "d10_selected_before_harvest":367,
    "d10_selected_after_harvest":388,
    "law_forced_coordinates":256,
    "unplaced_selected_after_harvest":132,
    "d10_remaining_after_harvest":636,
    "ratified_d10_residents":0,
}

rows=harvest["rows"]
assert len(rows)==21
assert len({r["stable_id"] for r in rows})==21
assert len({r["semantic_name"] for r in rows})==21
assert all(r["selected_d10_candidate"] is True for r in rows)
assert all(r["coordinate"] is None for r in rows)
assert all(r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["legacy_coordinate_authority"]=="NONE" for r in rows)
assert all(r["implementation_class_authority"]=="NONE" for r in rows)
assert all(r["ownership"]=="CORE-OWNED-CANDIDATE" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (lower & {r["semantic_name"].upper() for r in rows})

inventory_by_id={r["stable_id"]:r for r in inventory["rows"]}
for r in rows:
    current=inventory_by_id[r["stable_id"]]
    assert current["semantic_name"]==r["semantic_name"]
    assert current["source_class"]=="HISTORICAL-MACLISP-RECOVERY"
    assert current["coordinate"] is None
    assert current["coordinate_basis"]=="UNPLACED"
    assert current["ownership"]=="CORE-OWNED-CANDIDATE"
    assert current["ratified_resident"] is False

assert inventory["accounting"]=={
    "selected_semantic_candidates":388,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":132,
    "remaining_semantic_inventory":636,
    "ratified_d10_residents":0,
}

assert state["target"]["selected_semantic_candidates"]==388
assert state["target"]["remaining_semantic_candidates"]==636
assert state["target"]["unplaced_selected_candidates"]==132
assert state["target"]["ratified_residents"]==0
assert state["historical_maclisp_v1"]["selected"]==21
assert state["historical_maclisp_v1"]["coordinates_assigned"]==0
assert state["historical_maclisp_v1"]["sens8_preservation"]=="UNCHANGED"

# Sens8 archaeology is preserved, not deleted or repurposed.
assert sens8["accounting"]["total_legacy_cells"]==256
assert sens8["accounting"]["named_rows_accounted"]==182
assert sens8["accounting"]["donor_coverage_percent"]==100

print("D10-HISTORICAL-MACLISP-1=PASS")
print("historical-selected=21 inventory=388/1024 placed=256 unplaced=132 remaining=636 ratified=0")
print("sens8=preserved coverage=100%")
