#!/usr/bin/env python3
"""D10 Lisp-machine evaluator harvest: pinned executable source and identity checks.

Does not ratify semantics and does not claim source-level behavioral tests.
"""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((root / path).read_text(encoding="utf-8"))
ledger = read("knowledge/d10-lisp-machine-evaluator-harvest-v1.json")
inv = read("knowledge/d10-v1-semantic-inventory.json")
state = read("knowledge/d10-fill-v1-state.json")
foundation = read("knowledge/d1-d9-foundation.json")

assert ledger["schema"] == "d10-lisp-machine-evaluator-harvest-v1/v1"
assert ledger["status"] == "RESEARCH-UNRATIFIED"
rows = ledger["rows"]
assert len(rows) == ledger["accounting"]["selected"] == 31
assert len({r["stable_id"] for r in rows}) == len(rows)
assert len({r["semantic_name"] for r in rows}) == len(rows)
assert len({r["source_file"] for r in rows}) == 2

lower = {
    str(v).upper()
    for d in foundation["domains"].values()
    for v in d.get("residents", {}).values()
}
selected_ids = {r["stable_id"] for r in rows}
selected_names = {r["semantic_name"].upper() for r in rows}
other_names = {
    r["semantic_name"].upper() for r in inv["rows"]
    if r["stable_id"] not in selected_ids
}
assert not (selected_names & lower)
assert not (selected_names & other_names)
assert len(ledger["excluded"]) >= 5
assert all(x["reason"] for x in ledger["excluded"])

byid = {r["stable_id"]: r for r in inv["rows"]}
assert len(byid) == len(inv["rows"])
donors = {d["path"]: d["source_sha"] for d in ledger["donors"]}
source_lines = {}
for file, expected_sha in donors.items():
    raw = (root / file).read_bytes()
    blob = b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw
    assert hashlib.sha1(blob).hexdigest() == expected_sha
    source_lines[file] = raw.decode("utf-8").splitlines()

for row in rows:
    got = byid[row["stable_id"]]
    assert got["semantic_name"] == row["semantic_name"]
    assert got["source_class"] == "LISP-MACHINE-EVALUATOR-SEMANTIC-HARVEST"
    assert got["status"] == "SELECTED-RESEARCH-CANDIDATE"
    assert row["source_sha"] == donors[row["source_file"]]
    assert row["surface_uk"] and row["surface_ukr"] and row["behavior"]
    assert row["proposal_status"] == "pending-owner-review"
    assert row["ratified_resident"] is False
    assert row["coordinate"] is None and row["coordinate_basis"] == "UNPLACED"
    line = source_lines[row["source_file"]][row["source_line"] - 1]
    assert line.startswith("(00001001 " + row["source_name"])
    assert line[len("(00001001 " + row["source_name"]):][:1] in ("", " ", chr(9), ")")

selected = state["target"]["selected_semantic_candidates"]
assert selected >= ledger["accounting"]["after"]  # historical minimum, not a ceiling
assert len(inv["rows"]) == selected
assert len({r["semantic_name"] for r in inv["rows"]}) == selected
assert inv["accounting"] == {
    "selected_semantic_candidates": selected,
    "law_forced_coordinates": 256,
    "unplaced_selected_candidates": selected - 256,
    "remaining_semantic_inventory": 1024 - selected,
    "ratified_d10_residents": 0,
}
assert state["target"]["unplaced_selected_candidates"] == selected - 256
assert state["target"]["remaining_semantic_candidates"] == 1024 - selected
assert state["target"]["ratified_residents"] == 0
assert "knowledge/d10-lisp-machine-evaluator-harvest-v1.json" in inv["sources"]
print(f"D10-LISP-MACHINE-EVALUATOR-HARVEST: PASS ({len(rows)} added; {selected}/1024; ratified 0)")
