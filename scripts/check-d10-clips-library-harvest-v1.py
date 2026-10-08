#!/usr/bin/env python3
"""Перевірка джерела та унікальності дослідницьких CLIPS-значень D10."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
read=lambda name: json.loads((root/name).read_text(encoding="utf-8"))
h=read("knowledge/d10-clips-library-harvest-v1.json")
inv=read("knowledge/d10-v1-semantic-inventory.json")
st=read("knowledge/d10-fill-v1-state.json")
foundation=read("knowledge/d1-d9-foundation.json")
lines=(root/"lib/clips-import.lisp").read_text(encoding="utf-8").splitlines()
assert h["schema"]=="d10-clips-library-harvest-v1/v1"
assert h["status"]=="RESEARCH-UNRATIFIED"
assert len(h["rows"])==12
lower={str(v).upper() for d in foundation["domains"].values() for v in d.get("residents",{}).values()}
own={r["semantic_name"] for r in h["rows"]}
other={r["semantic_name"] for r in inv["rows"] if r.get("source_class")!="CLIPS-LIBRARY-SEMANTIC-HARVEST"}
assert len(own)==12 and not (own&(other|lower))
byid={r["stable_id"]:r for r in inv["rows"]}
for r in h["rows"]:
    assert byid[r["stable_id"]]["semantic_name"]==r["semantic_name"]
    assert r["source_sha"]==h["donor"]["source_sha"]
    assert r["proposal_status"]=="pending-owner-review"
    assert r["surface_uk"] and r["surface_ukr"]
    assert r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED"
    assert r["ratified_resident"] is False
    prefix="(00001001 "+r["source_name"]
    assert lines[r["source_line"]-1]==prefix or lines[r["source_line"]-1].startswith(prefix+" ")
selected=st["target"]["selected_semantic_candidates"]
assert len(inv["rows"])==selected
assert len({r["stable_id"] for r in inv["rows"]})==selected
assert len({r["semantic_name"] for r in inv["rows"]})==selected
assert selected>=h["accounting"]["after"]  # historical minimum, not ceiling
assert inv["accounting"]=={
    "selected_semantic_candidates":selected,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":selected-256,
    "remaining_semantic_inventory":1024-selected,
    "ratified_d10_residents":0
}
assert st["target"]["law_forced_coordinates"]==256
assert st["target"]["unplaced_selected_candidates"]==selected-256
assert st["target"]["remaining_semantic_candidates"]==1024-selected
assert st["target"]["ratified_residents"]==0
print(f"D10-CLIPS-LIBRARY-HARVEST: PASS ({len(h['rows'])} added; {selected}/1024; ratified 0)")
