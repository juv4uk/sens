#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ledger=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))
review_ledger=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))
restoration=json.loads((root/"knowledge/d10-single-stream-restoration-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))

assert ledger["schema"]=="d10-noncore-reclassification-v1/v1"
assert ledger["status"]=="PRESERVED-RECLASSIFIED"
assert ledger["authority"]=="#4047"
assert len(ledger["rows"])==55
assert all(r["decision"]=="RECLASSIFIED-NONCORE" for r in ledger["rows"])

moved={r["stable_id"] for r in ledger["rows"]}
review_moved={r["stable_id"] for r in review_ledger["rows"]}
restored={r["stable_id"] for r in restoration["rows"]}
current={r["stable_id"] for r in inventory["rows"]}

assert len(moved)==55
assert len(review_moved)==15
assert moved|review_moved==restored
assert restored <= current

for row in inventory["rows"]:
    if row["stable_id"] in restored:
        assert row["coordinate"] is None
        assert row["coordinate_basis"]=="UNPLACED"
        assert row["ratified_resident"] is False
        assert row["restoration"]["authority"]=="#4162"

target=state["target"]
selected=target["selected_semantic_candidates"]
remaining=target["remaining_semantic_candidates"]
assert selected>=504
assert remaining==1024-selected
assert target["law_forced_coordinates"]==256
assert target["unplaced_selected_candidates"]==selected-256
assert target["ratified_residents"]==0

assert state["ownership_gate"]["status"]=="SUPERSEDED-BY-OWNER-CORRECTION-4162"
assert state["ownership_cleanup_v1"]["status"]=="HISTORICAL-REVERSED-BY-4162"
assert state["ownership_cleanup_v1"]["restored_to_d10"]==55
assert state["ownership_cleanup_v2"]["status"]=="HISTORICAL-REVERSED-BY-4162"
assert state["ownership_cleanup_v2"]["restored_to_d10"]==15

print("D10-OWNERSHIP-CLEANUP-1=HISTORICAL-PASS")
print(f"historical-removed=55 restored-by-4162=55 inventory={selected}/1024")
