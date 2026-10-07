#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
harvest=json.loads((root/"knowledge/d10-library-harvest-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
ledger1=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))
ledger2=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))

assert harvest["schema"]=="d10-library-harvest-v1/v1"
assert harvest["status"]=="RESEARCH-UNRATIFIED"
assert harvest["authority"]=="#4026"
assert harvest["accounting"]["selected_d10_candidates"]==39
rows=harvest["rows"]
assert len(rows)==39 and len({r["stable_id"] for r in rows})==39
assert all(r["coordinate"] is None for r in rows)

inv_by_id={r["stable_id"]:r for r in inventory["rows"]}
historical1={r["stable_id"]:r for r in ledger1["rows"]}
historical2={r["stable_id"]:r for r in ledger2["rows"]}

# #4162 restores every language-visible row previously removed only for
# package/domain ownership.  Historical ledgers remain immutable provenance.
for row in rows:
    got=inv_by_id[row["stable_id"]]
    assert got["semantic_name"]==row["semantic_name"]
    assert got["coordinate"] is None
    assert got["coordinate_basis"]=="UNPLACED"
    assert got["ratified_resident"] is False

assert sum(r["stable_id"] in historical1 for r in rows)==6
assert sum(r["stable_id"] in historical2 for r in rows)==15
assert len(rows)==39

target=state["target"]
selected_total=target["selected_semantic_candidates"]
remaining_total=target["remaining_semantic_candidates"]
assert selected_total>=504
assert remaining_total==1024-selected_total
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==selected_total-256
assert target["ratified_residents"]==0
assert len(inventory["rows"])==selected_total
assert len({r["stable_id"] for r in inventory["rows"]})==selected_total
assert len({r["semantic_name"] for r in inventory["rows"]})==selected_total

print("D10-LIBRARY-HARVEST-V1=PASS")
print("harvest=39 selected=39 historical-cleanup-v1=6 historical-cleanup-v2=15")
print(f"inventory={selected_total}/1024 remaining={remaining_total} ratified=0")
