#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-knowledge-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-knowledge-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4030"
assert harvest["accounting"]=={
    "selected_d10_candidates":37,
    "epistemic_record_algebra":12,
    "knowledge_admission_protocol":23,
    "result_shape_validation":2,
    "d10_selected_before_harvest":330,
    "d10_selected_after_harvest":367,
    "d10_remaining_after_harvest":657,
    "law_forced_coordinates":256,
    "unplaced_selected_after_harvest":111,
    "ratified_d10_residents":0,
}

rows=harvest["rows"]
assert len(rows)==37
assert len({r["stable_id"] for r in rows})==37
assert len({r["semantic_name"] for r in rows})==37
assert all(r["coordinate"] is None for r in rows)
assert all(r["coordinate_basis"]=="UNPLACED" for r in rows)
assert all(r["legacy_coordinate_authority"]=="NONE" for r in rows)
assert all(r["ratified_resident"] is False for r in rows)

expected_sources={
    "lib/epistemic.lisp":12,
    "lib/knowledge.lisp":23,
    "lib/result-status.lisp":2,
}
actual={}
for r in rows:
    actual[r["source_file"]]=actual.get(r["source_file"],0)+1
assert actual==expected_sources

for source_file,count in expected_sources.items():
    text=(root/source_file).read_text(encoding="utf-8")
    defs={m.group(1) for m in re.finditer(r'^\([01]{8}\s+([^\s()]+)\s+',text,re.MULTILINE)}
    claimed={r["source_name"] for r in rows if r["source_file"]==source_file}
    assert len(claimed)==count
    assert claimed <= defs

# Explicitly exclude internal/global/transport rows from this tranche.
claimed={r["source_name"] for r in rows}
for name in (
    "epistemic--claim-ref?","epistemic--all-required-present?",
    "*knowledge-journal*","*knowledge-package-version*","*usage-counts*",
    "tcp-read-to-eof","tcp-read-frame","send-knowledge-package",
    "exchange-knowledge-package","receive-knowledge-package",
    "record-usage!","usage-of",
):
    assert name not in claimed

lower=set()
for domain in foundation["domains"].values():
    lower.update(str(name).lower() for name in domain.get("residents",{}).values())
assert not (lower & {r["source_name"].lower() for r in rows})

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["source_class"]=="EPISTEMIC-KNOWLEDGE-HARVEST"
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

assert len(inventory["rows"])==367
assert len({r["stable_id"] for r in inventory["rows"]})==367
assert len({r["semantic_name"] for r in inventory["rows"]})==367
assert inventory["accounting"]=={
    "selected_semantic_candidates":367,
    "law_forced_coordinates":256,
    "unplaced_selected_candidates":111,
    "remaining_semantic_inventory":657,
    "ratified_d10_residents":0,
}

assert state["target"]["selected_semantic_candidates"]==367
assert state["target"]["remaining_semantic_candidates"]==657
assert state["target"]["law_forced_coordinates"]==256
assert state["target"]["unplaced_selected_candidates"]==111
assert state["target"]["ratified_residents"]==0

print("D10-KNOWLEDGE-HARVEST-V1=PASS")
print("selected=37 inventory=367/1024 placed=256 unplaced=111 remaining=657 ratified=0")
