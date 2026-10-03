#!/usr/bin/env python3
"""#2700 current-baseline D4 + two-delta D6 product census.

A two-delta observation is NOT sufficient for D6 product placement.
The stronger theorem requires:
- exact same-base D4 parent;
- two independently observable deltas;
- independently specified middle corners;
- commutation/product law;
- local lower bound / no hidden authority.

Current controls:
1. DEFINE -> shared-location endpoint:
   known positive product control (#2511/#2518), owner residency handled elsewhere.
2. LAMBDA -> current TRANSFORMER:
   two separable deltas are observed, but #2591 does not prove the two middle
   corners / commuting product generator; therefore no D6 conclusion.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ELIGIBILITY = ROOT / "benchmarks" / "d5-sens-derivation-closeout" / "factor-eligibility.json"
PLACEMENT = ROOT / "benchmarks" / "post-d4-semantic-placement" / "placement.json"

KNOWN_BINDING_CONTROL = "setq-core-vs-define"
TRANSFORMER_CONTROL = "current-transformer-vs-lambda"


def main() -> int:
    data = json.loads(ELIGIBILITY.read_text(encoding="utf-8"))
    placement = json.loads(PLACEMENT.read_text(encoding="utf-8"))
    factors = data["factors"]
    controls = data["composite_controls"]

    assert placement["invariants"]["historical_rows"] == 19
    assert placement["invariants"]["new_nonselector_d5_candidates"] == 0
    candidate_rows = [row for row in placement["rows"] if row.get("candidate_coordinate")]
    assert len(candidate_rows) == 1, f"new placement candidate requires review: {candidate_rows}"
    assert candidate_rows[0]["operation"] == "SETQ"
    assert candidate_rows[0]["candidate_coordinate"].startswith("D6:001111")
    assert candidate_rows[0]["coordinate"] == "UNPLACED"

    # Factor rows: only the already-known binding family has a proved exact
    # D4 same-base parent with delta_count=2.
    d4_two_delta_factors = [
        row for row in factors
        if isinstance(row.get("strongest_same_base_parent"), str)
        and len(row["strongest_same_base_parent"]) == 4
        and row.get("delta_count") == 2
    ]
    assert [row["factor_id"] for row in d4_two_delta_factors] == ["shared-location-update"]

    controls_by_id = {row["control_id"]: row for row in controls}
    assert set(controls_by_id) == {KNOWN_BINDING_CONTROL, TRANSFORMER_CONTROL}

    binding = controls_by_id[KNOWN_BINDING_CONTROL]
    assert binding["parent"] == "0011"
    assert binding["delta_count"] == 2
    assert binding["classification"] == "SAME-PARENT-MULTI-DELTA"
    assert set(binding["observed_deltas"]) == {
        "target-resolution-scope",
        "missing-binding-policy",
    }

    transformer = controls_by_id[TRANSFORMER_CONTROL]
    assert transformer["parent"] == "0010"
    assert transformer["delta_count"] == 2
    assert transformer["classification"] == "SAME-PARENT-MULTI-DELTA"
    assert set(transformer["observed_deltas"]) == {
        "raw-form-input",
        "returned-form-protocol",
    }

    # #2591 is the explicit negative control: axis count alone does not prove
    # width, and current TRANSFORMER differs from LAMBDA on at least two axes
    # without an admitted two-middle-corner commuting product theorem.
    transformer_product_middle_corners_proved = False
    transformer_commutation_proved = False
    transformer_exact_d6_generator_proved = False

    transformer_d6_eligible = all([
        transformer_product_middle_corners_proved,
        transformer_commutation_proved,
        transformer_exact_d6_generator_proved,
    ])
    assert not transformer_d6_eligible

    # No other current factor/control supplies a new D4+two-delta product
    # theorem. The binding case is the known positive control and remains
    # isolated under #2538; it is not a new discovery in this lane.
    new_product_candidates = []
    assert new_product_candidates == []

    print("D6-THEOREM-FIRST-D4-PRODUCT=PASS")
    print("known-binding-product-controls=1")
    print("transformer-two-delta-observations=1")
    print("transformer-middle-corners-proved=0")
    print("transformer-commutation-proved=0")
    print("transformer-exact-d6-generator-proved=0")
    print("historical-placement-candidates=1")
    print("known-owner-ready-candidate=SETQ:D6:001111")
    print("new-d4-two-delta-product-families=0")
    print("RESULT=NO-NEW-D4-TWO-DELTA-FAMILY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
