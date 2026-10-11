#!/usr/bin/env python3
import json
from pathlib import Path

# Python -O вимикає assert — у цьому режимі доказів D10 немає.
if not __debug__:
    raise SystemExit("D10-FILL-V1-SEED: BLOCKED — Python -O вимикає перевірки")

root=Path(__file__).resolve().parents[1]
d9=json.loads((root/"knowledge/d9-ratified.json").read_text(encoding="utf-8"))
seed=json.loads((root/"knowledge/d10-selector-seed.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")

def child_name(parent: str, bit: str) -> str:
    assert parent.endswith("R")
    return parent[:-1] + ("A" if bit=="0" else "D") + "R"

assert d9["status"]=="owner-ratified"
assert d9["authority"]=="#4008"
assert d9["occupancy"]==512
assert d9["distinct_residents"]==512

assert seed["schema"]=="d10-selector-seed/v1"
assert seed["status"]=="RESEARCH-UNRATIFIED"
assert seed["authority"]=="#4012"
assert seed["domain"]=="D10" and seed["width"]==10
assert seed["target_capacity"]==1024
assert seed["source_foundation"]=={
    "current_contract":"11.8",
    "current_ratified_foundation":"#4008 / D1-D9",
    "parent_domain":"D9",
    "d9_ratified_map":"knowledge/d9-ratified.json",
    "d9_occupancy":512,
    "d9_ratified":True,
    "d9_selector_parent_count":128,
}
assert seed["accounting"]=={
    "d9_selector_parents":128,
    "generated_d10_selector_candidates":256,
    "target_d10_capacity":1024,
    "remaining_semantic_inventory":768,
    "ratified_d10_residents":0,
}

parents=sorted(
    (row for row in d9["rows"] if row["coordinate_basis"]=="proved-selector-generator"),
    key=lambda row: row["coordinate"],
)
assert len(parents)==128

expected=[]
for parent in parents:
    for bit in ("0","1"):
        expected.append((
            parent["coordinate"]+bit,
            child_name(parent["resident"],bit),
            parent["coordinate"],
            parent["resident"],
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
    assert "#4008" in row["authority"]
    assert "knowledge/d9-ratified.json" in row["authority"]

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (lower & {row["semantic_name"].upper() for row in rows})

assert inventory["schema"]=="d10-v1-semantic-inventory/v1"
assert inventory["status"]=="RESEARCH-UNRATIFIED-PARTIAL"
assert inventory["domain"]=="D10" and inventory["width"]==10 and inventory["capacity"]==1024
assert inventory["current_foundation"]=="#4008 / Contract 11.8 / D1-D9"
assert inventory["parent_domain"]=={
    "domain":"D9",
    "ratified":True,
    "authority":"#4008",
    "normative_map":"knowledge/d9-ratified.json",
    "occupancy":512,
    "selector_law_crossing_only":True,
}

target=state["target"]
selected=target["selected_semantic_candidates"]
assert selected>=256
assert target["domain"]=="D10"
assert target["width"]==10
assert target["capacity"]==1024
assert target["dense_target"]==1024
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==selected-256
assert target["remaining_semantic_candidates"]==1024-selected
assert target["ratified_residents"]==0

assert inventory["accounting"]=={
    "selected_semantic_candidates":selected,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":selected-256,
    "remaining_semantic_inventory":1024-selected,
    "ratified_d10_residents":0,
}
inv_by_id={row["stable_id"]:row for row in inventory["rows"]}
assert len(inventory["rows"])==selected
for row in seed["rows"]:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["coordinate"]==row["coordinate"]
    assert got["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR"

assert state["foundation"]=={
    "current_contract":"11.8",
    "current_authority":"#4008",
    "current_domains":["D1","D2","D3","D4","D5","D6","D7","D8","D9"],
    "parent_domain":"D9",
    "d9_occupancy":512,
    "d9_ratified":True,
    "d9_ratified_map":"knowledge/d9-ratified.json",
    "research_domain":"D10",
}
assert state["authority_boundary"]=={
    "d9_coordinates":"NORMATIVE D9 parent identities under #4008",
    "d9_to_d10_children":"NO AUTOMATIC SEMANTICS FROM WIDTH OR SUFFIX",
    "d9_selector_law":"MAY CROSS because independently proved",
    "legacy_sens8_sid8_function8":"NO D10 PLACEMENT AUTHORITY",
}

assert foundation["authority"]=="#4008"
assert "(minor . 8)" in lang
assert "Contract 11.8" in lang

print("D10-FILL-V1-SEED: PASS")
print(f"selector-seed=256 preserved; inventory={selected}/1024 remaining={1024-selected} ratified-D10=0")
