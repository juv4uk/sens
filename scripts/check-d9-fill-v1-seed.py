#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
d8=json.loads((root/"knowledge/d8-ratified.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))
seed=json.loads((root/"knowledge/d9-selector-seed.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")

def fnv1a64(text: str) -> str:
    h=0xcbf29ce484222325
    for b in text.encode("ascii"):
        h ^= b
        h=(h*0x100000001b3) & 0xffffffffffffffff
    return f"{h:016x}"

def child_name(parent: str, bit: str) -> str:
    assert parent.endswith("R")
    return parent[:-1] + ("A" if bit=="0" else "D") + "R"

assert seed["schema"]=="d9-selector-seed/v1"
assert seed["status"]=="RESEARCH-UNRATIFIED"
assert seed["authority"]=="#3964"
assert seed["domain"]=="D9" and seed["width"]==9
assert seed["target_capacity"]==512
assert seed["accounting"]=={
    "d8_selector_parents":64,
    "generated_d9_selector_candidates":128,
    "target_d9_capacity":512,
    "remaining_semantic_inventory":384,
    "ratified_d9_residents":0,
}

parents=sorted(
    (row for row in d8["rows"] if row["coordinate_basis"]=="proved-selector-generator"),
    key=lambda row: row["coordinate"],
)
assert len(parents)==64

expected=[]
for parent in parents:
    for bit in ("0","1"):
        name=child_name(parent["resident"],bit)
        coord=parent["coordinate"]+bit
        expected.append((coord,name,parent["coordinate"],parent["resident"],bit,fnv1a64("selector:"+name)))

rows=sorted(seed["rows"],key=lambda row: row["coordinate"])
assert len(rows)==128
assert len({row["coordinate"] for row in rows})==128
assert len({row["semantic_name"] for row in rows})==128
assert all(len(row["coordinate"])==9 and set(row["coordinate"])<=set("01") for row in rows)

for row,(coord,name,pcoord,pname,bit,h) in zip(rows,expected):
    assert row["coordinate"]==coord
    assert row["semantic_name"]==name
    assert row["parent_coordinate"]==pcoord
    assert row["parent_semantic_name"]==pname
    assert row["generator_suffix_bit"]==bit
    assert row["stable_id"]==f"d9.sel.{h}"
    assert row["coordinate_basis"]=="PROVED-SELECTOR-GENERATOR"
    assert row["relation_class"]=="SEMANTIC-GENERATOR"
    assert row["ratified_resident"] is False

lower_names=set()
for domain in foundation["domains"].values():
    lower_names.update(domain.get("residents",{}).values())
assert not (lower_names & {row["semantic_name"] for row in rows})

assert state["schema"]=="d9-fill-v1-state/v1"
assert state["status"]=="RESEARCH-UNRATIFIED"
assert state["authority"]=="#3964"
assert state["foundation"]["authority"]=="#3960"
assert state["foundation"]["current_domains"]==["D1","D2","D3","D4","D5","D6","D7","D8"]
assert state["foundation"]["research_domain"]=="D9"
target=state["target"]
assert target["domain"]=="D9"
assert target["width"]==9
assert target["capacity"]==512
assert target["dense_target"]==512
assert target["selected_semantic_candidates"]>=128
assert target["remaining_semantic_candidates"]==512-target["selected_semantic_candidates"]
assert target["ratified_residents"]==0
assert state["recovery_queue"]["automatic_admission"] is False

# This checker preserves the original D9 selector-seed audit as a historical artifact.
# The seed was created under Contract 11.7; the live language contract has since
# advanced to 11.8 and owner-ratifies D1–D9. Requiring the old version in the
# live source incorrectly makes a provenance check fail after a valid contract update.
assert state["foundation"]["contract"]=="11.7"
assert "(major . #d11) (minor . 8)" in lang
assert "Contract 11.8" in lang
assert "owner-ratifies D1–D9" in lang

print("D9-FILL-V1-SEED: PASS")
print("selectors=128/512 remaining=384 ratified-D9=0")
