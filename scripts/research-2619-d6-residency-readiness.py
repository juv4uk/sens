#!/usr/bin/env python3
"""#2619 — compose current D6 evidence into an owner-readiness gate.

This gate never admits a resident. It proves only that candidate 001111 has
reached the state where evidence work is complete and owner authority is the
remaining step.
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

TARGET = "001111"


def main() -> int:
    closure = runpy.run_path(str(CLOSURE))
    rows = closure["build_map"]()
    target = next(row for row in rows if row["coordinate"] == TARGET)

    assert len(rows) == 64
    assert sum(row["status"] == "generated" for row in rows) == 16
    assert sum(row["status"] == "UNKNOWN/free" for row in rows) == 48
    assert target["status"] == "UNKNOWN/free"
    assert target["semantic_member_of_ratified_domain"] is False
    assert target["placement_ref"] == ""
    assert target["manual_resident_required"] is False

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

    result = {
        "schema": "d6-residency-readiness/v1",
        "domain": "Core D6",
        "candidate": TARGET,
        "domain_ratified": True,
        "canonical_closure": {
            "generated": 16,
            "unknown_free": 48,
            "candidate_current_status": target["status"],
            "candidate_admitted": False,
        },
        "local_placement_theorem": {
            "parent": setq["strongest_local_parent"],
            "minimum_width": setq["local_minimum_width"],
            "placement": setq["placement"],
            "independent_deltas": ["scope", "miss"],
        },
        "falsifiers": {
            "alternative_parent": "survived",
            "nonprefix_scope": "survived-local-D6/distinct-standalone-D2",
            "cross_family_inheritance": "rejected",
        },
        "owner_action_required": True,
        "readiness": "READY-FOR-OWNER",
        "admitted": False,
        "non_conclusions": [
            "readiness is not ratification",
            "001111 is not a resident until explicit owner decision",
            "D6 pressure for SETQ does not transfer to SET, RETURN, FEXPR, FSUBR or TRANSFORMER",
            "standalone D2 product representation is a different domain and does not relocate the Core candidate",
        ],
    }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
