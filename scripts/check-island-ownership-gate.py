#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
audit=json.loads((root/"knowledge/island-ownership-gate-v1.json").read_text(encoding="utf-8"))
d9inv=json.loads((root/"knowledge/d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))
d9rat=json.loads((root/"knowledge/d9-ratified.json").read_text(encoding="utf-8"))
d10inv=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
d10state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))

assert audit["schema"]=="island-ownership-gate/v1"
assert audit["status"]=="P0-RECONCILIATION"
assert audit["authority"]=="#4033"

assert audit["d9"]["ratified"] is True
assert audit["d9"]["authority"]=="#4008 / Contract 11.8"
assert audit["d9"]["occupancy"]==512
assert audit["d9"]["definite_noncore_count"]==136
assert audit["d9"]["review_required_count"]==70
assert d9rat["status"]=="owner-ratified"
assert d9rat["authority"]=="#4008"
assert d9rat["occupancy"]==512

ratified_names=set(d9rat["residents"].values())
for row in audit["d9"]["definite_noncore_rows"] + audit["d9"]["review_required_rows"]:
    assert row["semantic_name"] in ratified_names
    assert len(row["coordinate"])==9 and set(row["coordinate"])<=set("01")
    assert row["action"]=="OWNER-AMENDMENT-REQUIRED-BEFORE-SEMANTIC-CHANGE"

assert audit["d10"]["ratified"] is False
assert audit["d10"]["definite_noncore_count"]==55
assert audit["d10"]["review_required_count"]==15

current_by_id={row["stable_id"]:row for row in d10inv["rows"]}
frozen_definite=set(audit["d10"]["frozen_definite_stable_ids"])
frozen_review=set(audit["d10"]["frozen_review_stable_ids"])

current_definite={
    row["stable_id"]
    for row in audit["d10"]["definite_noncore_rows"]
    if row["stable_id"] in current_by_id
}
current_review={
    row["stable_id"]
    for row in audit["d10"]["review_required_rows"]
    if row["stable_id"] in current_by_id
}

# Gate is monotone: rows may be removed/reclassified later, but no new
# definite/review ownership debt may appear without explicitly updating #4033.
assert current_definite <= frozen_definite
assert current_review <= frozen_review

gate=d10state["ownership_gate"]
assert gate["authority"]=="#4033"
assert gate["artifact"]=="knowledge/island-ownership-gate-v1.json"
assert gate["status"]=="RATIFICATION-BLOCKER-REVIEW-ONLY"
assert gate["definite_noncore_selected"]==0
assert gate["definite_noncore_reclassified"]==55
assert gate["review_required_selected"]==15
assert gate["no_new_definite_noncore"] is True

# D10 is still research. Definite ownership debt has been cleared; the
# remaining REVIEW-REQUIRED rows keep ratification blocked until ownership
# witnesses are resolved.
assert d10state["target"]["ratified_residents"]==0
assert len(current_definite)==0
assert len(current_review)==15

print("ISLAND-OWNERSHIP-GATE=PASS")
print("D9: ratified audit only; definite=136 review=70 owner-amendment-required")
print("D10: definite-selected=0 reclassified=55 review=15 ratification-blocked")
