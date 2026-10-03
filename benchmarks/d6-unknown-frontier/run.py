#!/usr/bin/env python3
"""#2660 — partition the canonical D6 UNKNOWN frontier without allocating it.

This is research accounting only.  It joins existing evidence while preserving
the canonical D6 closure map as the sole occupancy source.

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
OWNER_READY_NONADMITTED = "OWNER-READY-NONADMITTED"


def load_closure() -> list[dict[str, Any]]:
    rows = runpy.run_path(str(CLOSURE))["build_map"]()
    assert len(rows) == 64
    assert sum(r["status"] == "generated" for r in rows) == 16
    assert sum(r["status"] == "UNKNOWN/free" for r in rows) == 48
    return rows


def load_historical_unplaced() -> list[dict[str, Any]]:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["authority"] == "historical-evidence-ledger-not-language-semantic-authority"
    result = []
    for row in data["rows"]:
        if row["current_domain_candidate"] == "unresolved":
            assert row["binary_object"] == "unplaced"
            result.append(
                {
                    "operation": row["operation"],
                    "historical_phase": row["phase"],
                    "later_sens_classification": row["later_SENS_classification"],
                    "placement_status": row["placement_status"],
                    "binary_object": row["binary_object"],
                    "d6_coordinate": None,
                    "d6_membership_inferred": False,
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

    overlay_coords = {PARENT_DUPLICATE, *middle, TARGET}
    assert overlay_coords <= set(unknown)

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
        elif coordinate == TARGET:
            evidence_class = OWNER_READY_NONADMITTED
            refs = ["#2511", "#2518", "#2537", "#2541", "#2634", "#2538"]
            note = "local D6 placement/readiness evidence complete; canonical admission remains false"
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
        OWNER_READY_NONADMITTED: 1,
    }

    historical = load_historical_unplaced()
    historical_ops = {r["operation"] for r in historical}
    assert {"SET", "SETQ", "PROG", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"} <= historical_ops
    assert all(r["d6_coordinate"] is None for r in historical)
    assert all(r["d6_membership_inferred"] is False for r in historical)

    result = {
        "schema": "d6-unknown-frontier/v1",
        "domain": "Core D6",
        "canonical": {
            "capacity": 64,
            "generated_members": 16,
            "unknown_free": 48,
            "occupancy_mutations": 0,
        },
        "frontier_counts": counts,
        "frontier": frontier,
        "historical_unplaced_sidecar": historical,
        "guards": [
            "research overlay never mutates canonical closure",
            "historical presence never implies D6 width",
            "unresolved width never implies a free D6 coordinate",
            "001111 remains nonadmitted until explicit owner decision",
            "same bits in another domain confer no Core D6 law",
        ],
        "handoff": {
            PURE_UNKNOWN: "needs a new exact same-base law/theorem before any placement search",
            PARENT_DUPLICATE_NOT_EARNED: "needs an independently observable delta; printed width is insufficient",
            OVERLAY_CANDIDATE_NONADMITTED: "needs independent resident necessity plus coordinate-orientation evidence",
            OWNER_READY_NONADMITTED: "research complete for current proposal; decision authority is external to this gate",
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
    print("canonical=16-generated+48-unknown")
    for key, count in sorted(result["frontier_counts"].items()):
        print(f"{key}={count}")
    print(f"historical-unplaced={len(result['historical_unplaced_sidecar'])}")
    print("occupancy-mutations=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
