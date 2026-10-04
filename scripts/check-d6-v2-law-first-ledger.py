#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
d = json.loads((root / "knowledge/d6-v2-law-first-ledger.json").read_text(encoding="utf-8"))
rows = d["rows"]
summary = d["summary"]
unplaced = d["unplaced_law_anchors"]

assert d["status"] == "research-semantic-inventory-complete-coordinate-unratified"
assert d["foundation"].startswith("#3331")
assert len(rows) == 64
assert {r["coordinate"] for r in rows} == {f"{i:06b}" for i in range(64)}

# Coordinate geometry remains intentionally incomplete.
assert sum(r["status"] == "PROVED" for r in rows) == 16
assert sum(r["status"] == "CANDIDATE-WITH-LAW" for r in rows) == 16
assert sum(r["status"] == "UNKNOWN" for r in rows) == 32
assert len({r["coordinate"] for r in rows if r["status"] != "UNKNOWN"}) == 32

# Semantic inventory is complete independently of coordinate placement.
assert summary["capacity"] == 64
assert summary["law_covered_semantics"] == 64
assert summary["semantic_inventory_complete"] is True
assert summary["coordinate_inventory_complete"] is False

unplaced_names = [name for family in unplaced for name in family["names"]]
assert len(unplaced_names) == 32
assert len(set(unplaced_names)) == 32
assert all(family["placement"] == "UNPLACED" for family in unplaced)

for name in ["RPLACA", "RPLACD", "NCONC", "NREVERSE", "SETF"]:
    assert name in d["review_first"]

print("D6-V2-LAW-FIRST-LEDGER: PASS")
print("semantic=64/64 placed-or-anchored=32 unplaced-law=32 coordinate-unknown=32")
