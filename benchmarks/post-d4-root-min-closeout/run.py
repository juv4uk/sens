#!/usr/bin/env python3
"""#2617 — aggregate post-D4 root-minimization ledger.

This file does not re-prove child results. It composes the independently
executable R1..R6 witnesses plus the existing RETURN positive-root theorem into
one machine-checked accounting view.

Hard invariant:
    bounded-independent fact != semantic root != width != coordinate
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ALLOWED = {
    "PROVEN-ROOT",
    "DERIVED",
    "POLICY-OVER-ROOT",
    "CARRIER-PREMISE",
    "UNRESOLVED",
}

ROWS = [
    {
        "factor": "shared-location-update",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "hidden_capability_needed": True,
        "basis_dependencies": "explicit Store+Location carrier; ordinary lookup/data",
        "root_status": "CARRIER-PREMISE",
        "evidence": "#2628/#2654; donor #2589/#2598",
        "counterexample": (
            "pure immutable threading reproduces update only when S1 is passed; "
            "pre-existing no-arg observer sees NEW only with ambient shared-store authority"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
    },
    {
        "factor": "non-local-exit",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "hidden_capability_needed": True,
        "basis_dependencies": "D1-D4 control/composition insufficient without equivalent non-local continuation/exit channel",
        "root_status": "PROVEN-ROOT",
        "evidence": "#2488/#2504",
        "counterexample": (
            "local return/tail recursion cannot reproduce exit to the most-recent "
            "dynamic PROG target without importing equivalent non-local control authority"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
    },
    {
        "factor": "raw-form-input",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "hidden_capability_needed": True,
        "basis_dependencies": "ordinary explicit syntax/QUOTE data reproduces body observation",
        "root_status": "CARRIER-PREMISE",
        "evidence": "#2629/#2635",
        "counterexample": (
            "unchanged eager same-source calling loses unused/raw syntax; explicit "
            "quoted syntax recovers the observation, while transparent auto-quote is an imported channel"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
    },
    {
        "factor": "explicit-caller-env",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "hidden_capability_needed": True,
        "basis_dependencies": "explicit environment-shaped ordinary data + LOOKUP/BIND",
        "root_status": "CARRIER-PREMISE",
        "evidence": "#2630/#2637/#2641/#2651",
        "counterexample": (
            "explicit env value reproduces caller lookup; transparent current-caller-env "
            "acquisition requires evaluator reflection/injection"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
    },
    {
        "factor": "returned-form-protocol",
        "bounded_independent": True,
        "derivable_from_basis": True,
        "hidden_capability_needed": True,
        "basis_dependencies": "D4 EVAL + explicit form value + caller-env carrier premise",
        "root_status": "POLICY-OVER-ROOT",
        "evidence": "#2631/#2650",
        "counterexample": (
            "produce form + explicit context + D4 EVAL reproduces behavior; "
            "caller-context selection changes result and is charged separately"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
    },
    {
        "factor": "expansion-timing",
        "bounded_independent": True,
        "derivable_from_basis": True,
        "hidden_capability_needed": False,
        "basis_dependencies": "transform capability + explicit stored payload + scheduling/phase policy",
        "root_status": "POLICY-OVER-ROOT",
        "evidence": "#2632/#2639",
        "counterexample": (
            "OLD/NEW expansion observations are reproduced by explicit definition-time "
            "vs evaluation-time scheduling; hidden cache state would be separately charged"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
    },
    {
        "factor": "invocation-packaging",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "hidden_capability_needed": True,
        "basis_dependencies": "explicit head + operands -> whole-call construction",
        "root_status": "CARRIER-PREMISE",
        "evidence": "#2633/#2638/#2640",
        "counterexample": (
            "operands-only alias collision cannot recover head; explicit head makes "
            "whole-call construction derived, while automatic head acquisition is a carrier premise"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
    },
]

NEGATIVE_CONTROLS = [
    {"factor": "LABEL", "status": "DERIVED-D4"},
    {"factor": "FUNCTION/FUNARG", "status": "HISTORICAL-MECHANISM"},
    {"factor": "EVALQUOTE", "status": "DERIVED-D4"},
    {"factor": "APPEND/ASSOC/etc", "status": "DERIVED-D1-D4"},
]


def validate() -> dict:
    assert len(ROWS) == 7
    assert len({row["factor"] for row in ROWS}) == 7
    assert all(row["bounded_independent"] for row in ROWS)
    assert all(row["root_status"] in ALLOWED for row in ROWS)
    assert all(row["width"] == "UNKNOWN" for row in ROWS)
    assert all(row["coordinate"] == "UNPLACED" for row in ROWS)
    assert all(row["evidence"] for row in ROWS)
    assert all(row["counterexample"] for row in ROWS)

    counts = Counter(row["root_status"] for row in ROWS)
    expected = {
        "PROVEN-ROOT": 1,
        "CARRIER-PREMISE": 4,
        "POLICY-OVER-ROOT": 2,
        "DERIVED": 0,
        "UNRESOLVED": 0,
    }
    assert {key: counts.get(key, 0) for key in expected} == expected

    root = next(row for row in ROWS if row["root_status"] == "PROVEN-ROOT")
    assert root["factor"] == "non-local-exit"

    # No root classification may smuggle placement.
    assert not any(row["coordinate"] != "UNPLACED" for row in ROWS)
    assert not any(row["width"] != "UNKNOWN" for row in ROWS)

    return expected


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    counts = validate()

    with (args.out / "root-ledger.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(ROWS[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(ROWS)

    result = {
        "schema": "post-d4-root-min-closeout/v1",
        "phase": "SENS-DERIVATION",
        "authority": "research-only aggregation of child witnesses",
        "input_factor_facts": 7,
        "proved_roots": counts["PROVEN-ROOT"],
        "derived_factors": counts["DERIVED"],
        "policy_factors": counts["POLICY-OVER-ROOT"],
        "carrier_premises": counts["CARRIER-PREMISE"],
        "unresolved": counts["UNRESOLVED"],
        "new_residents": 0,
        "coordinates": 0,
        "rows": ROWS,
        "negative_controls": NEGATIVE_CONTROLS,
        "placement_handoff": {
            "d5_positive_candidates_from_root_minimization": 0,
            "reason": (
                "root classification does not itself provide same-base one-delta "
                "placement; all carrier/policy factors remain non-residents and the "
                "sole proven root has width UNKNOWN"
            ),
        },
        "non_conclusions": [
            "one proven root does not imply any D5/D6 coordinate",
            "carrier premises are semantic authority but not residents by themselves",
            "policy-over-root factors do not add independent roots",
            "D6 SETQ readiness remains a separate same-base placement theorem",
            "factor count does not determine bit width",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = f"""# Post-D4 root minimization closeout — #2617

Input bounded-independent factor facts: **7**

| root classification | count |
|---|---:|
| PROVEN-ROOT | {counts['PROVEN-ROOT']} |
| CARRIER-PREMISE | {counts['CARRIER-PREMISE']} |
| POLICY-OVER-ROOT | {counts['POLICY-OVER-ROOT']} |
| DERIVED | {counts['DERIVED']} |
| UNRESOLVED | {counts['UNRESOLVED']} |

The sole bounded PROVEN-ROOT is **non-local-exit** (#2488/#2504).

Carrier premises:
- shared-location-update;
- raw-form-input;
- explicit-caller-env;
- invocation-packaging.

Policies over admitted roots:
- returned-form-protocol;
- expansion-timing.

Every row keeps:
- width = UNKNOWN;
- coordinate = UNPLACED.

New residents: **0**
Coordinates allocated: **0**
D5 positive placement candidates produced by this root ledger: **0**

Interpretation: seven independently observable post-D4 facts compress to one
proved semantic root plus carrier/policy structure. Root counting is therefore
strictly smaller than factor counting, and neither count determines width.
"""
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
