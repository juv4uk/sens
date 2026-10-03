#!/usr/bin/env python3
"""#2583 — first post-ingest D5 structural-discovery factor graph.

Consumes the completed 19-row historical ledger and emits a conservative
capability hypergraph.

Important:
- factor candidate != semantic root;
- historical row != resident;
- no D5 coordinate may be proposed here;
- existing D1-D4 derivations are charged as zero post-D4 residue.

The seven post-D4 factor candidates in the current slice are observations/axes
already established by earlier bounded work:
  shared-location-update
  non-local-exit
  raw-form-input
  explicit-caller-env
  returned-form-protocol
  expansion-timing
  invocation-packaging

None is promoted to a proved independent root in this slice.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "research" / "2344-post-d4-historical-ledger.json"
OUT = ROOT / "benchmarks" / "d5-structural-discovery" / "factor-graph.json"

EXPECTED_OPERATIONS = {
    "LABEL", "FUNCTION", "FUNARG", "EVALQUOTE",
    "APPEND", "PAIR", "PAIRLIS", "ASSOC", "SUBST", "SUBLIS", "MAPLIST",
    "SET", "SETQ", "PROG", "GO", "RETURN",
    "FEXPR", "FSUBR", "TRANSFORMER",
}

FACTOR_DEFS: dict[str, dict[str, Any]] = {
    "existing-core-structural": {
        "semantic_observable": "behavior already reconstructed by existing D1-D4 semantics",
        "positive_rows": {
            "LABEL", "EVALQUOTE", "APPEND", "PAIR", "PAIRLIS",
            "ASSOC", "SUBST", "SUBLIS", "MAPLIST", "GO",
        },
        "negative_controls": {"SET", "RETURN", "FEXPR", "TRANSFORMER"},
        "dependency_on_other_factor": [],
        "current_status": "derived-existing-core",
        "evidence": ["#2238", "#2279", "#2300", "#2296", "#2386", "#2387", "#2480"],
        "falsifier": "a listed positive row exhibits a bounded observation not reconstructible from admitted D1-D4 semantics",
    },
    "historical-representation-mechanism": {
        "semantic_observable": "historical representation wrapper with no current independent semantic residue established",
        "positive_rows": {"FUNCTION", "FUNARG"},
        "negative_controls": {"SET", "RETURN"},
        "dependency_on_other_factor": ["existing-core-structural"],
        "current_status": "historical-mechanism-only",
        "evidence": ["#2259"],
        "falsifier": "FUNCTION/FUNARG yields an observable not reproduced by current closure/application semantics",
    },
    "shared-location-update": {
        "semantic_observable": "update nearest existing shared binding/location with fail-on-miss semantics",
        "positive_rows": {"SET", "SETQ"},
        "negative_controls": {"GO", "RETURN", "FEXPR"},
        "dependency_on_other_factor": [],
        "current_status": "bounded-independent-observable",
        "evidence": ["#2441", "#2442", "#2480", "#2492", "#2589", "f48956fc94e3eb5c7534dbfe0cbcb46c393a74c5"],
        "falsifier": "remove shared-location state while preserving all bounded SET/SETQ observations locally under admitted semantics",
    },
    "non-local-exit": {
        "semantic_observable": "exit the most-recent active PROG across an ordinary call boundary",
        "positive_rows": {"RETURN", "PROG"},
        "negative_controls": {"GO", "SETQ"},
        "dependency_on_other_factor": [],
        "current_status": "bounded-independent-external-root-theorem",
        "evidence": ["#2439", "#2480", "#2488", "#2504", "fcf3a410914882e52960647e49760d0152faa11d"],
        "falsifier": "local admitted control reconstructs RETURN without whole-call-graph CPS or an equivalent extra control channel",
    },
    "raw-form-input": {
        "semantic_observable": "receive unevaluated operand/form structure as input",
        "positive_rows": {"FEXPR", "FSUBR", "TRANSFORMER"},
        "negative_controls": {"EVALQUOTE", "FUNCTION"},
        "dependency_on_other_factor": [],
        "current_status": "protocol-axis-candidate",
        "evidence": ["#2522", "#2530", "#2557"],
        "falsifier": "raw-call observations are reproduced without access to raw form structure",
    },
    "explicit-caller-env": {
        "semantic_observable": "receive caller environment as an explicit semantic input",
        "positive_rows": {"FEXPR", "FSUBR"},
        "negative_controls": {"TRANSFORMER", "EVALQUOTE"},
        "dependency_on_other_factor": ["raw-form-input"],
        "current_status": "protocol-axis-candidate",
        "evidence": ["#2522", "#2530"],
        "falsifier": "caller-env observations are reconstructed from raw operands alone without an additional semantic input",
    },
    "returned-form-protocol": {
        "semantic_observable": "transformer result is a replacement/executable form rather than a direct value",
        "positive_rows": {"TRANSFORMER"},
        "negative_controls": {"FEXPR", "FSUBR"},
        "dependency_on_other_factor": ["raw-form-input"],
        "current_status": "protocol-axis-candidate",
        "evidence": ["#2557", "#2568"],
        "falsifier": "direct-value and returned-form behavior are observationally interchangeable in the bounded protocol corpus",
    },
    "expansion-timing": {
        "semantic_observable": "definition-time expansion differs observably from evaluation-time expansion",
        "positive_rows": {"TRANSFORMER"},
        "negative_controls": {"FEXPR", "FSUBR"},
        "dependency_on_other_factor": ["returned-form-protocol"],
        "current_status": "protocol-axis-candidate",
        "evidence": ["#2568", "#2569", "#2579"],
        "falsifier": "macro redefinition/order cannot distinguish definition-time from evaluation-time expansion",
    },
    "invocation-packaging": {
        "semantic_observable": "whole invocation form exposes call head while operand-only input does not",
        "positive_rows": {"TRANSFORMER"},
        "negative_controls": {"FEXPR", "FSUBR", "EVALQUOTE"},
        "dependency_on_other_factor": [],
        "current_status": "protocol-axis-candidate",
        "evidence": ["#2580", "#2588", "3d409736b994221561b413c42c837a428d242358"],
        "falsifier": "two aliases of one transformer with identical operands remain distinguishable without an explicit head/input channel",
    },
}

POST_D4_CANDIDATES = {
    "shared-location-update",
    "non-local-exit",
    "raw-form-input",
    "explicit-caller-env",
    "returned-form-protocol",
    "expansion-timing",
    "invocation-packaging",
}


def load_ledger() -> dict[str, Any]:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = data["rows"]
    ops = {row["operation"] for row in rows}
    assert ops == EXPECTED_OPERATIONS
    assert len(rows) == 19
    assert all(row["phase_status"] == "complete" for row in rows)
    assert all(row["binary_object"] == "unplaced" for row in rows)
    return data


def row_factors(operation: str) -> list[str]:
    return sorted(
        factor_id
        for factor_id, factor in FACTOR_DEFS.items()
        if operation in factor["positive_rows"]
    )


def validate_against_ledger(data: dict[str, Any]) -> None:
    by = {row["operation"]: row for row in data["rows"]}

    # Existing derivation/mechanism classifications must match the factor map.
    for op in FACTOR_DEFS["existing-core-structural"]["positive_rows"]:
        assert by[op]["later_SENS_classification"] == "DERIVED-D1-D4", op
    for op in FACTOR_DEFS["historical-representation-mechanism"]["positive_rows"]:
        assert by[op]["later_SENS_classification"] == "HISTORICAL-MECHANISM", op

    # Shared-location family is one semantic core behind SET and SETQ.
    assert by["SET"]["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY"
    assert by["SETQ"]["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY"

    # GO is explicitly not part of non-local-exit residue.
    assert by["GO"]["later_SENS_classification"] == "DERIVED-D1-D4"
    assert by["RETURN"]["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY"
    assert by["PROG"]["later_SENS_classification"] == "COMPOSITE"

    fexpr = {"raw_operands": True, "explicit_caller_env": True, "result_reeval": False}
    macro = {"raw_operands": True, "explicit_caller_env": False, "result_reeval": True}
    assert by["FEXPR"]["protocol_axes"] == fexpr
    assert by["FSUBR"]["protocol_axes"] == fexpr
    assert by["TRANSFORMER"]["protocol_axes"] == macro
    assert by["TRANSFORMER"]["historical_expansion_locus"] == "definition-time"
    assert by["TRANSFORMER"]["current_sens_expansion_locus"] == "evaluation-time"

    # Every historical row must be consumed by at least one structural bucket.
    for op in EXPECTED_OPERATIONS:
        assert row_factors(op), f"unconsumed historical row: {op}"


def render(data: dict[str, Any]) -> dict[str, Any]:
    by = {row["operation"]: row for row in data["rows"]}

    rows = []
    for op in sorted(EXPECTED_OPERATIONS, key=lambda x: by[x]["order"]):
        row = by[op]
        factors = row_factors(op)
        rows.append({
            "historical_operation": op,
            "historical_phase": row["phase"],
            "presence": row["historical_presence"],
            "later_classification": row["later_SENS_classification"],
            "derived_by_existing_core": (
                "existing-core-structural" in factors
                or "historical-representation-mechanism" in factors
            ),
            "candidate_factors": factors,
            "source_issue": row["issue"],
            "evidence_sha": row["evidence_sha"],
            "placement": "UNPLACED",
        })

    factors = []
    for factor_id in sorted(FACTOR_DEFS):
        factor = FACTOR_DEFS[factor_id]
        factors.append({
            "factor_id": factor_id,
            "semantic_observable": factor["semantic_observable"],
            "positive_rows": sorted(factor["positive_rows"]),
            "negative_controls": sorted(factor["negative_controls"]),
            "dependency_on_other_factor": factor["dependency_on_other_factor"],
            "current_status": factor["current_status"],
            "evidence": factor["evidence"],
            "falsifier": factor["falsifier"],
        })

    return {
        "schema": "d5-structural-factor-graph/1",
        "authority": "research-only-no-placement",
        "source_ledger": str(LEDGER.relative_to(ROOT)),
        "historical_rows": rows,
        "factors": factors,
        "summary": {
            "historical_rows_consumed": len(rows),
            "candidate_factors_total": len(factors),
            "post_d4_factor_candidates": len(POST_D4_CANDIDATES),
            "post_d4_factor_ids": sorted(POST_D4_CANDIDATES),
            "proven_independent_roots": 0,
            "external_root_theorems": [
                {
                    "factor_id": "non-local-exit",
                    "classification": "semantic-residue-root",
                    "evidence": ["#2488", "#2504"],
                    "width": "UNKNOWN",
                    "coordinate": "UNPLACED",
                }
            ],
            "new_d5_residents": 0,
            "d5_selector_generated": 8,
            "d5_unknown_free": 24,
            "placement_search_authorized": False,
        },
    }


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    data = load_ledger()
    validate_against_ledger(data)
    graph = render(data)

    # Critical phase/placement guards.
    summary = graph["summary"]
    assert summary["historical_rows_consumed"] == 19
    assert summary["post_d4_factor_candidates"] == 7
    assert summary["proven_independent_roots"] == 0
    assert summary["new_d5_residents"] == 0
    assert summary["d5_selector_generated"] == 8
    assert summary["d5_unknown_free"] == 24
    assert summary["placement_search_authorized"] is False

    text = canonical(graph)
    if args.write:
        OUT.write_text(text, encoding="utf-8")
    if args.check:
        assert OUT.exists(), "factor graph artifact missing"
        assert OUT.read_text(encoding="utf-8") == text, "factor graph artifact stale"

    print("D5-STRUCTURAL-FACTOR=PASS")
    print("historical-rows-consumed=19")
    print(f"factors-total={summary['candidate_factors_total']}")
    print("post-d4-factor-candidates=7")
    print("proven-independent-roots=0")
    print("new-d5-residents=0")
    print("d5-selector-generated=8")
    print("d5-unknown-free=24")
    print("placement-search-authorized=no")
    print("RULE=factor-candidate-is-not-root")
    print("RULE=history-row-is-not-resident")


if __name__ == "__main__":
    main()
