#!/usr/bin/env python3
"""Provenance/identity gate for unification and lexical scope D10 proposals."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((root/p).read_text(encoding="utf-8"))
h=read("knowledge/d10-unify-lexical-harvest-v1.json")
inv=read("knowledge/d10-v1-semantic-inventory.json")
st=read("knowledge/d10-fill-v1-state.json")
f=read("knowledge/d1-d9-foundation.json")
assert h["schema"]=="d10-unify-lexical-harvest-v1/v1"
assert h["status"]=="RESEARCH-UNRATIFIED"
rows=h["rows"]
assert len(rows)==h["accounting"]["selected"]==9
assert len({r["stable_id"] for r in rows})==9
assert len({r["semantic_name"] for r in rows})==9
lower={str(v).upper() for d in f["domains"].values() for v in d.get("residents",{}).values()}
ours={r["semantic_name"].upper() for r in rows}
others={r["semantic_name"].upper() for r in inv["rows"] if r.get("source_class")!="UNIFY-LEXICAL-SEMANTIC-HARVEST"}
assert not(ours&lower) and not(ours&others)
byid={r["stable_id"]:r for r in inv["rows"]}
assert len(byid)==len(inv["rows"])
assert len({r["semantic_name"] for r in inv["rows"]})==len(inv["rows"])
sources={}
for d in h["donors"]:
    raw=(root/d["path"]).read_bytes()
    sha=hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+bytes([0])+raw).hexdigest()
    assert sha==d["source_sha"],(d["path"],sha)
    sources[d["path"]]=(d,raw.decode("utf-8").splitlines())
assert set(sources)=={"lib/unify.lisp","lib/linter.lisp"}
for r in rows:
    assert byid[r["stable_id"]]["semantic_name"]==r["semantic_name"]
    assert byid[r["stable_id"]]["source_class"]=="UNIFY-LEXICAL-SEMANTIC-HARVEST"
    d,lines=sources[r["source_file"]]
    assert r["source_sha"]==d["source_sha"]
    assert r["definition_form"]==d["definition_form"]
    prefix="("+r["definition_form"]+" "+r["source_name"]
    actual=lines[r["source_line"]-1]
    assert actual.startswith(prefix),(r["source_file"],r["source_line"])
    assert actual[len(prefix):][:1] in (""," ",chr(9),")")
    assert r["proposal_status"]=="pending-owner-review"
    assert r["surface_uk"] and r["surface_ukr"] and r["behavior"]
    assert r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED"
    assert r["ratified_resident"] is False
n=st["target"]["selected_semantic_candidates"]
assert len(inv["rows"])==n and n>=h["accounting"]["after"]
assert inv["accounting"]=={"selected_semantic_candidates":n,"law_forced_coordinates":256,"unplaced_selected_candidates":n-256,"remaining_semantic_inventory":1024-n,"ratified_d10_residents":0}
assert st["target"]["law_forced_coordinates"]==256
assert st["target"]["unplaced_selected_candidates"]==n-256
assert st["target"]["remaining_semantic_candidates"]==1024-n
assert st["target"]["ratified_residents"]==0
assert "knowledge/d10-unify-lexical-harvest-v1.json" in inv["sources"]
print(f"D10-UNIFY-LEXICAL: PASS ({len(rows)} new, {n}/1024, ratified 0)")
