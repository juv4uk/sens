#!/usr/bin/env python3
"""#2703 — validate post-D4 historical semantic placement.

This is a SENS-DERIVATION aggregation gate. It places historical observations
under semantic owners/families without assigning new resident coordinates.
"""

from __future__ import annotations

import argparse
import json
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORY = ROOT / "docs/research/2344-post-d4-historical-ledger.json"
PLACEMENT = ROOT / "benchmarks/post-d4-semantic-placement/placement.json"
D5 = ROOT / "benchmarks/d5-sens-derivation-closeout/factor-eligibility.json"
ROOT_MIN = ROOT / "benchmarks/post-d4-root-min-closeout/run.py"

NO_COORD_KINDS = {"DERIVED-UNDER-OWNER", "HISTORICAL-ADAPTER", "COMPOSITE"}
UNPLACED_KINDS = {
    "CARRIER-FAMILY",
    "POLICY-OVER-CARRIER",
    "PROVEN-ROOT-UNPLACED",
}

EXPECTED_ROOT_FACTORS = {
    "shared-location-update": "CARRIER-PREMISE",
    "non-local-exit": "PROVEN-ROOT",
    "raw-form-input": "CARRIER-PREMISE",
    "explicit-caller-env": "CARRIER-PREMISE",
    "returned-form-protocol": "POLICY-OVER-ROOT",
    "expansion-timing": "POLICY-OVER-ROOT",
    "invocation-packaging": "CARRIER-PREMISE",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    history = load(HISTORY)
    placement = load(PLACEMENT)
    d5 = load(D5)

    hist_rows = history["rows"]
    rows = placement["rows"]

    assert len(hist_rows) == 19
    assert len(rows) == 19
    assert all(r["phase_status"] == "complete" for r in hist_rows)

    hist_by_op = {r["operation"]: r for r in hist_rows}
    placed_by_op = {r["operation"]: r for r in rows}
    assert len(hist_by_op) == 19
    assert len(placed_by_op) == 19
    assert set(hist_by_op) == set(placed_by_op)

    for op, row in placed_by_op.items():
        source = hist_by_op[op]
        assert row["historical_order"] == source["order"], op
        assert row["historical_classification"] == source["later_SENS_classification"], op

        kind = row["placement_kind"]
        if kind in NO_COORD_KINDS:
            assert row["resident_required"].startswith("NO"), op
            assert row["exact_domain"] == "NONE", op
            assert row["coordinate"] == "NONE", op
        elif kind in UNPLACED_KINDS:
            assert row["exact_domain"] == "UNKNOWN", op
            assert row["coordinate"] == "UNPLACED", op
        else:
            raise AssertionError(f"{op}: unknown placement kind {kind}")

    # Historical derived/mechanism rows must never become residents by placement.
    for op in [
        "LABEL", "FUNCTION", "FUNARG", "EVALQUOTE", "APPEND", "PAIR",
        "PAIRLIS", "ASSOC", "SUBST", "SUBLIS", "MAPLIST", "GO",
    ]:
        row = placed_by_op[op]
        assert row["coordinate"] == "NONE", op
        assert row["resident_required"] == "NO", op

    # Strong negative placements from the completed derivation work.
    assert "BIND" not in placed_by_op["PAIRLIS"]["primary_owner"]
    assert "LOOKUP" not in placed_by_op["ASSOC"]["primary_owner"]
    assert placed_by_op["RETURN"]["placement_kind"] == "PROVEN-ROOT-UNPLACED"
    assert placed_by_op["RETURN"]["coordinate"] == "UNPLACED"
    assert placed_by_op["TRANSFORMER"]["coordinate"] == "UNPLACED"

    # #2616: no surviving factor currently earns a non-selector D5 child.
    invariant = d5["map_invariant"]
    assert invariant == {
        "capacity": 32,
        "selector_generated": 8,
        "unknown_free": 24,
        "manual_nonselector_residents": 0,
        "source": "#2510/#2414",
    }
    assert not any(r["d5_eligible"] == "YES" for r in d5["factors"])

    # #2617: structural factors have already minimized to one root + carrier/policy.
    namespace = runpy.run_path(str(ROOT_MIN))
    root_rows = {r["factor"]: r for r in namespace["ROWS"]}
    assert {k: root_rows[k]["root_status"] for k in EXPECTED_ROOT_FACTORS} == EXPECTED_ROOT_FACTORS

    # SETQ candidate remains a candidate only.
    setq = placed_by_op["SETQ"]
    assert setq["coordinate"] == "UNPLACED"
    assert setq["candidate_coordinate"].startswith("D6:001111")
    assert "owner-ready only" in setq["candidate_coordinate"]

    counts = Counter(r["placement_kind"] for r in rows)
    summary = {
        "schema": "post-d4-semantic-placement-validation/v1",
        "historical_rows": len(rows),
        "placement_kind_counts": dict(sorted(counts.items())),
        "new_d5_residents": 0,
        "d5_selector_generated": 8,
        "d5_unknown_free": 24,
        "proven_root_unplaced": ["RETURN"],
        "candidate_only_not_ratified": ["SETQ:D6:001111"],
        "status": "PASS",
    }

    print("POST-D4-SEMANTIC-PLACEMENT=PASS")
    print(f"HISTORICAL-ROWS={len(rows)}")
    print("NEW-D5-RESIDENTS=0")
    print("D5=8-generated+24-UNKNOWN")
    print("RETURN=PROVEN-ROOT-UNPLACED")
    print("SETQ-D6-001111=CANDIDATE-ONLY")
    for key, value in sorted(counts.items()):
        print(f"{key}={value}")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "validation.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
