#!/usr/bin/env python3
"""#2624 — D6 middle-corner residency falsifier.

The two one-axis states in the binding-policy product are semantically real
states of the proved square. This script tests the stronger claim that they
must also be independent SENS residents.

Result boundary:
- semantic proof corner != admitted language resident;
- exact 01/10 orientation is not semantically forced;
- no D6 occupancy mutation follows from this witness.
"""

from __future__ import annotations

import json
import runpy
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BINDING = REPO / "scripts/research-2506-d6-binding-policy-generator.py"
ALT_PARENT = REPO / "benchmarks/d6-alt-parent-falsifier/run.py"
PRESSURE = REPO / "benchmarks/d6-width-pressure/run.py"
CLOSURE = REPO / "benchmarks/d6-closure-map/run.py"

MIDDLE = {"001101", "001110"}


def main() -> int:
    binding = runpy.run_path(str(BINDING))
    sig = binding["signature"]

    define = binding["DEFINE"]
    current_fail = binding["CURRENT_FAIL"]
    nearest_create = binding["NEAREST_CREATE"]
    setq = binding["SETQ_CORE"]

    signatures = {
        "DEFINE": sig(define),
        "CURRENT_FAIL": sig(current_fail),
        "NEAREST_CREATE": sig(nearest_create),
        "SETQ_CORE": sig(setq),
    }
    assert len(set(signatures.values())) == 4

    # The middle states are genuine one-axis semantic corners.
    assert current_fail != define and current_fail != setq
    assert nearest_create != define and nearest_create != setq
    assert binding["miss_refine"](define) == current_fail
    assert binding["scope_refine"](define) == nearest_create

    # But the exact assignment of the two one-axis meanings to 01/10 is not
    # forced: swapping the semantic axis order keeps the parent and target.
    canonical = {
        "DEFINE": "001100",
        "CURRENT_FAIL": "001101",
        "NEAREST_CREATE": "001110",
        "SETQ_CORE": "001111",
    }
    swapped = {
        "DEFINE": "001100",
        "CURRENT_FAIL": "001110",
        "NEAREST_CREATE": "001101",
        "SETQ_CORE": "001111",
    }
    assert canonical["DEFINE"] == swapped["DEFINE"]
    assert canonical["SETQ_CORE"] == swapped["SETQ_CORE"]
    assert {canonical["CURRENT_FAIL"], canonical["NEAREST_CREATE"]} == MIDDLE
    assert {swapped["CURRENT_FAIL"], swapped["NEAREST_CREATE"]} == MIDDLE
    assert canonical["CURRENT_FAIL"] != swapped["CURRENT_FAIL"]

    # Current tested D1-D4 alternatives do not identify either middle state
    # as an existing language operation.
    alt = runpy.run_path(str(ALT_PARENT))
    known_caps = {
        "DEFINE": alt["DEFINE"],
        "SETQ_CORE": alt["SETQ_CORE"],
        "LOOKUP": alt["LOOKUP"],
        "BIND": alt["BIND"],
        "CONS": alt["CONS"],
    }
    assert all(cap != current_fail for cap in known_caps.values())
    assert all(cap != nearest_create for cap in known_caps.values())

    # The historical width-pressure classifier has one local D6 positive
    # control only: SETQ. No middle-corner operation is admitted there.
    pressure = runpy.run_path(str(PRESSURE))["build"]()
    d6_rows = [r for r in pressure["rows"] if r["local_minimum_width"] == "D6"]
    assert [r["operation"] for r in d6_rows] == ["SETQ"]

    # Canonical D6 closure still leaves both coordinates non-members.
    rows = runpy.run_path(str(CLOSURE))["build_map"]()
    middle_rows = [r for r in rows if r["coordinate"] in MIDDLE]
    assert len(middle_rows) == 2
    for row in middle_rows:
        assert row["status"] == "UNKNOWN/free"
        assert row["semantic_member_of_ratified_domain"] is False
        assert row["placement_ref"] == ""

    result = {
        "schema": "d6-middle-corner-residency/v1",
        "domain": "Core D6",
        "candidate_set": sorted(MIDDLE),
        "semantic_product_states": {
            "current-fail": "proved-one-axis-corner",
            "nearest-create": "proved-one-axis-corner",
        },
        "coordinate_orientation": "UNFORCED-SWAP-CLASS",
        "bounded_existing_operation_match": "NONE",
        "canonical_map_status": "UNKNOWN/free",
        "resident_status": "UNPROVEN",
        "placement": "UNPLACED",
        "decision": "PROOF-INTERMEDIATE-NOT-RESIDENT",
        "non_conclusions": [
            "semantic existence of a product corner does not admit a language resident",
            "001101 and 001110 cannot be assigned fixed axis names from current evidence",
            "future independent capability evidence may reopen residency",
            "no D6 occupancy changes here",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
