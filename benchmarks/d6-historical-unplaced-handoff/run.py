#!/usr/bin/env python3
"""#2678/#2723 — historical evidence -> current D6 placement handoff.

This remains a join gate, not a theorem source. Historical presence alone
creates no residency. SETQ is the single exception only because separate
owner-ratified D6 placement authority now exists at 001111.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "docs" / "research" / "2344-post-d4-historical-ledger.json"
FRONTIER = REPO / "benchmarks" / "d6-unknown-frontier" / "run.py"
PARENT = REPO / "benchmarks" / "d6-pure-unknown-parent-tournament" / "run.py"
FIREWALL = REPO / "benchmarks" / "d6-pure-unknown-domain-firewall" / "run.py"
NONLOCAL = REPO / "benchmarks" / "nonlocal-exit-domain" / "run.py"

OPS = ("SET", "SETQ", "PROG", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER")


def historical_rows() -> dict[str, dict[str, Any]]:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["authority"] == "historical-evidence-ledger-not-language-semantic-authority"
    rows = {
        row["operation"]: row
        for row in data["rows"]
        if row["operation"] in OPS and row["current_domain_candidate"] == "unresolved"
    }
    assert tuple(op for op in OPS if op in rows) == OPS
    assert len(rows) == 7
    assert all(row["binary_object"] == "unplaced" for row in rows.values())
    return rows


def current_evidence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    frontier_ns = runpy.run_path(str(FRONTIER))
    frontier = frontier_ns["build"]()
    assert frontier["canonical"]["occupancy_mutations"] == 0

    parent_ns = runpy.run_path(str(PARENT))
    parent = parent_ns["build"]()
    assert parent["summary"]["pure_unknown_candidates"] == 0
    assert parent["summary"]["occupancy_mutations"] == 0

    firewall_ns = runpy.run_path(str(FIREWALL))
    firewall = firewall_ns["build"]()
    assert firewall["new_candidates"] == 0
    assert firewall["occupancy_mutations"] == 0
    assert firewall["bridge_escape_hatch_control"]["real_bridge_claimed"] is False

    nonlocal_ns = runpy.run_path(str(NONLOCAL))
    d5_row, root_row, d6_rows, nonlocal_frontier, _ret_ns = nonlocal_ns["load_inputs"]()
    nonlocal_status = nonlocal_ns["validate_inputs"](
        d5_row, root_row, d6_rows, nonlocal_frontier
    )
    assert nonlocal_status["d5"]["eligible"] == "NO"
    assert nonlocal_status["d6"]["eligible"] == "UNRESOLVED"

    return frontier, parent, firewall, nonlocal_status


def normalize_parent_capability(name: str) -> str:
    if name.startswith("TRANSFORMER("):
        return "TRANSFORMER"
    return name


def build() -> dict[str, Any]:
    historical = historical_rows()
    frontier, parent, firewall, nonlocal_status = current_evidence()

    sidecar = {
        row["operation"]: row
        for row in frontier["historical_unplaced_sidecar"]
        if row["operation"] in OPS
    }
    assert set(sidecar) == set(OPS)
    assert sidecar["SETQ"]["d6_coordinate"] == "001111"
    assert sidecar["SETQ"]["d6_membership_inferred"] is True
    assert all(
        row["d6_coordinate"] is None and row["d6_membership_inferred"] is False
        for op, row in sidecar.items() if op != "SETQ"
    )

    parent_rows = {
        normalize_parent_capability(row["capability"]): row
        for row in parent["tournament_rows"]
        if normalize_parent_capability(row["capability"]) in OPS
    }
    assert set(parent_rows) == set(OPS)

    target = frontier["ratified_target"]
    assert target["coordinate"] == "001111"
    assert target["research_evidence_class"] == "RATIFIED-MANUAL-RESIDENT"
    assert target["semantic_member"] is True

    rows = []
    for op in OPS:
        h = historical[op]
        p = parent_rows[op]
        s = sidecar[op]

        domain_evidence = "NO-D6-MEMBERSHIP-THEOREM"
        placement_evidence = p["verdict"]
        note = p.get("collapse_reason") or p.get("existing_nonpure_frontier_lane") or ""

        if op == "SET":
            domain_evidence = "SHARED-LOCATION-CARRIER-WITHOUT-SEPARATE-D6-RESIDENCY"
            placement_evidence = "SET-DOES-NOT-INHERIT-001111"
            note = (
                "SET shares carrier pressure but does not inherit the owner-ratified "
                "SETQ/shared-location two-axis coordinate"
            )
        elif op == "SETQ":
            domain_evidence = "RATIFIED-CORE-D6-MEMBERSHIP"
            placement_evidence = "001111-RATIFIED-RESIDENT"
            note = (
                "residency follows #2538 OD-001 + lower-bound/falsifier evidence, "
                "not historical spelling or chronology"
            )
        elif op == "RETURN":
            domain_evidence = (
                f"D5={nonlocal_status['d5']['eligible']};"
                f"D6={nonlocal_status['d6']['eligible']}"
            )
            placement_evidence = "PARENTLESS-PROVEN-ROOT-DOMAIN-UNRESOLVED"
            note = "root theorem exists, but root != width and width != coordinate"
        elif op == "PROG":
            domain_evidence = "COMPOSITE-NOT-PRIMITIVE-D6-MEMBER"
        elif op in {"FEXPR", "FSUBR"}:
            domain_evidence = "NO-ADMITTED-SAME-BASE-PARENT-THEOREM"
        elif op == "TRANSFORMER":
            domain_evidence = "NO-EXACT-D6-GENERATOR-OR-LOWER-BOUND"

        expected_member = op == "SETQ"
        assert s["d6_membership_inferred"] is expected_member
        assert s["d6_coordinate"] == ("001111" if expected_member else None)
        assert p["pure_unknown_candidate"] is False

        rows.append(
            {
                "operation": op,
                "historical_order": h["order"],
                "historical_phase": h["phase"],
                "historical_fact": h["historical_behavior"],
                "historical_class": h["later_SENS_classification"],
                "historical_binary_object": h["binary_object"],
                "current_parent_tournament_verdict": p["verdict"],
                "domain_evidence": domain_evidence,
                "placement_evidence": placement_evidence,
                "foreign_domain_authority": "NONE",
                "d6_membership_inferred": expected_member,
                "d6_coordinate": "001111" if expected_member else None,
                "handoff_verdict": "RATIFIED-D6-RESIDENT" if expected_member else "KEEP-UNPLACED",
                "note": note,
            }
        )

    assert len(rows) == 7
    setq = next(row for row in rows if row["operation"] == "SETQ")
    assert setq["handoff_verdict"] == "RATIFIED-D6-RESIDENT"
    assert setq["d6_membership_inferred"] is True
    assert setq["d6_coordinate"] == "001111"
    assert all(
        row["handoff_verdict"] == "KEEP-UNPLACED"
        and row["d6_membership_inferred"] is False
        and row["d6_coordinate"] is None
        for row in rows if row["operation"] != "SETQ"
    )

    return {
        "schema": "d6-historical-unplaced-handoff/v1",
        "issue": 2678,
        "phase": "HISTORICAL-INGEST -> SENS-DERIVATION",
        "domain": "UNKNOWN unless independently proved Core D6",
        "rows": rows,
        "summary": {
            "historical_rows_joined": 7,
            "keep_unplaced": 6,
            "d6_promotions": 1,
            "coordinate_allocations": 1,
            "pure_unknown_candidates_from_parent_tournament": parent["summary"]["pure_unknown_candidates"],
            "foreign_authority_candidates": firewall["new_candidates"],
            "occupancy_mutations": 1,
            "result": "SETQ-RATIFIED-OTHERS-KEEP-UNPLACED",
        },
        "guards": [
            "chronology != domain law",
            "historical presence != D6 membership",
            "free capacity != placement evidence",
            "name != coordinate",
            "parentless root != width",
            "foreign domain/mechanism != Core D6 authority",
            "research overlay never mutates canonical closure",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = build()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "result.json").write_text(rendered, encoding="utf-8")
        lines = [
            "# D6 historical-unplaced handoff — #2678",
            "",
            "Historical presence is pressure only; it does not supply width or coordinate.",
            "",
            "| operation | current evidence | handoff |",
            "|---|---|---|",
        ]
        for row in result["rows"]:
            lines.append(
                f"| {row['operation']} | {row['domain_evidence']} / "
                f"{row['placement_evidence']} | **{row['handoff_verdict']}** |"
            )
        lines += [
            "",
            "Summary:",
            "- 7 historical unresolved rows joined;",
            "- 6 KEEP-UNPLACED;",
            "- SETQ -> D6:001111 RATIFIED;",
            "- 1 D6 promotion / coordinate allocation from explicit owner authority;",
            "- all other historical survivors remain unplaced.",
            "",
        ]
        (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")

    print("D6-HISTORICAL-UNPLACED-HANDOFF=PASS")
    print("historical-rows-joined=7")
    print("keep-unplaced=6")
    print("d6-promotions=1")
    print("coordinate-allocations=1")
    print("occupancy-mutations=1")
    print("SETQ-D6-001111=RATIFIED")
    print("RESULT=SETQ-RATIFIED-OTHERS-KEEP-UNPLACED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
