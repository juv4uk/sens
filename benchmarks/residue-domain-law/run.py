#!/usr/bin/env python3
"""#2662 — residue-root exact-domain admission tournament.

Research-only. No coordinate is assigned.

Hard invariant:
    semantic root != exact width != coordinate
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ROOT_MIN = ROOT / "benchmarks" / "post-d4-root-min-closeout" / "run.py"
D5_GRAPH = ROOT / "benchmarks" / "d5-structural-discovery" / "factor-graph.json"
D6_MAP = ROOT / "benchmarks" / "d6-closure-map" / "run.py"
HISTORY = ROOT / "docs" / "research" / "2344-post-d4-historical-ledger.json"


def root_row() -> dict[str, Any]:
    rows = runpy.run_path(str(ROOT_MIN))["ROWS"]
    roots = [row for row in rows if row["root_status"] == "PROVEN-ROOT"]
    assert len(roots) == 1, roots
    row = roots[0]
    assert row["factor"] == "non-local-exit"
    assert row["width"] == "UNKNOWN"
    assert row["coordinate"] == "UNPLACED"
    return row


def d5_state() -> dict[str, Any]:
    graph = json.loads(D5_GRAPH.read_text(encoding="utf-8"))
    summary = graph["summary"]
    assert summary["d5_selector_generated"] == 8
    assert summary["d5_unknown_free"] == 24
    assert summary["placement_search_authorized"] is False
    return {
        "width": 5,
        "ratified_domain": True,
        "generated": 8,
        "unknown_free": 24,
        "root_membership_proved": False,
    }


def d6_state() -> dict[str, Any]:
    rows = runpy.run_path(str(D6_MAP))["build_map"]()
    generated = sum(row["status"] == "generated" for row in rows)
    ratified = [row for row in rows if row["status"] == "ratified-resident"]
    unknown = sum(row["status"] == "UNKNOWN/free" for row in rows)
    assert len(rows) == 64
    assert generated == 16
    assert len(ratified) == 1 and ratified[0]["coordinate"] == "001111"
    assert ratified[0]["placement_ref"] == "#2538-OD-001"
    assert unknown == 47
    assert [
        row["coordinate"] for row in rows if row["placement_ref"]
    ] == ["001111"]
    return {
        "width": 6,
        "ratified_domain": True,
        "generated": generated,
        "ratified_manual_residents": 1,
        "unknown_free": unknown,
        "root_membership_proved": False,
        "unrelated_manual_resident": "001111",
    }


def historical_control() -> dict[str, Any]:
    history = json.loads(HISTORY.read_text(encoding="utf-8"))
    rows = {row["operation"]: row for row in history["rows"]}
    ret = rows["RETURN"]
    prog = rows["PROG"]

    assert ret["phase"] == "D"
    assert ret["historical_presence"] == "yes"
    assert ret["current_domain_candidate"] == "unresolved"
    assert ret["binary_object"] == "unplaced"
    assert ret["placement_status"].startswith("unplaced")
    assert prog["binary_object"] == "unplaced"

    return {
        "return_phase": ret["phase"],
        "return_lineage": ret["first_attested_lineage"],
        "current_domain_candidate": ret["current_domain_candidate"],
        "binary_object": ret["binary_object"],
        "placement_status": ret["placement_status"],
    }


def model_rows(
    d5: dict[str, Any],
    d6: dict[str, Any],
    history: dict[str, Any],
) -> list[dict[str, Any]]:
    free_domains = [
        domain["width"]
        for domain in (d5, d6)
        if domain["ratified_domain"] and domain["unknown_free"] > 0
    ]
    assert free_domains == [5, 6]

    return [
        {
            "model": "R0-smallest-free-domain",
            "domain_selection_rule": "choose smallest ratified domain with unused capacity",
            "machine_attack": (
                "D5 and D6 both retain UNKNOWN/free coordinates while the root "
                "ledger keeps width UNKNOWN; the unrelated ratified D6:001111 resident "
                "does not supply a membership rule for this root"
            ),
            "minimum_width_theorem": False,
            "coordinate_assigned": False,
            "verdict": "FALSIFIED",
            "reason": "free capacity is not semantic evidence",
        },
        {
            "model": "R1-historical-stratum-domain",
            "domain_selection_rule": "map historical phase/era to exact binary domain",
            "machine_attack": (
                "the canonical historical row itself records "
                "current_domain_candidate=unresolved and binary_object=unplaced"
            ),
            "historical_phase": history["return_phase"],
            "minimum_width_theorem": False,
            "coordinate_assigned": False,
            "verdict": "FALSIFIED",
            "reason": "chronology records observation order, not a binary-domain law",
        },
        {
            "model": "R2-semantic-fact-lower-bound",
            "domain_selection_rule": (
                "derive minimum exact domain from irreducible observations "
                "under an explicit encoding/lower-bound theorem"
            ),
            "machine_attack": (
                "no minimum-width theorem is yet admitted; factor count or axis "
                "count must not be reinterpreted as bit width"
            ),
            "minimum_width_theorem": False,
            "coordinate_assigned": False,
            "verdict": "ACTIVE-CANDIDATE",
            "reason": "admissible route, proof still missing",
        },
        {
            "model": "R3-independent-root-domain",
            "domain_selection_rule": (
                "place parentless roots in a separately declared exact root domain"
            ),
            "machine_attack": (
                "requires explicit carrier/admissibility law and relation to "
                "Core D5/D6; otherwise it merely relocates an arbitrary table"
            ),
            "minimum_width_theorem": False,
            "coordinate_assigned": False,
            "verdict": "UNRESOLVED",
            "reason": "root-domain law not yet supplied",
        },
        {
            "model": "R4-proof-addressed-construction",
            "domain_selection_rule": (
                "derive canonical proof/certificate identity then project to storage"
            ),
            "machine_attack": (
                "#2490 still requires binary number + exact domain + proved law; "
                "a proof address can be a construction/projection certificate but "
                "cannot erase exact-domain authority"
            ),
            "minimum_width_theorem": False,
            "coordinate_assigned": False,
            "verdict": "PROJECTION-ONLY-UNLESS-EXACT-DOMAIN",
            "reason": "compatible only if an exact semantic domain is still proved",
        },
    ]


def build_result() -> dict[str, Any]:
    root = root_row()
    d5 = d5_state()
    d6 = d6_state()
    history = historical_control()
    models = model_rows(d5, d6, history)

    by_model = {row["model"]: row for row in models}
    assert len(by_model) == 5
    assert all(row["coordinate_assigned"] is False for row in models)
    assert by_model["R0-smallest-free-domain"]["verdict"] == "FALSIFIED"
    assert by_model["R1-historical-stratum-domain"]["verdict"] == "FALSIFIED"

    result = {
        "schema": "residue-domain-law/v1",
        "phase": "SENS-DERIVATION",
        "authority": "research-only-no-placement",
        "positive_control": {
            "factor": root["factor"],
            "root_status": root["root_status"],
            "width": root["width"],
            "coordinate": root["coordinate"],
            "evidence": root["evidence"],
        },
        "domain_controls": {"D5": d5, "D6": d6},
        "historical_control": history,
        "models": models,
        "result": {
            "residue_domain_law": "UNRESOLVED",
            "nonlocal_d5_eligible": "NOT-ESTABLISHED",
            "nonlocal_d6_eligible": "NOT-ESTABLISHED",
            "minimum_exact_domain": "UNRESOLVED",
            "coordinate": "UNPLACED",
            "new_residents": 0,
            "falsified_models": [
                "R0-smallest-free-domain",
                "R1-historical-stratum-domain",
            ],
            "active_scientific_routes": [
                "R2-semantic-fact-lower-bound",
                "R3-independent-root-domain",
            ],
            "proof_address_role": "projection-only-until-exact-domain-proved",
        },
        "guards": [
            "root != width",
            "width != coordinate",
            "free coordinate != semantic membership",
            "chronology != exact-domain law",
            "axis count != bit width",
            "ratified domain width != automatic occupancy",
        ],
    }

    assert result["result"]["coordinate"] == "UNPLACED"
    assert result["result"]["new_residents"] == 0
    return result


def report(result: dict[str, Any]) -> str:
    lines = [
        "# Residue-domain law tournament — #2662",
        "",
        "Positive control:",
        "    non-local-exit = PROVEN-ROOT",
        "    width          = UNKNOWN",
        "    coordinate     = UNPLACED",
        "",
        "Domain controls:",
        f"    D5 generated={result['domain_controls']['D5']['generated']} "
        f"UNKNOWN/free={result['domain_controls']['D5']['unknown_free']}",
        f"    D6 generated={result['domain_controls']['D6']['generated']} "
        f"UNKNOWN/free={result['domain_controls']['D6']['unknown_free']}",
        "",
        "| model | verdict |",
        "|---|---|",
    ]
    for row in result["models"]:
        lines.append(f"| {row['model']} | {row['verdict']} |")

    lines += [
        "",
        "Machine result:",
        "    R0-smallest-free-domain=FALSIFIED",
        "    R1-historical-stratum-domain=FALSIFIED",
        "    R2-semantic-fact-lower-bound=ACTIVE-CANDIDATE",
        "    R3-independent-root-domain=UNRESOLVED",
        "    R4-proof-addressed=PROJECTION-ONLY-UNLESS-EXACT-DOMAIN",
        "    RESIDUE-DOMAIN-LAW=UNRESOLVED",
        "    NONLOCAL-D5=NOT-ESTABLISHED",
        "    NONLOCAL-D6=NOT-ESTABLISHED",
        "    COORDINATE=UNPLACED",
        "    NEW-RESIDENTS=0",
        "",
        "Negative progress is decisive here: neither capacity nor chronology can",
        "select an exact domain for a parentless root.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    result = build_result()
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "report.md").write_text(report(result), encoding="utf-8")

    print("RESIDUE-DOMAIN-LAW=PASS")
    print("R0-SMALLEST-FREE=FALSIFIED")
    print("R1-HISTORICAL-STRATUM=FALSIFIED")
    print("R2-SEMANTIC-LOWER-BOUND=ACTIVE-CANDIDATE")
    print("R3-INDEPENDENT-ROOT-DOMAIN=UNRESOLVED")
    print("R4-PROOF-ADDRESSED=PROJECTION-ONLY")
    print("NONLOCAL-D5=NOT-ESTABLISHED")
    print("NONLOCAL-D6=NOT-ESTABLISHED")
    print("COORDINATE=UNPLACED")
    print("NEW-RESIDENTS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
