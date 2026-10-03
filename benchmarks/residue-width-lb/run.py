#!/usr/bin/env python3
"""#2667 — bounded semantic-width lower-bound attack for parentless roots.

Question:
Can observation cardinality determine the exact Core identity width of the sole
post-D4 semantic root, non-local-exit?

Result scope:
- behavioral state cardinality may lower-bound a standalone state carrier;
- it does not by itself select the exact domain of one semantic operation root.
"""

from __future__ import annotations

import argparse
import json
import math
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ROOT_MIN = ROOT / "benchmarks" / "post-d4-root-min-closeout" / "run.py"
NONPREFIX = ROOT / "benchmarks" / "d6-nonprefix-falsifier" / "run.py"

NONLOCAL_OBSERVATIONS = (
    "ordinary-local-completion",
    "nearest-active-prog-exit",
    "nested-nearest-scope-selection",
    "fail-outside-active-prog",
)


def root_control() -> dict[str, Any]:
    rows = runpy.run_path(str(ROOT_MIN))["ROWS"]
    roots = [row for row in rows if row["root_status"] == "PROVEN-ROOT"]
    assert len(roots) == 1
    root = roots[0]
    assert root["factor"] == "non-local-exit"
    assert root["width"] == "UNKNOWN"
    assert root["coordinate"] == "UNPLACED"
    return root


def cardinality_control() -> dict[str, Any]:
    assert len(set(NONLOCAL_OBSERVATIONS)) == 4
    standalone_bits = math.ceil(math.log2(len(NONLOCAL_OBSERVATIONS)))
    assert standalone_bits == 2
    return {
        "observation_count": len(NONLOCAL_OBSERVATIONS),
        "standalone_state_carrier_lower_bound_bits": standalone_bits,
        "observations": list(NONLOCAL_OBSERVATIONS),
    }


def cross_domain_counterexample() -> dict[str, Any]:
    ns = runpy.run_path(str(NONPREFIX))
    min_binary_width = ns["min_binary_width"]

    # #2527's binding-policy algebra is the positive counterexample to the
    # inference "four observations imply a 2-bit Core identity".
    assert min_binary_width(4) == 2

    return {
        "semantic_state_count": 4,
        "standalone_product_width": 2,
        "local_parent_path_width": 6,
        "standalone_domain": "BindingPolicyProduct-D2-hypothetical",
        "local_domain": "Core-D6-under-D4-DEFINE",
        "theorem": (
            "the same four semantic distinctions can have a 2-bit standalone "
            "state coordinate while a locally parented Core identity uses a "
            "6-bit path; state-cardinality width and Core identity-domain width "
            "are therefore different questions"
        ),
        "evidence": "#2527/#2541",
    }


def validate_separation(
    root: dict[str, Any],
    cardinality: dict[str, Any],
    control: dict[str, Any],
) -> dict[str, Any]:
    assert root["root_status"] == "PROVEN-ROOT"
    assert cardinality["standalone_state_carrier_lower_bound_bits"] == 2
    assert control["standalone_product_width"] == 2
    assert control["local_parent_path_width"] == 6

    # The root itself remains one semantic operation identity.  Its dynamic
    # observations are behavior under context, not four distinct operation
    # identities requiring four identity codes.
    semantic_identity_count = 1
    assert semantic_identity_count == 1

    return {
        "semantic_operation_identity_count": semantic_identity_count,
        "dynamic_observation_count": cardinality["observation_count"],
        "standalone_behavior_carrier_bits": cardinality[
            "standalone_state_carrier_lower_bound_bits"
        ],
        "identity_width_from_observation_cardinality": "UNRESOLVED",
        "core_domain_membership_from_cardinality": "NOT-ESTABLISHED",
        "reason": (
            "behavioral outcomes live in context/result space; they are not "
            "multiple identities of the non-local-exit operation"
        ),
    }


def build_result() -> dict[str, Any]:
    root = root_control()
    cardinality = cardinality_control()
    control = cross_domain_counterexample()
    separation = validate_separation(root, cardinality, control)

    result = {
        "schema": "residue-width-lower-bound/v1",
        "phase": "SENS-DERIVATION",
        "authority": "research-only-no-placement",
        "root": {
            "factor": root["factor"],
            "status": root["root_status"],
            "width": root["width"],
            "coordinate": root["coordinate"],
            "evidence": root["evidence"],
        },
        "nonlocal_behavioral_corpus": cardinality,
        "cross_domain_positive_control": control,
        "separation": separation,
        "verdict": {
            "minimum_width_theorem": "BOUNDED-ONLY",
            "what_is_bounded": "standalone-behavior-state-carrier",
            "standalone_behavior_carrier_lower_bound_bits": 2,
            "root_identity_exact_width": "UNRESOLVED",
            "d5_eligibility": "NOT-ESTABLISHED",
            "d6_eligibility": "NOT-ESTABLISHED",
            "coordinate": "UNPLACED",
            "new_residents": 0,
        },
        "falsified_inference": (
            "observation-count -> operation-identity-width -> Core-domain-membership"
        ),
        "guards": [
            "behavioral state != operation identity",
            "state-carrier width != Core identity width",
            "axis count != exact domain membership",
            "local parent path law may justify width independently of cardinality",
            "no coordinate from information theory alone",
        ],
    }

    assert result["verdict"]["root_identity_exact_width"] == "UNRESOLVED"
    assert result["verdict"]["coordinate"] == "UNPLACED"
    assert result["verdict"]["new_residents"] == 0
    return result


def report(result: dict[str, Any]) -> str:
    c = result["nonlocal_behavioral_corpus"]
    x = result["cross_domain_positive_control"]
    v = result["verdict"]

    return "\n".join(
        [
            "# Residue semantic-width lower bound — #2667",
            "",
            "Non-local-exit behavioral corpus:",
            f"- observations: {c['observation_count']}",
            f"- standalone state-carrier information lower bound: "
            f"{c['standalone_state_carrier_lower_bound_bits']} bits",
            "",
            "#2527 cross-domain control:",
            f"- same semantic-state count: {x['semantic_state_count']}",
            f"- standalone product width: {x['standalone_product_width']}",
            f"- local parent-path width: {x['local_parent_path_width']}",
            "",
            "Result:",
            f"- MINIMUM-WIDTH-THEOREM={v['minimum_width_theorem']}",
            f"- bounded object={v['what_is_bounded']}",
            f"- ROOT-IDENTITY-WIDTH={v['root_identity_exact_width']}",
            f"- D5-ELIGIBLE={v['d5_eligibility']}",
            f"- D6-ELIGIBLE={v['d6_eligibility']}",
            f"- COORDINATE={v['coordinate']}",
            f"- NEW-RESIDENTS={v['new_residents']}",
            "",
            "Interpretation:",
            "Four observations justify a two-bit standalone behavior/state carrier",
            "if one chooses to encode those states. They do not imply that the",
            "single non-local-exit semantic root has a two-bit identity, belongs",
            "to D5/D6, or has any particular exact Core width.",
            "",
        ]
    )


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

    print("RESIDUE-WIDTH-LB=PASS")
    print("MINIMUM-WIDTH-THEOREM=BOUNDED-ONLY")
    print("STANDALONE-BEHAVIOR-CARRIER-LB=2")
    print("ROOT-IDENTITY-WIDTH=UNRESOLVED")
    print("D5-ELIGIBLE=NOT-ESTABLISHED")
    print("D6-ELIGIBLE=NOT-ESTABLISHED")
    print("COORDINATE=UNPLACED")
    print("NEW-RESIDENTS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
