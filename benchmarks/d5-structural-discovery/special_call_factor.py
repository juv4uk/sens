#!/usr/bin/env python3
"""#2591 — factor special-call protocols without width inference.

Structural-discovery only.

The witness separates five independently observable protocol axes:
A raw-form input
B explicit caller environment
C returned-form / caller re-evaluation
D expansion timing/locus
E invocation packaging

Independence is evidence about observables, not a claim that each axis is a
semantic root, bit, resident, or width contribution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "benchmarks" / "d5-structural-discovery" / "special-call-factor.json"

AXES = {
    "raw-form-input": {
        "observable": "call body receives unevaluated form structure rather than eager values",
        "evidence": ["#2522", "#2530"],
        "remove_one_attack": "unused undefined operand becomes eager/fails instead of remaining inert raw syntax",
        "independence": "proved-by-eight-corner-ABC-cube",
    },
    "explicit-caller-env": {
        "observable": "call body receives caller environment as an explicit semantic input",
        "evidence": ["#2522", "#2530"],
        "remove_one_attack": "caller-only binding cannot be observed without adding another environment channel",
        "independence": "proved-by-eight-corner-ABC-cube",
    },
    "returned-form-protocol": {
        "observable": "returned object is treated as executable replacement form and evaluated in caller context",
        "evidence": ["#2522", "#2530", "#2557"],
        "remove_one_attack": "returned symbol/form stays a direct value instead of resolving/executing in caller context",
        "independence": "proved-by-eight-corner-ABC-cube",
    },
    "expansion-timing": {
        "observable": "definition-time expansion differs from evaluation-time expansion",
        "evidence": ["#2568", "#2569"],
        "remove_one_attack": "macro redefinition can no longer distinguish OLD definition-time body from NEW evaluation-time behavior",
        "independence": "proved-with-single-head-timing-witness; packaging distinction is not exercised",
    },
    "invocation-packaging": {
        "observable": "whole invocation form exposes call head while operand-only input does not",
        "evidence": ["#2580", "#2588", "3d409736b994221561b413c42c837a428d242358"],
        "remove_one_attack": "two aliases of one transformer with identical operands collapse to identical input and the head cannot be reconstructed",
        "independence": "proved-by-alias-collision-with-raw/env/result-held-fixed",
    },
}

PROTOCOLS = {
    "ordinary-lambda-control": {
        "raw-form-input": False,
        "explicit-caller-env": False,
        "returned-form-protocol": False,
        "expansion-timing": "evaluation-time",
        "invocation-packaging": "operands-only",
    },
    "fexpr-fsubr": {
        "raw-form-input": True,
        "explicit-caller-env": True,
        "returned-form-protocol": False,
        "expansion-timing": "evaluation-time",
        "invocation-packaging": "operands-only",
    },
    "hart-macro": {
        "raw-form-input": True,
        "explicit-caller-env": False,
        "returned-form-protocol": True,
        "expansion-timing": "definition-time",
        "invocation-packaging": "whole-call",
    },
    "sens-transformer": {
        "raw-form-input": True,
        "explicit-caller-env": False,
        "returned-form-protocol": True,
        "expansion-timing": "evaluation-time",
        "invocation-packaging": "operands-only",
    },
}


def deltas(left: str, right: str) -> list[str]:
    a = PROTOCOLS[left]
    b = PROTOCOLS[right]
    return sorted(axis for axis in AXES if a[axis] != b[axis])


def render() -> dict[str, Any]:
    comparisons = {
        "lambda->fexpr": deltas("ordinary-lambda-control", "fexpr-fsubr"),
        "lambda->sens-transformer": deltas("ordinary-lambda-control", "sens-transformer"),
        "lambda->hart-macro": deltas("ordinary-lambda-control", "hart-macro"),
        "fexpr->sens-transformer": deltas("fexpr-fsubr", "sens-transformer"),
        "hart->sens-transformer": deltas("hart-macro", "sens-transformer"),
    }

    # Structural controls.
    assert comparisons["lambda->fexpr"] == [
        "explicit-caller-env",
        "raw-form-input",
    ]
    assert comparisons["lambda->sens-transformer"] == [
        "raw-form-input",
        "returned-form-protocol",
    ]
    assert comparisons["fexpr->sens-transformer"] == [
        "explicit-caller-env",
        "returned-form-protocol",
    ]
    assert comparisons["hart->sens-transformer"] == [
        "expansion-timing",
        "invocation-packaging",
    ]

    # The archived one-bit LAMBDA->TRANSFORMER story fails the current
    # parent+one-observable-delta placement law: same base is useful evidence,
    # but two independently separable protocol deltas remain.
    assert len(comparisons["lambda->sens-transformer"]) == 2

    return {
        "schema": "special-call-factor/1",
        "phase": "STRUCTURAL-DISCOVERY",
        "authority": "research-only-no-placement",
        "domain": "Core.PostD4.SpecialCallProtocol",
        "binary_object": "UNPLACED",
        "axes": [
            {
                "factor_id": axis,
                **AXES[axis],
                "status": "independently-observable-axis",
                "root_status": "UNPROVEN",
                "width_consequence": "NONE",
                "placement_consequence": "NONE",
            }
            for axis in sorted(AXES)
        ],
        "protocols": [
            {"protocol": name, "axes": PROTOCOLS[name]}
            for name in (
                "ordinary-lambda-control",
                "fexpr-fsubr",
                "hart-macro",
                "sens-transformer",
            )
        ],
        "comparisons": comparisons,
        "same_base_parent_tests": [
            {
                "protocol": "sens-transformer",
                "candidate_parent": "D4-LAMBDA",
                "same_base_object": True,
                "evidence": ["#2198", "#2200"],
                "observable_deltas": comparisons["lambda->sens-transformer"],
                "one_delta_child": False,
                "verdict": "SAME-BASE-YES; D5-ONE-DELTA-NOT-PROVED",
            },
            {
                "protocol": "fexpr-fsubr",
                "candidate_parent": "D4-LAMBDA",
                "same_base_object": "UNPROVEN",
                "evidence": ["#2522", "#2530"],
                "observable_deltas": comparisons["lambda->fexpr"],
                "one_delta_child": False,
                "verdict": "NO-ADMITTED-SAME-BASE-PARENT-THEOREM",
            },
            {
                "protocol": "hart-macro",
                "candidate_parent": "D4-LAMBDA",
                "same_base_object": "UNPROVEN",
                "evidence": ["#2557", "#2568", "#2580"],
                "observable_deltas": comparisons["lambda->hart-macro"],
                "one_delta_child": False,
                "verdict": "NO-ADMITTED-SAME-BASE-PARENT-THEOREM",
            },
        ],
        "summary": {
            "independently_observable_protocol_axes": 5,
            "proved_semantic_roots": 0,
            "proved_width_from_axis_count": False,
            "proved_d5_children": 0,
            "proved_d6_children": 0,
            "coordinates_allocated": 0,
            "archived_00101_transformer_reusable": False,
            "reason_00101_not_reusable": "same LAMBDA payload does not reduce two independently separable deltas (raw input + returned-form protocol) to one observable delta",
            "width_status": "UNKNOWN",
            "placement_status": "UNPLACED",
        },
    }


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    graph = render()
    text = canonical(graph)

    if args.write:
        OUT.write_text(text, encoding="utf-8")
    if args.check:
        assert OUT.exists(), "special-call factor artifact missing"
        assert OUT.read_text(encoding="utf-8") == text, "special-call factor artifact stale"

    summary = graph["summary"]
    print("SPECIAL-CALL-FACTOR=PASS")
    print("independently-observable-axes=5")
    print("proved-semantic-roots=0")
    print("lambda-transformer-observable-deltas=2")
    print("archived-00101-reusable=no")
    print("width-status=UNKNOWN")
    print("coordinates-allocated=0")
    print("RULE=axis-count-does-not-imply-width")
    print("RULE=same-base-does-not-imply-one-delta")


if __name__ == "__main__":
    main()
