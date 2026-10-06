#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
registry=(root/"lib/surface/semantic-registry.lisp").read_text(encoding="utf-8")
signatures=(root/"lib/surface/function-signatures.lisp").read_text(encoding="utf-8")
harvest=json.loads((root/"knowledge/d9-registry-harvest-v2.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))

registry_names=[
    m.group(2)
    for m in re.finditer(r'^\s*\(([01]{8})\s+\(en\s+([^()\s]+|\(\))\)', registry, flags=re.M)
    if m.group(2)!="()"
]
signature_names={
    m.group(1)
    for m in re.finditer(r'\(sig\s+"\\?\(([^()\s]+)[^"]*"\)\s+\(doc\s+"([^"]*)"\)', signatures)
}
beyond=[name for name in registry_names if name not in signature_names]

assert len(registry_names)==182
assert len(signature_names)==57
assert len(beyond)==132
assert len(set(beyond))==132

assert harvest["schema"]=="d9-registry-harvest-v2/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#3979"
assert harvest["source"]=="lib/surface/semantic-registry.lisp"
assert harvest["excluded_prior_source"]=="lib/surface/function-signatures.lisp"
assert harvest["accounting"]=={
    "named_registry_rows":182,
    "prior_signature_names":57,
    "reviewed_rows_beyond_signatures":132,
    "selected_d9_candidates":82,
    "lower_domain_or_current_projection":44,
    "internal_no_slot":4,
    "hold_semantic_review":2,
    "d9_selected_before_harvest":168,
    "d9_selected_after_harvest":250,
    "d9_remaining_after_harvest":262,
    "ratified_d9_residents":0,
}

rows=harvest["rows"]
assert len(rows)==132
assert len({row["stable_id"] for row in rows})==132
assert len({row["surface"] for row in rows})==132
assert {row["surface"] for row in rows}==set(beyond)

counts={}
for row in rows:
    counts[row["decision"]]=counts.get(row["decision"],0)+1
assert counts=={
    "LOWER-DOMAIN-OR-CURRENT-PROJECTION":44,
    "SELECT-D9-CANDIDATE":82,
    "INTERNAL-NO-SLOT":4,
    "HOLD-SEMANTIC-REVIEW":2,
}

selected=[row for row in rows if row["selected_d9_candidate"]]
assert len(selected)==82
assert all(row["decision"]=="SELECT-D9-CANDIDATE" for row in selected)
assert all(row["semantic_name"] and row["behavior"] and row["family"] for row in selected)
assert all(row["d9_coordinate"] is None for row in selected)

# Legacy registry coordinates are source-lineage only and must not enter D9 artifacts.
for row in rows:
    assert "legacy_code" not in row
    assert "legacy_coordinate" not in row
    assert "sid" not in row
assert "erased" in harvest["coordinate_policy"].lower()

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in selected:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="SEMANTIC-REGISTRY-RECOVERY"
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["relation_class"]==row["family"]
    assert candidate["ratified_resident"] is False

# Upper-domain recovery control: ordinal sequence accessors remain distinct
# from pair-algebra selectors such as CADR.
for surface in ("second","third","fourth","fifth"):
    row=next(row for row in rows if row["surface"]==surface)
    assert row["decision"]=="SELECT-D9-CANDIDATE"
    assert row["family"]=="SEQUENCE-ORDINAL"

by_surface={row["surface"]:row for row in rows}
assert by_surface["invoke"]["decision"]=="HOLD-SEMANTIC-REVIEW"
assert by_surface["binary"]["decision"]=="HOLD-SEMANTIC-REVIEW"

for surface in ("largest-chunk","nondecreasing-from?","nonincreasing-from?","digit->string"):
    assert by_surface[surface]["decision"]=="INTERNAL-NO-SLOT"

assert len(inventory["rows"])==250
assert len({row["stable_id"] for row in inventory["rows"]})==250
assert len({row["semantic_name"] for row in inventory["rows"]})==250
assert inventory["accounting"]=={
    "selected_semantic_candidates":250,
    "law_forced_coordinates":128,
    "unplaced_selected_candidates":122,
    "remaining_semantic_inventory":262,
    "ratified_d9_residents":0,
}

assert state["target"]["selected_semantic_candidates"]==250
assert state["target"]["remaining_semantic_candidates"]==262
assert state["target"]["ratified_residents"]==0
assert state["registry_harvest_v2"]=={
    "artifact":"knowledge/d9-registry-harvest-v2.json",
    "reviewed_rows":132,
    "selected":82,
    "lower_or_current_projection":44,
    "internal_no_slot":4,
    "hold":2,
    "coordinates_assigned":0,
}

print("D9-REGISTRY-HARVEST-2=PASS")
print("reviewed=132 selected=82 lower/current=44 internal=4 hold=2")
print("inventory=250/512 placed=128 unplaced=122 remaining=262 ratified=0")
