#!/usr/bin/env python3
"""Verify complete D10 v17 10-bit RESEARCH gauge; never ratify or admit T5.

Existing 719 coordinates are immutable. Fill only the 305 unallocated research
entries by ordered smallest-free-code assignment in this separate pinned map.
A research coordinate is not a physical executable instruction.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = "knowledge/d10-v17-complete-research-gauge-20261012.json"
EXPECTED_SOURCE = "knowledge/d10-v17-semantic-inventory.json"
BITS = re.compile(r"^[01]{10}$")
STATES = (
    "PRESERVED_LIVE_RESEARCH_COORDINATE",
    "PROPOSED_ORDERED_FREE_RESEARCH_GAUGE",
)

def require(condition, msg):
    if not condition:
        raise ValueError("D10_COMPLETE_GAUGE_BLOCK: " + msg)

def git_blob(data: bytes):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def verify(source, gauge, pointer):
    origin = gauge["origin"]
    require(origin["path"] == EXPECTED_SOURCE, "source path")
    require(gauge["schema"] == "d10-v17-complete-research-coordinate-gauge/v1", "schema")
    require(gauge["authority"] == "RESEARCH-ONLY-COORDINATE-PROPOSAL-NOT-RATIFICATION",
            "no ratification authority")
    require(pointer["canonical_current"]["path"] == EXPECTED_SOURCE
            and pointer["canonical_current"]["git_blob"] == origin["git_blob"],
            "live inventory diverged from frozen research gauge")
    require(source["schema"] == "d10-v17-semantic-inventory/v1", "source schema")
    require(source["domain"] == "D10" and source["capacity"] == 1024 and
            source["width"] == 10, "D10 bit-width or capacity")
    current_rows = source["rows"]
    mapped = gauge["rows"]
    require(len(current_rows) == len(mapped) == 1024, "missing or surplus rows")
    ids = [r["stable_id"] for r in current_rows]
    names = [r["semantic_name"].casefold() for r in current_rows]
    require(len(set(ids)) == len(set(names)) == 1024, "duplicate source identities")
    preserved = [r["coordinate"] for r in current_rows if r.get("coordinate") is not None]
    require(len(preserved) == len(set(preserved)) == 719
            and all(isinstance(x,str) and BITS.fullmatch(x) for x in preserved),
            "changed or colliding canonical coordinates")
    available = [format(i, "010b") for i in range(1024) if format(i, "010b") not in set(preserved)]
    require(len(available) == 305, "wrong free space")
    add = 0
    used = []
    for n, (original, candidate) in enumerate(zip(current_rows, mapped)):
        old_code = original["coordinate"]
        flag = STATES[0] if old_code is not None else STATES[1]
        next_code = old_code if old_code is not None else available[add]
        if old_code is None:
            add += 1
        require(candidate["index"] == n and
                candidate["stable_id"] == original["stable_id"] and
                candidate["semantic_name"] == original["semantic_name"],
                "source row identity/sequence drift")
        require(candidate["coordinate"] == next_code and
                candidate["assignment"] == flag, "not the deterministic smallest-free mapping")
        require(candidate["ratified"] is False and
                candidate["physical_t5_authorized"] is False,
                "fabricated ratification or physical execution authority")
        used.append(candidate["coordinate"])
    require(add == 305 and len(set(used)) == 1024 and
            set(used) == {format(i, "010b") for i in range(1024)},
            "not a complete bijective 10-bit map")
    require(not any(r.get("ratified_resident") is True for r in current_rows),
            "live domain ratification cannot be silently inferred")
    expected = {
        "capacity": 1024, "candidate_ids": 1024, "unique_semantic_names": 1024,
        "existing_coordinates_preserved": 719,
        "new_research_gauge_coordinates_proposed": 305,
        "total_provisional_map_coordinates": 1024,
        "remaining_provisional_codes": 0,
        "canonical_live_coordinates_unchanged": 719,
        "ratified_new": 0, "physical_t5_authorized_new": 0,
    }
    require(gauge["accounting"] == expected, "false completion accounting")
    return {"research": 1024, "canonical_placed": 719,
            "new_proposed": 305, "map_unique": 1024,
            "ratified": 0, "runtime_authorized": 0}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    gauge = json.loads((root/MAP).read_text(encoding="utf-8"))
    origin = gauge["origin"]
    source_file = (root/origin["path"]).resolve()
    require(source_file.is_relative_to(root) and source_file.is_file(), "unsafe source path")
    source_bytes = source_file.read_bytes()
    require(git_blob(source_bytes) == origin["git_blob"], "source SHA changed")
    source = json.loads(source_bytes)
    pointer = json.loads((root/"knowledge/d10-current-inventory.json").read_text())
    result = verify(source, gauge, pointer)
    if args.self_test:
        mutations = [
            ("duplicate address", lambda x: x["rows"][719].update(
                coordinate=x["rows"][0]["coordinate"])),
            ("shift another code", lambda x: x["rows"][720].update(coordinate="0000000000")),
            ("change stable id", lambda x: x["rows"][1023].update(stable_id="FORGED")),
            ("change row sequence", lambda x: x["rows"][719].update(index=718)),
            ("forge ratification", lambda x: x["rows"][719].update(ratified=True)),
            ("forge physical opcode", lambda x: x["rows"][1023].update(physical_t5_authorized=True)),
            ("lose one row", lambda x: x["rows"].pop()),
        ]
        for label, modify in mutations:
            tampered = copy.deepcopy(gauge)
            modify(tampered)
            try:
                verify(source, tampered, pointer)
            except ValueError:
                continue
            raise ValueError("D10_COMPLETE_GAUGE_BLOCK: negative mutation escaped: "+label)
        result["negative_cases_rejected"] = len(mutations)
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
