#!/usr/bin/env python3
"""Validate monotonic D10 history without falsifying pinned historical blobs.

Old research guards must inspect the EXACT 625-row historical *view*, while
newer machine inventory may append research-only rows. Reconstruct a frozen
inventory by reversing audited append events and check its original Git SHA.
Neither old snapshots nor ratified domains get rewritten.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
BASELINE = "73dd518469f972c55411e004b70b054ba8b3ec86"
APPEND = "knowledge/d10-historical-primary-selected-20261009.json"

def git_blob(data: dict) -> str:
    b = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

def historic_view(current: dict, expected_blob: str = BASELINE) -> dict:
    if git_blob(current) == expected_blob:
        return copy.deepcopy(current)
    work = copy.deepcopy(current)
    assert work["sources"][-1] == APPEND, "unrecognized D10 append donor; fail closed"
    batch = json.loads((ROOT / APPEND).read_text(encoding="utf-8"))
    start = batch["source_foundation"]["prior_selected"]
    count = batch["accounting"]["new_selected"]
    assert batch["source_foundation"]["d10_prior_blob"] == BASELINE
    assert expected_blob == BASELINE, "unsupported historical D10 snapshot SHA"
    assert len(work["rows"]) == start + count == 629
    assert work["accounting"]["selected_semantic_candidates"] == 629
    assert work["accounting"]["ratified_d10_residents"] == 0
    append_rows = work["rows"][start:]
    for actual, donor in zip(append_rows, batch["rows"]):
        assert actual["stable_id"] == donor["stable_id"]
        assert actual["semantic_name"] == donor["semantic_name"]
        assert actual["coordinate"] is None
        assert actual["ratified_resident"] is False
        assert actual["source_class"] == donor["source_class"]
        assert actual["primary_source_url"] == donor["primary_url"]
    assert len(append_rows) == count
    work["rows"] = work["rows"][:start]
    work["sources"].pop()
    work["accounting"]["selected_semantic_candidates"] = start
    work["accounting"]["unplaced_selected_candidates"] = start - 256
    work["accounting"]["remaining_semantic_inventory"] = 1024 - start
    assert git_blob(work) == expected_blob, "historical content changed, not monotonic"
    return work

def pinned_inventory_git_blob(path: Path) -> str:
    """Historical pin *validation* (not hash of the current file)."""
    if path.resolve() != INVENTORY.resolve():
        raise ValueError("only D10 inventory may be interpreted as a historical pin")
    current = json.loads(path.read_text(encoding="utf-8"))
    historic_view(current, BASELINE)
    return BASELINE
