#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
review=json.loads((root/"knowledge/d10-crossrepo-paip-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert review["schema"]=="d10-crossrepo-paip-v1/v1"
assert review["status"]=="RESEARCH-UNRATIFIED"
assert review["authority"]=="#4089"
assert review["donor"]=={
    "repository":"juv4uk/paip-lisp",
    "pinned_commit":"2db2ba99465cadef904e574b20b6981b32ad81df",
    "primary_source":"lisp/auxfns.lisp",
    "role":"CORE-HISTORICAL-DONOR",
}
assert review["accounting"]=={
    "selected_d10_candidates":23,
    "d10_before":420,
    "d10_after":443,
    "placed_after":256,
    "unplaced_after":187,
    "remaining_after":581,
    "ratified_d10_residents":0,
}

rows=review["rows"]
assert len(rows)==23
assert len({r["stable_id"] for r in rows})==23
assert len({r["semantic_name"] for r in rows})==23
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in rows)
assert all(r["selected_d10_candidate"] is True for r in rows)
assert all(r["coordinate"] is None and r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)

expected={
"ONCE-ONLY","FIND-ALL","PARTITION-IF","LAST1","MAPPEND","MKLIST","FLATTEN",
"MEMO","MEMOIZE","CLEAR-MEMOIZE","DELAY","FORCE",
"MAKE-QUEUE","ENQUEUE","DEQUEUE","FRONT","EMPTY-QUEUE?","QUEUE-NCONC",
"SORT*","FIND-IF-ANYWHERE","UNIQUE-FIND-IF-ANYWHERE","MAP-INTO","NEW-SYMBOL"
}
assert {r["semantic_name"] for r in rows}==expected

# Checked-in donor evidence is not copied into sens; provenance is pinned instead.
# Guard the claimed source spellings against the reviewed function/macro names.
claimed={r["source_name"] for r in rows}
expected_source={name.lower() for name in expected}
assert claimed==expected_source

exhausted={r["repository"]:r for r in review["exhausted_donors"]}
assert exhausted["juv4uk/Clojure-code"]["pinned_commit"]=="40049756e76417fbc5b6dcc42f47cc69bfb01313"
assert exhausted["juv4uk/clojure-cookbook"]["pinned_commit"]=="1b3754a7f4aab51cc9b254ea102870e7ce478aa0"
assert all(r["decision"]=="REVIEWED-EXHAUSTED-FOR-CORE" for r in exhausted.values())

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (lower & expected)

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="CROSSREPO-PAIP-HISTORICAL-HARVEST"
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

target=state["target"]
selected_total=target["selected_semantic_candidates"]
remaining_total=target["remaining_semantic_candidates"]
assert selected_total>=428
assert remaining_total==1024-selected_total
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==selected_total-256
assert target["ratified_residents"]==0
assert len(inventory["rows"])==selected_total
assert len({r["stable_id"] for r in inventory["rows"]})==selected_total
assert len({r["semantic_name"] for r in inventory["rows"]})==selected_total

assert state["crossrepo_paip_v1"]=={
    "artifact":"knowledge/d10-crossrepo-paip-v1.json",
    "selected":23,
    "clojure_code":"REVIEWED-EXHAUSTED-FOR-CORE",
    "clojure_cookbook":"REVIEWED-EXHAUSTED-FOR-CORE",
    "coordinates_assigned":0,
}

print("D10-CROSSREPO-PAIP-V1=PASS")
print(f"selected=23 inventory={selected_total}/1024 placed=256 unplaced={selected_total-256} remaining={remaining_total} ratified=0")
