#!/usr/bin/env python3
"""#2678 — historical-unplaced -> current D6 evidence handoff.

History is candidate pressure, never width or coordinate authority.

This gate joins:
- the historical post-D4 ledger (#2344);
- the canonical D6 frontier (#2660/#2661);
- the admitted-parent tournament (#2677/#2685);
- anti-numerology (#2664 lane C / #2676);
- domain firewall (#2679/#2683).

It must not allocate or mutate any D6 coordinate.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
HISTORICAL = REPO / "docs" / "research" / "2344-post-d4-historical-ledger.json"
FRONTIER = REPO / "benchmarks" / "d6-unknown-frontier" / "run.py"
TOURNAMENT = REPO / "benchmarks" / "d6-pure-unknown-parent-tournament" / "run.py"
ANTINUM = REPO / "benchmarks" / "d6-pure-unknown-antinumerology" / "run.py"
FIREWALL = REPO / "benchmarks" / "d6-pure-unknown-domain-firewall" / "run.py"

EXPECTED = ("SET", "SETQ", "PROG", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER")

TOURNAMENT_NAME = {
    "SET": "SET",
    "SETQ": "SETQ",
    "PROG": "PROG",
    "RETURN": "RETURN",
    "FEXPR": "FEXPR",
    "FSUBR": "FSUBR",
    "TRANSFORMER": "TRANSFORMER(Hart-1963)",
}

HANDOFF_CLASS = {
    "SET": "SHARED-LOCATION-CARRIER-PREMISE",
    "SETQ": "SHARED-LOCATION-CARRIER-PREMISE",
    "PROG": "COMPOSITE",
    "RETURN": "PROVEN-ROOT-WIDTH-UNKNOWN",
    "FEXPR": "TWO-AXIS-NO-SAME-BASE-THEOREM",
    "FSUBR": "TWO-AXIS-NO-SAME-BASE-THEOREM",
    "TRANSFORMER": "PROTOCOL/POLICY-CARRIER-STRUCTURE",
}


def _build(path: Path) -> dict[str, Any]:
    ns = runpy.run_path(str(path))
    return ns["build"]()


def _historical_rows() -> dict[str, dict[str, Any]]:
    data = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    assert data["authority"] == "historical-evidence-ledger-not-language-semantic-authority"
    rows = {
        row["operation"]: row
        for row in data["rows"]
        if row["current_domain_candidate"] == "unresolved"
    }
    assert tuple(rows) == EXPECTED, tuple(rows)
    assert all(row["binary_object"] == "unplaced" for row in rows.values())
    return rows


def build() -> dict[str, Any]:
    historical = _historical_rows()
    frontier = _build(FRONTIER)
    tournament = _build(TOURNAMENT)
    antinum = _build(ANTINUM)
    firewall = _build(FIREWALL)

    assert frontier["frontier_counts"]["PURE-UNKNOWN"] == 44
    assert frontier["canonical"]["occupancy_mutations"] == 0
    assert tournament["summary"]["pure_unknown_candidates"] == 0
    assert tournament["summary"]["occupancy_mutations"] == 0
    assert antinum["result"] == "NO-CANDIDATE-FROM-COORDINATE-ONLY"
    assert firewall["result"] == "NO-FOREIGN-AUTHORITY-FOR-D6-PURE-UNKNOWN"

    tournament_rows = {
        row["capability"]: row for row in tournament["tournament_rows"]
    }

    frontier_hist = {
        row["operation"]: row for row in frontier["historical_unplaced_sidecar"]
    }
    assert set(frontier_hist) == set(EXPECTED)

    rows: list[dict[str, Any]] = []
    for operation in EXPECTED:
        hist = historical[operation]
        tournament_key = TOURNAMENT_NAME[operation]
        trow = tournament_rows[tournament_key]
        frow = frontier_hist[operation]

        assert frow["binary_object"] == "unplaced"
        assert frow["d6_coordinate"] is None
        assert frow["d6_membership_inferred"] is False
        assert trow["pure_unknown_candidate"] is False

        related_nonpure_overlay = trow.get("existing_frontier_lane")
        verdict = "KEEP-UNPLACED"
        if related_nonpure_overlay:
            verdict = "KEEP-HISTORICAL-NAME-UNPLACED; HANDOFF-SEPARATE-NONPURE-LANE"

        rows.append(
            {
                "operation": operation,
                "historical_phase": hist["phase"],
                "historical_fact": hist["historical_behavior"],
                "historical_classification": hist["later_SENS_classification"],
                "current_semantic_handoff": HANDOFF_CLASS[operation],
                "domain_evidence": (
                    "UNKNOWN unless independent Core D6 theorem exists"
                ),
                "placement_evidence": trow["verdict"],
                "same_base_parent": trow["same_base"],
                "composition_law": trow["composition_law"],
                "lower_bound": trow["lower_bound"],
                "related_nonpure_overlay": related_nonpure_overlay,
                "binary_object": "UNPLACED",
                "d6_coordinate": None,
                "d6_membership_inferred": False,
                "pure_unknown_candidate": False,
                "verdict": verdict,
                "historical_evidence_issue": hist["issue"],
                "historical_evidence_sha": hist["evidence_sha"],
            }
        )

    assert len(rows) == 7
    assert all(row["binary_object"] == "UNPLACED" for row in rows)
    assert all(row["d6_coordinate"] is None for row in rows)
    assert all(row["d6_membership_inferred"] is False for row in rows)
    assert all(row["pure_unknown_candidate"] is False for row in rows)
    assert not any(row["verdict"] == "PLACE-IN-D6" for row in rows)

    result = {
        "schema": "d6-historical-unplaced-handoff/v1",
        "issue": 2678,
        "phase": "HISTORICAL-INGEST -> SENS-DERIVATION",
        "domain": "UNKNOWN unless independently proved Core D6",
        "binary_object": "UNPLACED historical rows",
        "law": (
            "historical presence/chronology/name creates candidate pressure only; "
            "it never supplies width or coordinate"
        ),
        "inputs": {
            "historical_rows": len(rows),
            "pure_unknown_coordinates": 44,
            "parent_tournament_candidates": 0,
            "anti_numerology": "NO-CANDIDATE-FROM-COORDINATE-ONLY",
            "domain_firewall": "NO-FOREIGN-AUTHORITY-FOR-D6-PURE-UNKNOWN",
        },
        "rows": rows,
        "summary": {
            "historical_unplaced_tested": len(rows),
            "keep_unplaced": len(rows),
            "d6_membership_inferred": 0,
            "pure_unknown_candidates": 0,
            "occupancy_mutations": 0,
            "result": "KEEP-ALL-HISTORICAL-ROWS-UNPLACED",
        },
        "guards": [
            "history != width",
            "history != coordinate",
            "name != identity",
            "free capacity != semantic evidence",
            "coordinate proximity != semantic evidence",
            "foreign domain/mechanism != Core D6 authority",
            "known non-PURE D6 pressure does not place a historical spelling",
            "parentless root != D6 until residue-domain admission law proves it",
        ],
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = build()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")

    print("D6-HISTORICAL-UNPLACED-HANDOFF=PASS")
    print("historical-unplaced-tested=7")
    print("keep-unplaced=7")
    print("d6-membership-inferred=0")
    print("pure-unknown-candidates=0")
    print("occupancy-mutations=0")
    print("RESULT=KEEP-ALL-HISTORICAL-ROWS-UNPLACED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
