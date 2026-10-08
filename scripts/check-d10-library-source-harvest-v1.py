#!/usr/bin/env python3
"""Verify the D10 library *source harvest* without promoting names into residents.

This checker deliberately validates source provenance and research-only status.
It does not treat harvested DEFINE names as new D10 semantics.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

harvest = json.loads(
    (ROOT / "knowledge/d10-library-source-harvest-v1.json").read_text(encoding="utf-8")
)
inventory = json.loads(
    (ROOT / "knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8")
)
state = json.loads(
    (ROOT / "knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8")
)

EXPECTED_SOURCES = {
    "lib/quantity.lisp": {
        "blob_sha": "548bfc4092e8809a373d5397c6eafa884ac5ccef",
        "candidate_count": 42,
        "status": "HARVESTED",
    },
    "lib/translation.lisp": {
        "blob_sha": "6c3118daba896c64255efbb93c926a58d2f19829",
        "candidate_count": 31,
        "status": "HARVESTED",
    },
    "lib/reason.lisp": {
        "blob_sha": "dadc52a2f40f2f30ad77642898afb81980044c08",
        "candidate_count": 0,
        "status": "HOLD-ALTERNATE-HEAD-PATTERN",
    },
    "lib/si.lisp": {
        "blob_sha": "2b94f1ea6d2fb05c084c3a0d863c14119a5ba11f",
        "candidate_count": 29,
        "status": "HARVESTED",
    },
}
EXPECTED_COUNTS = {path: spec["candidate_count"] for path, spec in EXPECTED_SOURCES.items()}


def git_blob_sha(data: bytes) -> str:
    """Compute the canonical Git blob SHA-1 for exact source bytes."""
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


assert harvest["schema"] == "d10-library-harvest/v1"
assert harvest["authority"] == "#4013"
assert harvest["status"] == "RESEARCH-UNRATIFIED"
assert harvest["count"] == 102
assert "NO D10 positions invented" in harvest["law"]

# Every listed donor source must have exact provenance; a name census from a
# different source revision is not evidence for this pinned harvest.
listed_sources = {row["path"]: row["blob_sha"] for row in harvest["sources"]}
assert listed_sources == {
    path: spec["blob_sha"] for path, spec in EXPECTED_SOURCES.items()
}
source_results = {row["path"]: row for row in harvest["source_audit"]}
assert set(source_results) == set(EXPECTED_SOURCES)
for path, spec in EXPECTED_SOURCES.items():
    result = source_results[path]
    assert result["blob_sha"] == spec["blob_sha"]
    assert result["candidate_count"] == spec["candidate_count"]
    assert result["status"] == spec["status"]

    source_bytes = (ROOT / path).read_bytes()
    assert git_blob_sha(source_bytes) == spec["blob_sha"], (
        f"source changed at {path}; re-audit exact lines and explicitly update "
        "the harvest rather than silently reusing stale provenance"
    )

candidates = harvest["candidates"]
assert len(candidates) == harvest["count"]
candidate_counts = Counter(row["source"] for row in candidates)
assert dict(candidate_counts) == {
    path: count for path, count in EXPECTED_COUNTS.items() if count > 0
}

seen = set()
for row in candidates:
    path = row["source"]
    assert path in EXPECTED_SOURCES and EXPECTED_COUNTS[path] > 0
    assert row["blob_sha"] == EXPECTED_SOURCES[path]["blob_sha"]
    assert row["kind"] == "library-defined"
    assert row["status"] == "research-unratified"
    # These are raw source-census records, not identity assignments.
    assert "stable_id" not in row
    assert row.get("coordinate") is None
    assert row.get("ratified_resident") in (None, False)

    line_number = row["line"]
    assert isinstance(line_number, int) and line_number > 0
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    assert line_number <= len(lines), f"line outside pinned source: {path}:{line_number}"
    line = lines[line_number - 1]
    match = re.match(r"^\s*\(00001001\s+([^\s()]+)", line)
    assert match and match.group(1) == row["name"], (
        f"stale candidate anchor {path}:{line_number}: expected {row['name']!r}, "
        f"found {line!r}"
    )

    key = (path, line_number, row["name"])
    assert key not in seen, f"duplicate source candidate {key}"
    seen.add(key)

# This is the deliberate HOLD boundary: reason.lisp really exists in the
# source manifest, but uses a different exact-domain source-head pattern. The
# current harvesting regex did not enumerate it. Do not misread that as an
# empty semantic module or allocate slots to its index implementation.
assert candidate_counts.get("lib/reason.lisp", 0) == 0
assert "alternate-head-pattern" in source_results["lib/reason.lisp"]["status"].lower()

effect = harvest["inventory_effect"]
assert effect == {
    "selected_increment": 0,
    "coordinate_assignments": 0,
    "ratified_increment": 0,
    "reason": effect["reason"],
}
assert "semantic dedup" in effect["reason"].lower()

# The 102 rows are source-grounded research intake only. They are not the
# 102nd-through-? additions to the canonical inventory and cannot change D10
# selection count just by existing in this harvest file.
target = state["target"]
assert target["selected_semantic_candidates"] == 625
assert target["remaining_semantic_candidates"] == 399
assert target["law_forced_coordinates"] == 256
assert target["unplaced_selected_candidates"] == 369
assert target["ratified_residents"] == 0
assert len(inventory["rows"]) == 625
assert len({row["stable_id"] for row in inventory["rows"]}) == 625
assert len({row["semantic_name"] for row in inventory["rows"]}) == 625

print("D10-LIBRARY-SOURCE-HARVEST: PASS")
print("source records: quantity=42 translation=31 reason=0(HOLD alternate head) si=29")
print("raw source rows=102; selected increment=0; coordinates=0; ratified=0")
print("inventory=625/1024 remaining=399 law-forced=256 unplaced=369")
