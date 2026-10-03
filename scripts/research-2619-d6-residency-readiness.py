#!/usr/bin/env python3
"""#2619/#2723 — post-owner-decision D6 residency guard.

This gate now verifies that owner-ratified candidate 001111 is canonically
admitted and that the decision did not leak into adjacent/intermediate or
historically related capabilities.
"""

from __future__ import annotations

import json
import runpy
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CLOSURE = REPO / "benchmarks/d6-closure-map/run.py"
PRESSURE = REPO / "benchmarks/d6-width-pressure/run.py"
ALT_PARENT = REPO / "benchmarks/d6-alt-parent-falsifier/run.py"
NONPREFIX = REPO / "benchmarks/d6-nonprefix-falsifier/run.py"
BINDING = REPO / "scripts/research-2506-d6-binding-policy-generator.py"
MIDDLE_CORNERS = REPO / "scripts/research-2624-d6-middle-corners.py"

TARGET = "001111"
MIDDLE = {"001101", "001110"}


def main() -> int:
    closure = runpy.run_path(str(CLOSURE))
    rows = closure["build_map"]()
    target = next(row for row in rows if row["coordinate"] == TARGET)

    assert len(rows) == 64
    assert sum(row["status"] == "generated" for row in rows) == 16
    assert sum(row["status"] == "ratified-manual" for row in rows) == 1
    assert sum(row["status"] == "UNKNOWN/free" for row in rows) == 47
    assert target["status"] == "ratified-manual"
    assert target["semantic_member_of_ratified_domain"] is True
    assert target["placement_ref"] == "#2538:OD-001/#2723"
    assert target["manual_resident_required"] is True

    pressure = runpy.run_path(str(PRESSURE))
    pressure_map = pressure["build"]()
    setq = next(row for row in pressure_map["rows"] if row["operation"] == "SETQ")
    assert setq["strongest_local_parent"] == "D4 DEFINE / 0011"
    assert setq["local_minimum_width"] == "D6"
    assert setq["placement"] == "UNPLACED"
    for op in ("SET", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"):
        row = next(row for row in pressure_map["rows"] if row["operation"] == op)
        assert row["placement"] == "UNPLACED"
        assert row["local_minimum_width"] != "D6"

    binding = runpy.run_path(str(BINDING))
    assert binding["miss_refine"](binding["scope_refine"](binding["DEFINE"])) == binding["SETQ_CORE"]
    assert binding["scope_refine"](binding["miss_refine"](binding["DEFINE"])) == binding["SETQ_CORE"]
    assert len({
        binding["signature"](binding["DEFINE"]),
        binding["signature"](binding["CURRENT_FAIL"]),
        binding["signature"](binding["NEAREST_CREATE"]),
        binding["signature"](binding["SETQ_CORE"]),
    }) == 4

    alt = runpy.run_path(str(ALT_PARENT))
    assert alt["field_distance"](alt["DEFINE"], alt["SETQ_CORE"]) == ["scope", "miss"]
    for candidate in (alt["LOOKUP"], alt["BIND"], alt["CONS"]):
        assert candidate.base_family != alt["SETQ_CORE"].base_family

    nonprefix = runpy.run_path(str(NONPREFIX))
    assert nonprefix["min_binary_width"](4) == 2
    canonical = {
        "DEFINE": "00",
        "CURRENT_FAIL": "01",
        "NEAREST_CREATE": "10",
        "SETQ_CORE": "11",
    }
    assert nonprefix["factor_preserving"](canonical)
    assert TARGET == "0011" + canonical["SETQ_CORE"]

    # Fresh #2624/#2625 guard: the two one-axis product corners are real
    # proof states, but proof-state existence is not language residency.
    middle = runpy.run_path(str(MIDDLE_CORNERS))
    assert middle["main"]() == 0
    middle_rows = [row for row in rows if row["coordinate"] in MIDDLE]
    assert len(middle_rows) == 2
    for row in middle_rows:
        assert row["status"] == "UNKNOWN/free"
        assert row["semantic_member_of_ratified_domain"] is False
        assert row["placement_ref"] == ""

    result = {
        "schema": "d6-residency-readiness/v1",
        "domain": "Core D6",
        "candidate": TARGET,
        "domain_ratified": True,
        "canonical_closure": {
            "generated": 16,
            "ratified_manual": 1,
            "unknown_free": 47,
            "candidate_current_status": target["status"],
            "candidate_admitted": True,
        },
        "local_placement_theorem": {
            "parent": setq["strongest_local_parent"],
            "minimum_width": setq["local_minimum_width"],
            "placement": setq["placement"],
            "independent_deltas": ["scope", "miss"],
        },
        "middle_corners": {
            "coordinates": sorted(MIDDLE),
            "status": "PROOF-INTERMEDIATE-NOT-RESIDENT",
            "admitted": False,
        },
        "falsifiers": {
            "alternative_parent": "survived",
            "nonprefix_scope": "survived-local-D6/distinct-standalone-D2",
            "cross_family_inheritance": "rejected",
        },
        "owner_action_required": False,
        "owner_decision": "#2538:OD-001/#2723",
        "readiness": "OWNER-RATIFIED-APPLIED",
        "admitted": True,
        "non_conclusions": [
            "owner ratification of 001111 does not transfer to SET, RETURN, FEXPR, FSUBR or TRANSFORMER",
            "001100 parent duplicate remains non-resident",
            "001101/001110 proof intermediates remain non-residents",
            "standalone D2 product representation is a different domain and does not relocate the Core candidate",
            "one-axis D6 proof corners 001101/001110 remain non-residents",
        ],
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
