#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
h=json.loads((root/"knowledge/d10-crossrepo-golisp-pascal-v1.json").read_text(encoding="utf-8"))
inv=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))

assert h["schema"]=="d10-crossrepo-golisp-pascal-v1/v1"
assert h["status"]=="RESEARCH-UNRATIFIED"
assert h["authority"]=="#4077"
assert h["accounting"]=={
    "donors_reviewed":2,
    "selected_d10_candidates":22,
    "d10_selected_before":398,
    "d10_selected_after":420,
    "d10_remaining_after":604,
    "ratified_d10_residents":0,
}
assert {d["repository"] for d in h["donors"]}=={"juv4uk/golisp","juv4uk/pascal-lisp"}
assert all(d["review_status"]=="EXHAUSTED-FOR-PORTABLE-CORE-SLICE" for d in h["donors"])

rows=h["rows"]
assert len(rows)==22
assert len({r["stable_id"] for r in rows})==22
assert len({r["semantic_name"] for r in rows})==22
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in rows)
assert all(r["ownership"]=="CORE-CANDIDATE" for r in rows)
assert all(r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["implementation_identity_authority"]=="NONE" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)

by={r["semantic_name"]:r for r in rows}
assert by["MODULO"]["source_name"]=="modulo"
assert by["MODULO"]["relation_class"]=="ARITHMETIC-SIGN-ALGEBRA"
assert by["CALL-WITH-VALUES"]["donor_repo"]=="juv4uk/pascal-lisp"
assert by["NULL-ENVIRONMENT"]["relation_class"]=="ENVIRONMENT-VALUE-ALGEBRA"
assert by["CAPTURE-ENVIRONMENT"]["relation_class"]=="ENVIRONMENT-VALUE-ALGEBRA"
for name in ("MAKE-CHANNEL","CHANNEL-SEND","CHANNEL-RECEIVE"):
    assert by[name]["relation_class"]=="CHANNEL-COMMUNICATION-ALGEBRA"
for name in ("READ-CHAR","READ-BYTE","EOF-OBJECT?","WRITE-STRING","WRITE-BYTE","FLUSH"):
    assert by[name]["relation_class"]=="PORT-IO-ALGEBRA"

# Implementation identities are mechanism-only and must never appear as semantic fields.
for row in rows:
    forbidden=("fd","file_descriptor","goroutine","pointer","address","os_process")
    assert not any(key in row for key in forbidden)

inv_by_id={r["stable_id"]:r for r in inv["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="CROSSREPO-GOLISP-PASCAL-HARVEST"
    assert got["coordinate"] is None
    assert got["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=420
assert target["remaining_semantic_candidates"]==1024-target["selected_semantic_candidates"]
assert target["law_forced_coordinates"]==256
assert target["ratified_residents"]==0

print("D10-CROSSREPO-GOLISP-PASCAL-1=PASS")
print(f"selected=22 global={target['selected_semantic_candidates']}/1024 remaining={target['remaining_semantic_candidates']} ratified=0")
