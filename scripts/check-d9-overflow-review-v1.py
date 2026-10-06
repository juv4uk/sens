#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=json.loads((root/"knowledge/d8-v2-overflow-ledger.json").read_text(encoding="utf-8"))
review=json.loads((root/"knowledge/d9-overflow-review-v1.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d9-fill-v1-state.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))

assert review["schema"]=="d9-overflow-review-v1/v1"
assert review["status"]=="RESEARCH-UNRATIFIED"
assert review["authority"]=="#3965"
assert review["source"]=="knowledge/d8-v2-overflow-ledger.json"

rows=review["rows"]
assert len(source["rows"])==34
assert len(rows)==34
assert len({r["stable_id"] for r in rows})==34
assert len({r["semantic_name"] for r in rows})==34
assert {r["semantic_name"] for r in rows}=={r["semantic_name"] for r in source["rows"]}

counts={}
for row in rows:
    counts[row["decision"]]=counts.get(row["decision"],0)+1
assert counts=={
    "SELECT-D9-CANDIDATE":20,
    "HOLD-SEMANTIC-REVIEW":11,
    "REJECT-EXACT-LOWER-DUPLICATE":3,
}
assert review["accounting"]=={
    "source_rows":34,
    "selected_d9_candidates":20,
    "hold_semantic_review":11,
    "reject_exact_lower_duplicate":3,
    "d9_selected_before_review":128,
    "d9_selected_after_review":148,
    "d9_remaining_after_review":364,
    "ratified_d9_residents":0,
}

by_name={r["semantic_name"]:r for r in rows}
expected_reject={
    "APPLY":"D4:0000 APPLY",
    "COMPOSE":"D6:001011 COMPOSE",
    "REDUCE":"D6:101110 REDUCE",
}
for name,lower in expected_reject.items():
    row=by_name[name]
    assert row["decision"]=="REJECT-EXACT-LOWER-DUPLICATE"
    assert row["exact_lower_duplicate"] is True
    assert row["lower_identity"]==lower
    assert row["selected_d9_candidate"] is False
    assert row["d9_coordinate"] is None

assert foundation["domains"]["D4"]["residents"]["0000"]=="APPLY"
assert foundation["domains"]["D6"]["residents"]["001011"]=="COMPOSE"
assert foundation["domains"]["D6"]["residents"]["101110"]=="REDUCE"

# Name equality is not semantic equality: D2 OPEN/CLOSE are structural syntax,
# while these reviewed rows are stream operations.
assert foundation["domains"]["D2"]["residents"]["10"]=="OPEN"
assert foundation["domains"]["D2"]["residents"]["01"]=="CLOSE"
for name in ("OPEN","CLOSE"):
    row=by_name[name]
    assert row["decision"]=="SELECT-D9-CANDIDATE"
    assert row["exact_lower_duplicate"] is False
    assert row["selected_d9_candidate"] is True
    assert row["d9_coordinate"] is None

selected=[r for r in rows if r["selected_d9_candidate"]]
assert len(selected)==20
assert all(r["d9_coordinate"] is None for r in selected)

target=state["target"]
assert target["domain"]=="D9"
assert target["capacity"]==512
assert target["selected_semantic_candidates"]==148
assert target["remaining_semantic_candidates"]==364
assert target["ratified_residents"]==0
assert state["overflow_review"]=={
    "artifact":"knowledge/d9-overflow-review-v1.json",
    "source_rows":34,
    "selected":20,
    "hold":11,
    "rejected_exact_lower_duplicate":3,
}

print("D9-OVERFLOW-REVIEW-V1: PASS")
print("selected=20 hold=11 reject-lower-duplicate=3 total-selected=148/512 remaining=364")
