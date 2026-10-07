#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-crossrepo-my-idea-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-crossrepo-my-idea-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4182 / juv4uk/my-idea#80"
assert harvest["accounting"]=={
    "selected_d10_candidates":13,
    "d10_before":527,
    "d10_after":540,
    "law_forced_coordinates":256,
    "unplaced_after":284,
    "remaining_after":484,
    "ratified_d10_residents":0,
}
rows=harvest["rows"]
assert len(rows)==13
assert len({r["stable_id"] for r in rows})==13
assert len({r["semantic_name"] for r in rows})==13
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in rows)
assert all(r["coordinate"] is None for r in rows)
assert all(r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["donor_coordinate_authority"]=="NONE" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)
assert all(r["donor_repo"]=="juv4uk/my-idea" for r in rows)
assert all(len(r["source_sha"])==40 for r in rows)

expected={
"EDITOR-REGISTER-COMMAND","EDITOR-SELECTION","EDITOR-BUFFER-TEXT",
"EDITOR-REPLACE-SELECTION","EDITOR-MESSAGE","EDITOR-REGISTER-KEYMAP",
"EDITOR-REGISTER-HANDLER","EDITOR-INVOKE-COMMAND","EDITOR-DISPATCH-KEY",
"EDITOR-EMIT-EVENT","SELF-BUILD-PLAN","EVIDENCE-LATEST-MATRIX",
"REPO-CAPABILITY-EDGES"
}
assert {r["semantic_name"] for r in rows}==expected

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (expected & lower)

# Host/mechanism-only functions are deliberately not selected.
for forbidden in (
    "LOAD-PLUGINS-DETERMINISTIC","SCAN-EVIDENCE-RECORDS",
    "SCAN-REPO-CONTRACTS","CANONICAL-SELF-BUILD-PLAN",
    "PROCESS-RUN","TAURI-INVOKE"
):
    assert forbidden not in expected

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="CROSSREPO-MY-IDEA-SEMANTIC-HARVEST"
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

assert inventory["accounting"]=={
    "selected_semantic_candidates":540,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":284,
    "remaining_semantic_inventory":484,
    "ratified_d10_residents":0,
}
assert state["target"]["selected_semantic_candidates"]==540
assert state["target"]["unplaced_selected_candidates"]==284
assert state["target"]["remaining_semantic_candidates"]==484
assert state["target"]["ratified_residents"]==0
assert state["crossrepo_my_idea_v1"]=={
    "authority":"#4182 / juv4uk/my-idea#80",
    "artifact":"knowledge/d10-crossrepo-my-idea-v1.json",
    "selected":13,
    "coordinates_assigned":0,
    "ratification_effect":"NONE",
}

print("D10-CROSSREPO-MY-IDEA-V1=PASS")
print("selected=13 inventory=540/1024 placed=256 unplaced=284 remaining=484 ratified=0")
