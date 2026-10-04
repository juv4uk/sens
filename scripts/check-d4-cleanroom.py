#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cleanroom_path = root / "knowledge/d4-cleanroom.json"
tournament_path = root / "knowledge/d4-parent-law-tournament.json"

d = json.loads(cleanroom_path.read_text(encoding="utf-8"))
t = json.loads(tournament_path.read_text(encoding="utf-8"))

assert d["authority"] == "#3225"
assert d["admitted"] == {
    "0110": "CDAR",
    "0111": "CDDR",
    "1000": "CAAR",
    "1001": "CADR",
}
assert len(d["unknown"]) == 12
assert set(d["admitted"]).isdisjoint(d["unknown"])
assert set(d["admitted"]) | set(d["unknown"]) == {f"{i:04b}" for i in range(16)}

# Clean-room semantic source must contain none of the legacy D4 resident labels.
text = cleanroom_path.read_text(encoding="utf-8")
for banned in [
    "APPLY","EVAL","LAMBDA","DEFINE","LOOKUP","BIND","EVLIS","EVCON","LIST","NOT",
    "arithmetic-family-A","arithmetic-family-M"
]:
    assert banned not in text, banned

# Parent-law tournament: placement is earned only by a two-child generator.
assert t["schema"] == "d4-cleanroom-parent-law/v1"
assert t["authority"] == "#3244"
assert t["parent_cleanroom"] == "#3225"
assert t["d3_authority"] == "#3202"
assert t["statuses"] == ["PROVED-GENERATOR", "REFUTED", "UNKNOWN"]
assert t["candidate_context"] == {
    "minimality_candidate": "#3247",
    "candidate_table_is_semantic_authority": False,
    "unallocated_coordinates_allowed": True,
    "promotion_rule": "candidate presence never upgrades relation status without a parent-law certificate",
}
assert t["suffix_rule"] == {
    "required_children": 2,
    "suffixes": ["0", "1"],
    "isolated_child_placement_allowed": False,
}

parents = {
    "000": "EMPTY",
    "001": "QUOTE",
    "010": "ATOM",
    "011": "CDR",
    "100": "CAR",
    "101": "EQ",
    "110": "COND",
    "111": "CONS",
}
assert {row["bits"]: row["role"] for row in t["parents"]} == parents

capabilities = {row["id"]: row for row in t["capabilities"]}
assert set(capabilities) == {
    "late-bound-executable-construction",
    "unbounded-semantic-reentry",
}
assert all(row["coordinate"] is None for row in capabilities.values())

relations = t["candidate_relations"]
assert len(relations) == 8
assert {row["parent"] for row in relations} == set(parents)
for row in relations:
    assert row["status"] in t["statuses"]
    pair = row["capability_pair"]
    assert len(pair) == 2 and set(pair) == set(capabilities)
    if row["status"] == "PROVED-GENERATOR":
        assert row["shared_generator"]
        assert row["sibling_meaning"]
        assert row["parent_recovery"]
        assert row["falsifier"]
    else:
        # UNKNOWN/REFUTED must not smuggle a coordinate or half-family placement.
        assert row["shared_generator"] is None
        assert row["sibling_meaning"] is None
        assert row["parent_recovery"] is None
        assert row["falsifier"] is None

controls = {row["parent"]: row for row in t["positive_controls"]}
assert set(controls) == {"011", "100"}
for parent, row in controls.items():
    assert row["status"] == "PROVED-GENERATOR"
    assert set(row["children"]) == {"0", "1"}
    assert row["children"]["0"] == parent + "0"
    assert row["children"]["1"] == parent + "1"
    assert row["equation"]
    assert row["parent_recovery"]
    assert row["falsifier"]
    assert set(row["suffix_meaning"]) == {"0", "1"}

selector_relations = {row["parent"]: row for row in t["selector_parent_relations"]}
assert set(selector_relations) == set(parents)
for parent, row in selector_relations.items():
    assert row["status"] in t["statuses"]
    if parent in {"011", "100"}:
        assert row["status"] == "PROVED-GENERATOR"
        assert row["control_ref"] == f"positive_controls:{parent}"
    else:
        assert row["status"] == "REFUTED"
        assert row["reason"]

single = t["single_child_negative_control"]
assert single["status"] == "UNKNOWN"
assert single["child0_semantics"]
assert single["child1_semantics"] is None
assert single["shared_generator"] == "partial-only"
assert single["falsifier"]

# No candidate relation may directly assign one child coordinate.
# Capability records may explicitly carry coordinate=null to prove that placement
# has not been earned; the prohibition applies to candidate parent relations.
for row in relations:
    for forbidden_key in ("coordinate", "child", "child0", "child1", "children"):
        assert forbidden_key not in row, (row["parent"], forbidden_key)

tournament_text = tournament_path.read_text(encoding="utf-8")

# Historical D4 semantic names remain forbidden as clean-room premises.
for banned in [
    "APPLY","EVAL","LAMBDA","DEFINE","LOOKUP","BIND","EVLIS","EVCON","LIST","NOT",
    "arithmetic-family-A","arithmetic-family-M"
]:
    assert banned not in tournament_text, banned

print("D4-CLEANROOM-GUARD: PASS")
print("D4-PARENT-LAW-TOURNAMENT: PASS")
