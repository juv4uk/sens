#!/usr/bin/env python3
"""Historical D10 Interlisp/PSL proposal gate: uniqueness, provenance, counts; no runtime proof."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
read = lambda p: json.loads((root / p).read_text(encoding="utf-8"))
h = read("knowledge/d10-interlisp-psl-history-harvest-v1.json")
inv = read("knowledge/d10-v1-semantic-inventory.json")
st = read("knowledge/d10-fill-v1-state.json")
f = read("knowledge/d1-d9-foundation.json")
assert h["status"] == "RESEARCH-UNRATIFIED" and len(h["rows"]) == 13
assert len({r["stable_id"] for r in h["rows"]}) == len(h["rows"])
assert len({r["semantic_name"] for r in h["rows"]}) == len(h["rows"])
lower = {str(v).upper() for d in f["domains"].values() for v in d.get("residents", {}).values()}
names = {r["semantic_name"] for r in h["rows"]}
other = {r["semantic_name"] for r in inv["rows"] if r.get("source_class") != "INTERLISP-PSL-HISTORICAL-HARVEST"}
assert not (names & lower) and not (names & other)
byid = {r["stable_id"]: r for r in inv["rows"]}
assert len(byid) == len(inv["rows"])
for r in h["rows"]:
    assert byid[r["stable_id"]]["semantic_name"] == r["semantic_name"]
    assert byid[r["stable_id"]]["source_class"] == "INTERLISP-PSL-HISTORICAL-HARVEST"
    assert r["source_url"].startswith("https://") and r["source_locator"]
    assert r["surface_uk"] and r["surface_ukr"] and r["behavior"]
    assert r["implementation_status"] == "HISTORICAL-SOURCE-ONLY"
    assert r["proposal_status"] == "pending-owner-review"
    assert r["coordinate"] is None and r["ratified_resident"] is False
n = st["target"]["selected_semantic_candidates"]
assert n >= h["accounting"]["after"] and len(inv["rows"]) == n
assert len({r["semantic_name"] for r in inv["rows"]}) == n
assert inv["accounting"] == {
    "selected_semantic_candidates":n,"law_forced_coordinates":256,
    "unplaced_selected_candidates":n-256,"remaining_semantic_inventory":1024-n,
    "ratified_d10_residents":0}
assert st["target"]["remaining_semantic_candidates"] == 1024-n
assert st["target"]["unplaced_selected_candidates"] == n-256
assert st["target"]["ratified_residents"] == 0
print(f"D10-HISTORICAL-INTERLISP-PSL: PASS ({len(h['rows'])} selected, {n}/1024, ratified 0)")
