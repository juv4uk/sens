#!/usr/bin/env python3
"""OD-005 -> D6 theorem-input rebase audit (#2755).

Neutral audit only.  It does not choose a D5/D6 placement and performs zero
occupancy mutation.  It proves that the merged full historical D5 map changed
the evidence surface consumed by the older D6 theorem-input bundle.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D5_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
PLACEMENT = ROOT / "benchmarks" / "post-d4-semantic-placement" / "placement.json"

REQUIRED_STATUS_FIELDS = ("phase", "status", "semantic_resident")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit() -> dict:
    d5 = load(D5_MAP)
    placement = load(PLACEMENT)

    rows = d5["coordinates"]
    assert d5["width"] == 5
    assert d5["capacity"] == 32
    assert len(rows) == 32
    assert len({row["coordinate"] for row in rows}) == 32
    assert all(len(row["coordinate"]) == 5 for row in rows)

    d5_setq = next(row for row in rows if row["name"] == "SETQ")
    placement_setq = next(row for row in placement["rows"] if row["operation"] == "SETQ")

    missing_status = {
        field: sum(field not in row for row in rows)
        for field in REQUIRED_STATUS_FIELDS
    }

    old = placement["invariants"]
    old_sparse_baseline = {
        "selector_generated": old["d5_selector_generated"],
        "unknown_free": old["d5_unknown_free"],
        "manual_nonselector": old["d5_manual_nonselector_residents"],
    }

    dual_claim = {
        "d5_historical_coordinate": d5_setq["coordinate"],
        "placement_exact_domain": placement_setq["exact_domain"],
        "placement_coordinate": placement_setq["coordinate"],
        "placement_candidate": placement_setq.get("candidate_coordinate"),
    }

    explicit_status = all(count == 0 for count in missing_status.values())
    old_baseline_matches_full_map = (
        old_sparse_baseline["selector_generated"] == 32
        and old_sparse_baseline["unknown_free"] == 0
    )

    reasons: list[str] = []
    if not explicit_status:
        reasons.append("d5-full-map-lacks-phase-status-semantic-resident")
    if not old_baseline_matches_full_map:
        reasons.append("d6-placement-ledger-still-encodes-pre-od005-d5-baseline")
    if (
        d5_setq["coordinate"] == "00111"
        and placement_setq.get("candidate_coordinate") == "D6:001111 (OD-001 owner-ready only)"
    ):
        reasons.append("setq-has-d5-coordinate-and-d6-placement-claim")

    return {
        "d5_historical_rows": len(rows),
        "d5_unallocated": d5["status_counts"]["unallocated"],
        "missing_status_fields": missing_status,
        "old_d6_input_d5_baseline": old_sparse_baseline,
        "setq": dual_claim,
        "reasons": reasons,
    }


def self_test() -> None:
    result = audit()
    assert result["d5_historical_rows"] == 32
    assert result["d5_unallocated"] == 0
    assert result["old_d6_input_d5_baseline"] == {
        "selector_generated": 8,
        "unknown_free": 24,
        "manual_nonselector": 0,
    }
    assert result["setq"]["d5_historical_coordinate"] == "00111"
    assert result["setq"]["placement_candidate"] == "D6:001111 (OD-001 owner-ready only)"
    assert "d5-full-map-lacks-phase-status-semantic-resident" in result["reasons"]
    assert "d6-placement-ledger-still-encodes-pre-od005-d5-baseline" in result["reasons"]
    assert "setq-has-d5-coordinate-and-d6-placement-claim" in result["reasons"]


def main() -> int:
    self_test()
    result = audit()

    print("D5-HISTORICAL-ROWS=32")
    print("D5-HISTORICAL-UNALLOCATED=0")
    print(
        "OLD-D6-D5-BASELINE="
        f"{result['old_d6_input_d5_baseline']['selector_generated']}+"
        f"{result['old_d6_input_d5_baseline']['unknown_free']}+"
        f"{result['old_d6_input_d5_baseline']['manual_nonselector']}"
    )
    print(f"SETQ-D5={result['setq']['d5_historical_coordinate']}")
    print(f"SETQ-D6-CANDIDATE={result['setq']['placement_candidate']}")
    for field, count in result["missing_status_fields"].items():
        print(f"D5-MISSING-{field.upper().replace('_','-')}={count}")

    if result["reasons"]:
        print("RESULT=D6-INPUT-REBASE-REQUIRED")
        for reason in result["reasons"]:
            print(f"reason={reason}")
        return 0

    print("RESULT=D6-INPUTS-RECLASSIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
