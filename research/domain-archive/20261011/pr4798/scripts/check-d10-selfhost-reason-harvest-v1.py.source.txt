#!/usr/bin/env python3
"""D10 self-hosting & proof semantic recovery: source identity, coordinates, duplicates.

This proves only pinned source declarations and registry invariants, not semantic
equivalence of the implementations, historical attribution, or owner ratification.
"""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
read = lambda p: json.loads((root / p).read_text(encoding="utf-8"))
h = read("knowledge/d10-selfhost-reason-harvest-v1.json")
inv = read("knowledge/d10-v1-semantic-inventory.json")
state = read("knowledge/d10-fill-v1-state.json")
foundation = read("knowledge/d1-d9-foundation.json")
assert h["schema"] == "d10-selfhost-reason-harvest-v1/v1"
assert h["status"] == "RESEARCH-UNRATIFIED"
rows = h["rows"]
assert len(rows) == h["accounting"]["selected"] == 23
assert len({x["stable_id"] for x in rows}) == 23
assert len({x["semantic_name"] for x in rows}) == 23
lower = {
    str(name).upper()
    for d in foundation["domains"].values()
    for name in d.get("residents", {}).values()
}
ours = {x["semantic_name"].upper() for x in rows}
other = {
    x["semantic_name"].upper()
    for x in inv["rows"]
    if x.get("source_class") != "SELFHOST-REASON-SEMANTIC-HARVEST"
}
assert not (ours & lower)
assert not (ours & other)
all_ids = {r["stable_id"]: r for r in inv["rows"]}
assert len(all_ids) == len(inv["rows"])
assert len({r["semantic_name"].upper() for r in inv["rows"]}) == len(inv["rows"])
donors = {r["path"]: r for r in h["donors"]}
assert set(donors) == {"lib/meta-eval.lisp", "lib/reason.lisp"}
lines = {}
for path, donor in donors.items():
    raw = (root / path).read_bytes()
    actual = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw
    ).hexdigest()
    assert actual == donor["source_sha"], (path, actual)
    lines[path] = raw.decode("utf-8").splitlines()
for row in rows:
    got = all_ids[row["stable_id"]]
    assert got["semantic_name"] == row["semantic_name"]
    assert got["source_class"] == "SELFHOST-REASON-SEMANTIC-HARVEST"
    assert got["status"] == "SELECTED-RESEARCH-CANDIDATE"
    assert row["source_sha"] == donors[row["source_file"]]["source_sha"]
    assert row["definition_form"] == donors[row["source_file"]]["definition_form"]
    assert row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED"
    assert row["ratified_resident"] is False
    assert row["proposal_status"] == "pending-owner-review"
    assert row["surface_uk"] and row["surface_ukr"] and row["behavior"]
    line = lines[row["source_file"]][row["source_line"] - 1]
    prefix = "(" + row["definition_form"] + " " + row["source_name"]
    assert line.startswith(prefix), (row["source_file"], row["source_line"])
    assert line[len(prefix):][:1] in ("", " ", chr(9), ")")
n = state["target"]["selected_semantic_candidates"]
assert n >= h["accounting"]["after"]  # historical checkpoint, not a ceiling
assert len(inv["rows"]) == n
assert inv["accounting"] == {
    "selected_semantic_candidates": n,
    "law_forced_coordinates": 256,
    "unplaced_selected_candidates": n-256,
    "remaining_semantic_inventory": 1024-n,
    "ratified_d10_residents": 0,
}
assert state["target"]["unplaced_selected_candidates"] == n-256
assert state["target"]["remaining_semantic_candidates"] == 1024-n
assert state["target"]["law_forced_coordinates"] == 256
assert state["target"]["ratified_residents"] == 0
assert "knowledge/d10-selfhost-reason-harvest-v1.json" in inv["sources"]
print(f"D10-SELFHOST-REASON-HARVEST: PASS ({len(rows)} new, {n}/1024, remaining {1024-n}, ratified 0)")
