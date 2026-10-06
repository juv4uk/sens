#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
d9=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
seed=json.loads((root/"knowledge/d10-selector-seed.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")

def child_name(parent: str, bit: str) -> str:
    assert parent.endswith("R")
    return parent[:-1] + ("A" if bit=="0" else "D") + "R"

assert seed["schema"]=="d10-selector-seed/v1"
assert seed["status"]=="RESEARCH-UNRATIFIED"
assert seed["authority"]=="#4012"
assert seed["domain"]=="D10" and seed["width"]==10
assert seed["target_capacity"]==1024
assert seed["accounting"]=={
    "d9_selector_parents":128,
    "generated_d10_selector_candidates":256,
    "target_d10_capacity":1024,
    "remaining_semantic_inventory":768,
    "ratified_d10_residents":0,
}

parents=sorted(
    (row for row in d9["rows"] if row["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR" and row["coordinate"] is not None),
    key=lambda row: row["coordinate"],
)
assert len(parents)==128
assert d9["accounting"]["selected_semantic_candidates"]==512
assert d9["accounting"]["ratified_d9_residents"]==0

expected=[]
for parent in parents:
    for bit in ("0","1"):
        expected.append((
            parent["coordinate"]+bit,
            child_name(parent["semantic_name"],bit),
            parent["coordinate"],
            parent["semantic_name"],
            bit,
        ))

rows=sorted(seed["rows"],key=lambda row: row["coordinate"])
assert len(rows)==256
assert len({row["coordinate"] for row in rows})==256
assert len({row["semantic_name"] for row in rows})==256
assert all(len(row["coordinate"])==10 and set(row["coordinate"])<=set("01") for row in rows)

for row,(coord,name,pcoord,pname,bit) in zip(rows,expected):
    assert row["coordinate"]==coord
    assert row["semantic_name"]==name
    assert row["parent_coordinate"]==pcoord
    assert row["parent_semantic_name"]==pname
    assert row["generator_suffix_bit"]==bit
    assert row["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR"
    assert row["relation_class"]=="SEMANTIC-GENERATOR"
    assert row["ratified_resident"] is False

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
lower.update(row["semantic_name"].upper() for row in d9["rows"])
assert not (lower & {row["semantic_name"].upper() for row in rows})

assert inventory["schema"]=="d10-v1-semantic-inventory/v1"
assert inventory["status"]=="RESEARCH-UNRATIFIED-PARTIAL"
assert inventory["domain"]=="D10" and inventory["width"]==10 and inventory["capacity"]==1024
assert inventory["accounting"]=={
    "selected_semantic_candidates":256,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":0,
    "remaining_semantic_inventory":768,
    "ratified_d10_residents":0,
}
assert len(inventory["rows"])==256
assert len({row["stable_id"] for row in inventory["rows"]})==256
assert len({row["semantic_name"] for row in inventory["rows"]})==256
assert len({row["coordinate"] for row in inventory["rows"]})==256
assert all(row["ratified_resident"] is False for row in inventory["rows"])

assert state["target"]=={
    "domain":"D10",
    "width":10,
    "capacity":1024,
    "dense_target":1024,
    "selected_semantic_candidates":256,
    "remaining_semantic_candidates":768,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":0,
    "ratified_residents":0,
}
assert state["foundation"]["d9_ratified"] is False
assert state["authority_boundary"]["d9_unratified_coordinates"]=="NO D10 AUTHORITY"
assert state["authority_boundary"]["d9_selector_law"].startswith("MAY CROSS")

assert foundation["authority"]=="#3960"
assert "(minor . 7)" in lang
assert "Contract 11.7" in lang

print("D10-FILL-V1-SEED: PASS")
print("selectors=256/1024 remaining=768 ratified-D10=0")
