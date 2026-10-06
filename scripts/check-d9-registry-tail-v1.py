#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
review=json.loads((root/"knowledge/d9-registry-tail-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))
registry=(root/"lib/surface/semantic-registry.lisp").read_text(encoding="utf-8")
uk_inventory=(root/"lib/surface/uk-inventory.lisp").read_text(encoding="utf-8")
selector_research=(root/"scripts/research-1962-selector-compression.py").read_text(encoding="utf-8")

assert review["schema"]=="d9-registry-tail-v1/v1"
assert review["status"]=="RESEARCH-UNRATIFIED"
assert review["authority"]=="#3985"
assert review["source"]=="lib/surface/semantic-registry.lisp"
assert review["accounting"]=={
    "source_rows":39,
    "selected_d9_candidates":22,
    "lower_domain_or_surface_projection":12,
    "internal_helpers":4,
    "hold_mechanism":1,
    "d9_selected_before_review":226,
    "d9_selected_after_review":248,
    "d9_remaining_after_review":264,
    "ratified_d9_residents":0,
}

rows=review["rows"]
assert len(rows)==39
assert len({row["stable_id"] for row in rows})==39
assert len({row["registry_name"] for row in rows})==39

counts={}
for row in rows:
    counts[row["decision"]]=counts.get(row["decision"],0)+1
assert counts=={
    "SELECT-D9-CANDIDATE":22,
    "INTERNAL-HELPER":4,
    "LOWER-DOMAIN-OR-SURFACE-PROJECTION":12,
    "HOLD-MECHANISM":1,
}

# Every reviewed name must actually be an English registry surface.
registry_names={m.group(1) for m in re.finditer(r'^\s*\([01]{8}\s+\(en\s+([^()\s]+|\(\))\)', registry, re.MULTILINE)}
assert {row["registry_name"] for row in rows} <= registry_names

# Old registry coordinates are intentionally absent.
assert "zero D9 placement authority" in review["coordinate_policy"]
for row in rows:
    assert "legacy_code" not in row
    assert "legacy_coordinate" not in row
    assert "sid" not in row
    assert row["coordinate"] is None
    assert row["ratified_resident"] is False

# Lower/projection rows must point to real current lower identities.
expected_lower={
    "lessp?":("D5","11010","LESSP"),
    "greaterp?":("D5","11011","GREATERP"),
    "equalp?":("D8","11110111","EQUAL"),
    "not-greaterp?":("D6","110100","LEQ"),
    "not-lessp?":("D6","110110","GEQ"),
    "not?":("D4","0100","NOT"),
    "equal?":("D8","11110111","EQUAL"),
    "member?":("D5","11101","MEMBER"),
    "second":("D4","1001","CADR"),
    "third":("D5","10011","CADDR"),
    "fourth":("D6","100111","CADDDR"),
    "null?":("D4","0101","NULL"),
}
by_name={row["registry_name"]:row for row in rows}
for name,(domain,coord,resident) in expected_lower.items():
    row=by_name[name]
    assert row["decision"]=="LOWER-DOMAIN-OR-SURFACE-PROJECTION"
    assert foundation["domains"][domain]["residents"][coord]==resident
    assert resident in row["lower_identity"]

# Internal helpers are explicitly classified internal by the public-surface inventory.
for name in ("largest-chunk","nondecreasing-from?","nonincreasing-from?","digit->string"):
    assert by_name[name]["decision"]=="INTERNAL-HELPER"
    assert name in uk_inventory

assert by_name["invoke"]["decision"]=="HOLD-MECHANISM"
assert by_name["invoke"]["selected_d9_candidate"] is False

# FIFTH is the skipped-selector recovery: it is not a current D1-D8 resident.
lower_names=set()
for domain in foundation["domains"].values():
    lower_names.update(domain.get("residents",{}).values())
assert "FIFTH" not in lower_names
assert "CADDDDR" not in lower_names
assert by_name["fifth"]["decision"]=="SELECT-D9-CANDIDATE"
assert "fifth" in selector_research and "CADDDDR" in selector_research

# Every selected source binding must exist in the claimed language-owned file.
selected=[row for row in rows if row["selected_d9_candidate"]]
assert len(selected)==22
source_cache={}
for row in selected:
    path=row["source_file"]
    if path not in source_cache:
        source_cache[path]=(root/path).read_text(encoding="utf-8")
    defs={m.group(1) for m in re.finditer(r'^\([01]{8}\s+([^\s()]+)\s+', source_cache[path], re.MULTILINE)}
    assert row["source_binding"] in defs, (row["semantic_name"],row["source_binding"],path)

inventory_by_id={row["stable_id"]:row for row in inventory["rows"]}
for row in selected:
    candidate=inventory_by_id[row["stable_id"]]
    assert candidate["semantic_name"]==row["semantic_name"]
    assert candidate["source_class"]=="SEMANTIC-REGISTRY-TAIL-RECOVERY"
    assert candidate["coordinate"] is None
    assert candidate["coordinate_basis"]=="UNPLACED"
    assert candidate["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=248
assert target["remaining_semantic_candidates"]==512-target["selected_semantic_candidates"]
assert target["ratified_residents"]==0

assert len(inventory["rows"])==target["selected_semantic_candidates"]
assert len({row["stable_id"] for row in inventory["rows"]})==target["selected_semantic_candidates"]
assert len({row["semantic_name"] for row in inventory["rows"]})==target["selected_semantic_candidates"]

assert state["registry_tail_review"]=={
    "artifact":"knowledge/d9-registry-tail-v1.json",
    "source_rows":39,
    "selected":22,
    "lower_or_projection":12,
    "internal":4,
    "hold_mechanism":1,
    "coordinates_assigned":0,
}

print("D9-REGISTRY-TAIL-1=PASS")
print("rows=39 selected=22 lower/projection=12 internal=4 hold=1")
selected_total=target["selected_semantic_candidates"]
remaining_total=target["remaining_semantic_candidates"]
print(f"inventory={selected_total}/512 placed=128 unplaced={selected_total-128} remaining={remaining_total} ratified=0")
