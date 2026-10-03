#!/usr/bin/env python3
"""#2660/#2723 — partition the canonical D6 UNKNOWN frontier after 001111 ratification.

This is research accounting only. The canonical D6 closure map remains the
sole occupancy source. 001111 is no longer part of the UNKNOWN frontier.

Key invariant:
    evidence-about-an-UNKNOWN != semantic-membership != residency
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
CLOSURE = REPO / "benchmarks/d6-closure-map/run.py"
MIDDLE = REPO / "scripts/research-2624-d6-middle-corners.py"
READINESS = REPO / "scripts/research-2619-d6-residency-readiness.py"
LEDGER = REPO / "docs/research/2344-post-d4-historical-ledger.json"

PARENT_DUPLICATE = "001100"
MIDDLE_EXPECTED = {"001101", "001110"}
TARGET = "001111"

PURE_UNKNOWN = "PURE-UNKNOWN"
PARENT_DUPLICATE_NOT_EARNED = "PARENT-DUPLICATE-NOT-EARNED"
OVERLAY_CANDIDATE_NONADMITTED = "OVERLAY-CANDIDATE-NONADMITTED"
RATIFIED_TARGET = "RATIFIED-MANUAL-RESIDENT"


def load_closure() -> list[dict[str, Any]]:
    rows = runpy.run_path(str(CLOSURE))["build_map"]()
    assert len(rows) == 64
    assert sum(r["status"] == "generated" for r in rows) == 16
    assert sum(r["status"] == "ratified-resident" for r in rows) == 1
    assert sum(r["status"] == "UNKNOWN/free" for r in rows) == 47
    target = next(r for r in rows if r["coordinate"] == TARGET)
    assert target["status"] == "ratified-resident"
    assert target["semantic_member_of_ratified_domain"] is True
    return rows


def load_historical_unplaced() -> list[dict[str, Any]]:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["authority"] == "historical-evidence-ledger-not-language-semantic-authority"
    result = []
    for row in data["rows"]:
        if row["current_domain_candidate"] == "unresolved":
            assert row["binary_object"] == "unplaced"
            is_ratified_setq = row["operation"] == "SETQ"
            result.append(
                {
                    "operation": row["operation"],
                    "historical_phase": row["phase"],
                    "later_sens_classification": row["later_SENS_classification"],
                    "placement_status": row["placement_status"],
                    "binary_object": row["binary_object"],
                    "d6_coordinate": TARGET if is_ratified_setq else None,
                    "d6_membership_inferred": is_ratified_setq,
                    "d6_placement_authority": "#2538-OD-001" if is_ratified_setq else None,
                    "evidence_issue": row["issue"],
                }
            )
    return result


def build() -> dict[str, Any]:
    rows = load_closure()
    unknown = {r["coordinate"]: r for r in rows if r["status"] == "UNKNOWN/free"}

    middle_ns = runpy.run_path(str(MIDDLE))
    middle = set(middle_ns["MIDDLE"])
    assert middle == MIDDLE_EXPECTED

    readiness_ns = runpy.run_path(str(READINESS))
    assert readiness_ns["TARGET"] == TARGET

    overlay_coords = {PARENT_DUPLICATE, *middle}
    assert overlay_coords <= set(unknown)
    assert TARGET not in unknown
    ratified_target = next(r for r in rows if r["coordinate"] == TARGET)
    assert ratified_target["status"] == "ratified-resident"
    assert ratified_target["semantic_member_of_ratified_domain"] is True

    frontier = []
    for coordinate in sorted(unknown):
        if coordinate == PARENT_DUPLICATE:
            evidence_class = PARENT_DUPLICATE_NOT_EARNED
            refs = ["#2506"]
            note = "00 product corner duplicates the D4 parent; printed D6 width does not earn a resident"
        elif coordinate in middle:
            evidence_class = OVERLAY_CANDIDATE_NONADMITTED
            refs = ["#2506", "#2624"]
            note = "proved one-axis semantic product corner; exact orientation/residency is unproven"
        else:
            evidence_class = PURE_UNKNOWN
            refs = []
            note = "no merged D6-local overlay is admitted by this accounting gate"

        canonical = unknown[coordinate]
        assert canonical["semantic_member_of_ratified_domain"] is False
        assert canonical["placement_ref"] == ""
        frontier.append(
            {
                "coordinate": coordinate,
                "canonical_status": canonical["status"],
                "canonical_semantic_member": False,
                "canonical_placement_ref": "",
                "research_evidence_class": evidence_class,
                "research_refs": refs,
                "note": note,
            }
        )

    counts: dict[str, int] = {}
    for row in frontier:
        key = row["research_evidence_class"]
        counts[key] = counts.get(key, 0) + 1

    assert counts == {
        PURE_UNKNOWN: 44,
        PARENT_DUPLICATE_NOT_EARNED: 1,
        OVERLAY_CANDIDATE_NONADMITTED: 2,
    }

    historical = load_historical_unplaced()
    historical_ops = {r["operation"] for r in historical}
    assert {"SET", "SETQ", "PROG", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"} <= historical_ops
    placed_hist = [r for r in historical if r["d6_membership_inferred"]]
    assert len(placed_hist) == 1 and placed_hist[0]["operation"] == "SETQ"
    assert placed_hist[0]["d6_coordinate"] == TARGET
    assert all(
        r["d6_coordinate"] is None and r["d6_membership_inferred"] is False
        for r in historical if r["operation"] != "SETQ"
    )

    result = {
        "schema": "d6-unknown-frontier/v1",
        "domain": "Core D6",
        "canonical": {
            "capacity": 64,
            "generated_members": 16,
            "ratified_manual_residents": 1,
            "unknown_free": 47,
            "occupancy_mutations": 0,
        },
        "ratified_target": {
            "coordinate": TARGET,
            "status": ratified_target["status"],
            "semantic_member": ratified_target["semantic_member_of_ratified_domain"],
            "placement_ref": ratified_target["placement_ref"],
            "research_evidence_class": RATIFIED_TARGET,
        },
        "frontier_counts": counts,
        "frontier": frontier,
        "historical_unplaced_sidecar": historical,
        "guards": [
            "research overlay never mutates canonical closure",
            "historical presence never implies D6 width",
            "unresolved width never implies a free D6 coordinate",
            "001111 is admitted only by explicit owner decision #2538 OD-001",
            "same bits in another domain confer no Core D6 law",
        ],
        "handoff": {
            PURE_UNKNOWN: "needs a new exact same-base law/theorem before any placement search",
            PARENT_DUPLICATE_NOT_EARNED: "needs an independently observable delta; printed width is insufficient",
            OVERLAY_CANDIDATE_NONADMITTED: "needs independent resident necessity plus coordinate-orientation evidence",
            RATIFIED_TARGET: "already removed from UNKNOWN frontier by owner-ratified canonical occupancy",
            "historical-unplaced": "continue structural discovery/root/width proofs; never choose D6 by name or free capacity",
        },
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

    print("D6-UNKNOWN-FRONTIER=PASS")
    print("canonical=16-generated+1-ratified+47-unknown")
    for key, count in sorted(result["frontier_counts"].items()):
        print(f"{key}={count}")
    print(f"historical-unplaced={len(result['historical_unplaced_sidecar'])}")
    print("occupancy-mutations=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
