#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
audit=json.loads((root/"knowledge/island-ownership-gate-v1.json").read_text(encoding="utf-8"))
d9rat=json.loads((root/"knowledge/d9-ratified.json").read_text(encoding="utf-8"))
d10inv=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
d10state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
rest=json.loads((root/"knowledge/d10-single-stream-restoration-v1.json").read_text(encoding="utf-8"))

assert audit["schema"]=="island-ownership-gate/v1"
assert audit["status"]=="P0-RECONCILIATION"
assert audit["authority"]=="#4033"

assert audit["d9"]["ratified"] is True
assert audit["d9"]["authority"]=="#4008 / Contract 11.8"
assert audit["d9"]["occupancy"]==512
assert d9rat["status"]=="owner-ratified"
assert d9rat["authority"]=="#4008"
assert d9rat["occupancy"]==512

# #4033 remains immutable provenance about the old ownership split.
assert audit["d10"]["ratified"] is False
assert audit["d10"]["definite_noncore_count"]==55
assert audit["d10"]["review_required_count"]==15

current_by_id={row["stable_id"]:row for row in d10inv["rows"]}
frozen_definite=set(audit["d10"]["frozen_definite_stable_ids"])
frozen_review=set(audit["d10"]["frozen_review_stable_ids"])
restored={row["stable_id"] for row in rest["rows"]}

# Owner correction #4162 reverses ownership-only exclusion.  The exact 70
# historical debt rows are now selected again as UNPLACED meanings.
assert len(frozen_definite)==55
assert len(frozen_review)==15
assert frozen_definite | frozen_review == restored
assert restored <= set(current_by_id)
for stable_id in restored:
    row=current_by_id[stable_id]
    assert row["coordinate"] is None
    assert row["coordinate_basis"]=="UNPLACED"
    assert row["ratified_resident"] is False

gate=d10state["ownership_gate"]
assert gate["authority"]=="#4033"
assert gate["artifact"]=="knowledge/island-ownership-gate-v1.json"
assert gate["status"]=="SUPERSEDED-BY-OWNER-CORRECTION-4162"
assert "#4162" in d10state["owner_correction_single_stream"]["authority"]
assert d10state["owner_correction_single_stream"]["restored_total"]==70
assert d10state["target"]["selected_semantic_candidates"]==504
assert d10state["target"]["law_forced_coordinates"]==256
assert d10state["target"]["unplaced_selected_candidates"]==248
assert d10state["target"]["remaining_semantic_candidates"]==520
assert d10state["target"]["ratified_residents"]==0

print("ISLAND-OWNERSHIP-GATE=HISTORICAL-PASS")
print("old #4033 ownership split preserved as provenance")
print("owner correction #4162 restored 55 definite + 15 review rows into one D10 stream")
print("D10=504/1024 placed=256 unplaced=248 remaining=520 ratified=0")
