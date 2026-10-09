#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-crossrepo-panini-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-crossrepo-panini-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["accounting"]=={
    "selected_d10_candidates":23,
    "d10_before":504,
    "d10_after":527,
    "law_forced_coordinates":256,
    "unplaced_after":271,
    "remaining_after":497,
    "ratified_d10_residents":0,
}
assert harvest["donor"]=={"repository":"juv4uk/my-lisp-panini","branch":"master"}

rows=harvest["rows"]
assert len(rows)==23
assert len({r["stable_id"] for r in rows})==23
assert len({r["semantic_name"] for r in rows})==23
assert all(r["decision"]=="SELECT-D10-CANDIDATE" for r in rows)
assert all(r["coordinate"] is None for r in rows)
assert all(r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["donor_coordinate_authority"]=="NONE" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)
assert all(r["donor_repo"]=="juv4uk/my-lisp-panini" for r in rows)
assert all(len(r["source_sha"])==40 for r in rows)

expected={
"RESOLVE-PRATYAHARA","PRATYAHARA-MEMBER?",
"APPLY-GUNA","APPLY-ECO-SANDHI",
"SANDHI-IKO-YAN-ACI","SANDHI-MANUSVARA","STOP-DEVOICE",
"SANDHI-KHARI-SAVARNE","STOP-VOICE","SANDHI-JHALAM-JHASHI",
"APPLY-SANDHI","JOIN-WORDS-SANDHI",
"DERIVE-VERB-LAKARA","DERIVE-VERB-OPTATIVE",
"DERIVE-VERB-ATMANEPADA","DERIVE-VERB-FUTURE",
"PARADIGM-PARASMAIPADA","PARADIGM-ATMANEPADA","PARADIGM-FULL",
"ANUVRTTI-GRAPH-VALID?","IT-DELETABLE?","SAP-ELIGIBLE?",
"AMBIGUOUS-APAVADA?"
}
assert {r["semantic_name"] for r in rows}==expected

# Do not duplicate any ratified D1-D9 resident by semantic name.
lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).upper() for name in domain.get("residents",{}).values())
assert not (expected & lower)

# Curated tranche deliberately excludes data/examples/trace projections.
for forbidden in (
    "TRACE-FINAL","TRACE-STEP-AT","TRACE-COUNT",
    "DERIVE-BHAVATI","DERIVE-PACATI",
    "AC","HAL","IK","YAN"
):
    assert forbidden not in expected

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="CROSSREPO-PANINI-EXECUTABLE-HARVEST"
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

# 527 is the historical Panini checkpoint, not the D10 inventory ceiling.
selected_now=state["target"]["selected_semantic_candidates"]
assert selected_now>=527
assert inventory["accounting"]=={
    "selected_semantic_candidates":selected_now,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":selected_now-256,
    "remaining_semantic_inventory":1024-selected_now,
    "ratified_d10_residents":0,
}
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==selected_now-256
assert state["target"]["remaining_semantic_candidates"]==1024-selected_now
assert state["target"]["ratified_residents"]==0
assert state["crossrepo_panini_v1"]=={
    "authority":"#4182 / juv4uk/my-lisp-panini#52",
    "artifact":"knowledge/d10-crossrepo-panini-v1.json",
    "selected":23,
    "coordinates_assigned":0,
    "ratification_effect":"NONE",
}

print("D10-CROSSREPO-PANINI-V1=PASS")
print(f"selected=23 inventory={selected_now}/1024 placed=256 unplaced={selected_now-256} remaining={1024-selected_now} ratified=0")
