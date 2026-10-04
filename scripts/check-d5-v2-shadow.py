#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
shadow=json.loads((root/"knowledge/d5-v2-shadow.json").read_text(encoding="utf-8"))
current=json.loads((root/"knowledge/d5-historical-full-map.json").read_text(encoding="utf-8"))
atlas=json.loads((root/"knowledge/d5-internal-law-atlas.json").read_text(encoding="utf-8"))
d4=json.loads((root/"knowledge/d4-cleanroom.json").read_text(encoding="utf-8"))

rows=shadow["coordinates"]
assert shadow["status"]=="research-shadow-not-authority"
assert len(rows)==32
assert len({r["coordinate"] for r in rows})==32
assert {r["coordinate"] for r in rows}=={f"{i:05b}" for i in range(32)}
assert {r["name"] for r in rows}=={r["name"] for r in current["coordinates"]}
assert sum(r["old_coordinate"]!=r["coordinate"] for r in rows)==16
assert sum(r["old_coordinate"]==r["coordinate"] for r in rows)==16

# Preserve every old sibling block as an unordered semantic pair.
old_pairs={
    frozenset((p["child0"]["label"],p["child1"]["label"]))
    for p in atlas["pairs"]
}
new_by_prefix={}
for r in rows:
    new_by_prefix.setdefault(r["coordinate"][:4],[]).append(r["name"])
new_pairs={frozenset(v) for v in new_by_prefix.values()}
assert old_pairs==new_pairs
assert len(new_pairs)==16

# Preserve relation-class counts.
old_counts={}
for p in atlas["pairs"]:
    old_counts[p["relation_class"]]=old_counts.get(p["relation_class"],0)+1
new_counts={}
for rs in new_by_prefix.values():
    row=next(r for r in rows if r["name"]==rs[0])
    new_counts[row["relation_class"]]=new_counts.get(row["relation_class"],0)+1
assert old_counts==new_counts=={
    "SEMANTIC-GENERATOR":4,
    "LOCAL-ALGEBRA":6,
    "MULTI-DELTA-FAMILY":2,
    "COORDINATE-HISTORICAL":4,
}

expected_selectors={
    "01100":"CDAAR","01101":"CDADR",
    "01110":"CDDAR","01111":"CDDDR",
    "10000":"CAAAR","10001":"CAADR",
    "10010":"CADAR","10011":"CADDR",
}
by={r["coordinate"]:r["name"] for r in rows}
for bits,name in expected_selectors.items():
    assert by[bits]==name,(bits,by[bits],name)

# Lower-domain duplicate is explicit, never silently ignored.
d4_append=next(k for k,v in d4["residents"].items() if v=="APPEND")
d5_append=next(r["coordinate"] for r in rows if r["name"]=="APPEND")
dup=shadow["lower_domain_duplicate_audit"][0]
assert dup=={
    "name":"APPEND",
    "d4_coordinate":d4_append,
    "d5_shadow_coordinate":d5_append,
    "status":"REQUIRES-SEMANTIC-DEDUP-DECISION",
}

print("D5-V2-SHADOW: PASS")
print("occupancy=32/32 moved=16 unchanged=16 selectors=8/8 pairs=16/16")
print(f"duplicate=APPEND D4:{d4_append} D5:{d5_append}")
