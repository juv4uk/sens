#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
h=json.loads((root/"knowledge/d10-crossrepo-lisp-koans-v1.json").read_text(encoding="utf-8"))
inv=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert h["schema"]=="d10-crossrepo-lisp-koans-v1/v1"
assert h["status"]=="RESEARCH-UNRATIFIED"
assert h["authority"]=="#4074"
assert h["donor"]=={
    "repository":"juv4uk/lisp-koans",
    "head":"57b901f8d4b16d66696896a745110b7561120da3",
    "role":"CORE-HISTORICAL-DONOR",
    "review_status":"EXHAUSTED-FOR-SELECTED-LANGUAGE-SLICE",
}
assert h["accounting"]=={
    "donor_attested_reviewed":36,
    "selected_d10_candidates":25,
    "rejected_exact_d1_d9_duplicates":11,
    "d10_selected_before":373,
    "d10_selected_after":398,
    "d10_remaining_after":626,
    "ratified_d10_residents":0,
}

rows=h["rows"]
assert len(rows)==25
assert len({r["stable_id"] for r in rows})==25
assert len({r["semantic_name"] for r in rows})==25
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in rows)
assert all(r["ownership"]=="CORE-CANDIDATE" for r in rows)
assert all(r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)
assert all(r["donor_repo"]=="juv4uk/lisp-koans" for r in rows)
assert all(r["source_file"].startswith("koans-solved/") for r in rows)

lower={}
for domain,body in foundation["domains"].items():
    for coordinate,name in body.get("residents",{}).items():
        lower.setdefault(str(name).upper(),[]).append(f"{domain}:{coordinate} {name}")

expected_dups={
    "VALUES":"D8:00110100 VALUES",
    "MULTIPLE-VALUE-BIND":"D8:00100101 MULTIPLE-VALUE-BIND",
    "MAKE-CONDITION":"D8:00100000 MAKE-CONDITION",
    "HANDLER-BIND":"D8:11010111 HANDLER-BIND",
    "SIGNAL":"D8:11000010 SIGNAL",
    "HANDLER-CASE":"D8:11100101 HANDLER-CASE",
    "SUBSEQ":"D8:00100001 SUBSEQ",
    "CHAR":"D8:01011011 CHAR",
    "POSITION":"D8:00000110 POSITION",
    "FLET":"D8:01011110 FLET",
    "LABELS":"D8:10110000 LABELS",
}
dup_rows={r["semantic_name"]:r["current_target"] for r in h["exact_duplicate_review"]}
assert dup_rows==expected_dups
for name,target in expected_dups.items():
    assert target in lower[name]
    assert name not in {r["semantic_name"] for r in rows}

inv_by_id={r["stable_id"]:r for r in inv["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="CROSSREPO-LISP-KOANS-HISTORICAL-HARVEST"
    assert got["coordinate"] is None
    assert got["ownership"]=="CORE-CANDIDATE"
    assert got["ratified_resident"] is False

target=state["target"]
assert target["selected_semantic_candidates"]>=398
assert target["remaining_semantic_candidates"]==1024-target["selected_semantic_candidates"]
assert target["law_forced_coordinates"]==256
assert target["ratified_residents"]==0

print("D10-CROSSREPO-LISP-KOANS-1=PASS")
print(f"selected=25 exact-lower-duplicates=11 global={target['selected_semantic_candidates']}/1024 remaining={target['remaining_semantic_candidates']}")
