#!/usr/bin/env python3
"""#2677 — D6 PURE-UNKNOWN admitted-parent tournament.

Search semantic families/capabilities, never free coordinate labels.

A PURE-UNKNOWN D6 candidate requires ALL of:
1. an exact admitted D1-D5 same-base parent;
2. exactly two independently witnessed semantic deltas;
3. an exact replayable two-delta composition/generator law;
4. a local lower-bound theorem showing one delta is insufficient;
5. no derivability/composite/carrier-policy collapse;
6. no existing non-PURE D6 evidence lane already owns the pressure.

NO-CANDIDATE is a successful result.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import runpy
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
HISTORICAL = REPO / "docs" / "research" / "2344-post-d4-historical-ledger.json"
SPECIAL = REPO / "benchmarks" / "d5-structural-discovery" / "special-call-factor.json"
ROOT_MIN = REPO / "benchmarks" / "post-d4-root-min-closeout" / "run.py"
FRONTIER = REPO / "benchmarks" / "d6-unknown-frontier" / "run.py"
BINDING_LB = REPO / "scripts" / "research-2518-d6-binding-residency-lower-bound.py"

UNRESOLVED_OPS = {"SET", "SETQ", "PROG", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"}


def capture_main(path: Path) -> tuple[dict[str, Any], str]:
    ns = runpy.run_path(str(path))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns["main"]()
    return ns, buf.getvalue()


def load_historical() -> list[dict[str, Any]]:
    data = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    rows = [
        row for row in data["rows"]
        if row["current_domain_candidate"] == "unresolved"
    ]
    ops = {row["operation"] for row in rows}
    assert UNRESOLVED_OPS <= ops
    assert all(row["binary_object"] == "unplaced" for row in rows)
    return [row for row in rows if row["operation"] in UNRESOLVED_OPS]


def root_statuses() -> dict[str, str]:
    ns = runpy.run_path(str(ROOT_MIN))
    ns["validate"]()
    return {row["factor"]: row["root_status"] for row in ns["ROWS"]}


def special_data() -> dict[str, Any]:
    data = json.loads(SPECIAL.read_text(encoding="utf-8"))
    assert data["summary"]["proved_d6_children"] == 0
    assert data["summary"]["width_status"] == "UNKNOWN"
    return data


def frontier_data() -> dict[str, Any]:
    ns = runpy.run_path(str(FRONTIER))
    result = ns["build"]()
    assert result["canonical"]["occupancy_mutations"] == 0
    assert result["frontier_counts"][ns["PURE_UNKNOWN"]] == 44
    return result


def candidate_row(
    *,
    capability: str,
    source: str,
    parent: str | None,
    same_base: str,
    deltas: list[str],
    delta_statuses: list[str],
    composition_law: str,
    lower_bound: str,
    collapse_reason: str | None,
    existing_frontier_lane: str | None,
    verdict: str,
) -> dict[str, Any]:
    exact_two = len(deltas) == 2
    independent = bool(deltas) and all(
        status in {"CARRIER-PREMISE", "POLICY-OVER-ROOT", "PROVEN-ROOT"}
        for status in delta_statuses
    )
    passes = (
        parent is not None
        and same_base == "PROVED"
        and exact_two
        and independent
        and composition_law == "PROVED"
        and lower_bound == "PROVED"
        and collapse_reason is None
        and existing_frontier_lane is None
    )
    return {
        "capability": capability,
        "source": source,
        "candidate_parent": parent,
        "same_base_parent": same_base,
        "semantic_deltas": deltas,
        "delta_root_classes": delta_statuses,
        "exactly_two_deltas": exact_two,
        "deltas_independently_witnessed": independent,
        "two_delta_composition_law": composition_law,
        "local_lower_bound": lower_bound,
        "collapse_reason": collapse_reason,
        "existing_nonpure_frontier_lane": existing_frontier_lane,
        "pure_unknown_candidate": passes,
        "verdict": verdict,
        "coordinate": "UNPLACED",
    }


def build() -> dict[str, Any]:
    historical = {row["operation"]: row for row in load_historical()}
    roots = root_statuses()
    special = special_data()
    frontier = frontier_data()

    # Positive method control: this is a real same-base + two-delta D6 local
    # theorem, but it is already a separately classified NON-PURE frontier lane.
    _binding_ns, binding_out = capture_main(BINDING_LB)
    assert "D6-BINDING-RESIDENCY-LOWER-BOUND=PASS" in binding_out
    assert "OBSERVABLE-INDEPENDENT-DELTA-COUNT=2" in binding_out
    assert "D6-LOCAL-TWO-DELTA-SUFFICIENT=yes" in binding_out
    assert "D6-TARGET-CANDIDATE=001111" in binding_out
    target_frontier = next(
        row for row in frontier["frontier"] if row["coordinate"] == "001111"
    )
    assert target_frontier["research_evidence_class"] == "OWNER-READY-NONADMITTED"
    assert target_frontier["canonical_semantic_member"] is False

    controls = [
        candidate_row(
            capability="DEFINE->shared-location-target",
            source="#2492/#2511/#2518",
            parent="D4 DEFINE 0011",
            same_base="PROVED",
            deltas=["nearest-existing-scope", "fail-on-miss"],
            delta_statuses=["CARRIER-PREMISE", "CARRIER-PREMISE"],
            composition_law="PROVED",
            lower_bound="PROVED",
            collapse_reason=None,
            existing_frontier_lane="001111 OWNER-READY-NONADMITTED",
            verdict="POSITIVE-TWO-DELTA-CONTROL-BUT-NOT-PURE-UNKNOWN",
        )
    ]
    assert controls[0]["pure_unknown_candidate"] is False

    same_base_tests = {
        row["protocol"]: row for row in special["same_base_parent_tests"]
    }

    rows: list[dict[str, Any]] = []

    # SET/SETQ pressure is already owned by the known binding-policy overlay,
    # so lane A must not re-export it into one of the 44 PURE-UNKNOWN slots.
    for op in ("SET", "SETQ"):
        assert historical[op]["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY"
        rows.append(
            candidate_row(
                capability=op,
                source=f"historical #{historical[op]['issue']} + #2518",
                parent="D4 DEFINE 0011",
                same_base="PROVED-FOR-SHARED-LOCATION-CORE",
                deltas=["nearest-existing-scope", "fail-on-miss"],
                delta_statuses=[roots["shared-location-update"], roots["shared-location-update"]],
                composition_law="PROVED",
                lower_bound="PROVED",
                collapse_reason="SET/SETQ names collapse to one shared-location semantic core",
                existing_frontier_lane="001100..001111 binding-policy overlay; 001111 owner-ready nonadmitted",
                verdict="EXCLUDED-SEPARATE-NONPURE-OVERLAY",
            )
        )

    # PROG is a historical composite; surviving irreducibility belongs to RETURN.
    assert historical["PROG"]["later_SENS_classification"] == "COMPOSITE"
    rows.append(
        candidate_row(
            capability="PROG",
            source=f"historical #{historical['PROG']['issue']} + #2617",
            parent=None,
            same_base="NONE",
            deltas=["local-GO-derived", "non-local-exit-root"],
            delta_statuses=["DERIVED", roots["non-local-exit"]],
            composition_law="COMPOSITE-NOT-GENERATOR",
            lower_bound="NOT-APPLICABLE",
            collapse_reason="historical container composes derived GO with RETURN root; not a primitive child",
            existing_frontier_lane=None,
            verdict="NO-CANDIDATE-COMPOSITE",
        )
    )

    # RETURN is the one proven root, but parentless roots do not enter this
    # generated-child tournament. #2662/#2663 owns domain admission for it.
    assert roots["non-local-exit"] == "PROVEN-ROOT"
    rows.append(
        candidate_row(
            capability="RETURN",
            source="#2488/#2504/#2617",
            parent=None,
            same_base="NONE-PROVED",
            deltas=["non-local-exit"],
            delta_statuses=["PROVEN-ROOT"],
            composition_law="NONE-PARENTLESS-ROOT",
            lower_bound="ROOT-THEOREM-NOT-CHILD-WIDTH",
            collapse_reason="parentless root; residue-domain law owns exact-domain admission",
            existing_frontier_lane=None,
            verdict="NO-CANDIDATE-NO-D1-D5-PARENT",
        )
    )

    # FEXPR/FSUBR have two independently observable axes but the current
    # special-call artifact explicitly says there is no admitted same-base
    # parent theorem. Two axes alone cannot synthesize a D6 child.
    fexpr_test = same_base_tests["fexpr-fsubr"]
    assert fexpr_test["same_base_object"] == "UNPROVEN"
    assert fexpr_test["observable_deltas"] == ["explicit-caller-env", "raw-form-input"]
    for op in ("FEXPR", "FSUBR"):
        rows.append(
            candidate_row(
                capability=op,
                source=f"historical #{historical[op]['issue']} + #2522/#2530/#2617",
                parent="D4 LAMBDA (attacked candidate)",
                same_base="UNPROVEN",
                deltas=list(fexpr_test["observable_deltas"]),
                delta_statuses=[
                    roots["explicit-caller-env"],
                    roots["raw-form-input"],
                ],
                composition_law="PROTOCOL-CUBE-ONLY-NOT-D6-GENERATOR",
                lower_bound="NO-EXACT-D6-CHILD-LOWER-BOUND",
                collapse_reason=None,
                existing_frontier_lane=None,
                verdict="NO-CANDIDATE-NO-SAME-BASE-THEOREM",
            )
        )

    # Historical Hart transformer is even farther from a D6 two-delta child:
    # same-base theorem absent and four observed axes relative to ordinary lambda.
    hart = same_base_tests["hart-macro"]
    assert hart["same_base_object"] == "UNPROVEN"
    assert len(hart["observable_deltas"]) == 4
    rows.append(
        candidate_row(
            capability="TRANSFORMER(Hart-1963)",
            source=f"historical #{historical['TRANSFORMER']['issue']} + #2568/#2588",
            parent="D4 LAMBDA (attacked candidate)",
            same_base="UNPROVEN",
            deltas=list(hart["observable_deltas"]),
            delta_statuses=[
                roots[delta] for delta in hart["observable_deltas"]
            ],
            composition_law="NO-EXACT-TWO-DELTA-D6-GENERATOR",
            lower_bound="NO",
            collapse_reason=None,
            existing_frontier_lane=None,
            verdict="NO-CANDIDATE-FOUR-DELTAS-AND-NO-PARENT",
        )
    )

    # Strongest negative control: current SENS transformer *does* share the D4
    # LAMBDA closure payload and differs on exactly two observed axes. Still,
    # #2591/#2602 deliberately prove no width from factor count. Root
    # minimization further classifies these axes as carrier/policy structure.
    sens_t = same_base_tests["sens-transformer"]
    assert sens_t["same_base_object"] is True
    assert sens_t["observable_deltas"] == ["raw-form-input", "returned-form-protocol"]
    rows.append(
        candidate_row(
            capability="current-SENS-TRANSFORMER-control",
            source="#2198/#2200/#2591/#2602/#2617",
            parent="D4 LAMBDA",
            same_base="PROVED",
            deltas=list(sens_t["observable_deltas"]),
            delta_statuses=[
                roots["raw-form-input"],
                roots["returned-form-protocol"],
            ],
            composition_law="NOT-PROVED-AS-D6-LOCAL-GENERATOR",
            lower_bound="NOT-PROVED-FROM-TWO-FACTOR-CARDINALITY",
            collapse_reason=(
                "two observed factors classify as carrier/policy structure; "
                "factor count is not a width theorem"
            ),
            existing_frontier_lane=None,
            verdict="PRESSURE-NOT-CANDIDATE-TWO-DELTAS-INSUFFICIENT",
        )
    )

    assert len(rows) == 8
    assert not any(row["pure_unknown_candidate"] for row in rows)
    assert frontier["frontier_counts"]["PURE-UNKNOWN"] == 44
    assert frontier["canonical"]["occupancy_mutations"] == 0

    result = {
        "schema": "d6-pure-unknown-parent-tournament/v1",
        "issue": 2677,
        "domain": "Core D6",
        "phase": "SENS-DERIVATION",
        "candidate_rule": {
            "same_base_parent": "required",
            "independent_semantic_deltas": 2,
            "exact_composition_generator": "required",
            "local_lower_bound": "required",
            "non_derivable_or_composite": "required",
            "not_already_owned_by_nonpure_frontier_lane": "required",
        },
        "positive_controls": controls,
        "tournament_rows": rows,
        "summary": {
            "historical_unresolved_rows_tested": 7,
            "extra_current_sens_control_rows": 1,
            "pure_unknown_coordinates": 44,
            "pure_unknown_candidates": 0,
            "known_nonpure_two_delta_controls": 1,
            "occupancy_mutations": 0,
            "result": "NO-CANDIDATE",
        },
        "guards": [
            "never search free coordinate labels",
            "two observable deltas do not imply D6 without exact generator/lower-bound law",
            "parentless roots are not generated children",
            "composites are not primitive residents",
            "known 001111 evidence does not transfer to PURE-UNKNOWN",
            "no Core-Math or mechanism donation",
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

    print("D6-PURE-UNKNOWN-PARENT-TOURNAMENT=PASS")
    print("historical-unresolved-tested=7")
    print("current-sens-control-tested=1")
    print("known-nonpure-two-delta-control=PASS")
    print("pure-unknown-candidates=0")
    print("occupancy-mutations=0")
    print("RESULT=NO-CANDIDATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
