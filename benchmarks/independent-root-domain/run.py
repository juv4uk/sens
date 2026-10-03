#!/usr/bin/env python3
"""#2668 — independent exact root-domain attack.

Research only. This lane tests whether parentless PROVEN-ROOT objects can form
an independent Core domain without recreating an arbitrary table.

No domain ratification, coordinate allocation, D5/D6 mutation, or proof-address
construction is performed here.
"""

from __future__ import annotations

import argparse
import json
import math
import runpy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT_CLOSEOUT = REPO / "benchmarks/post-d4-root-min-closeout/run.py"
D6_CLOSEOUT = REPO / "benchmarks/d6-closure-map/run.py"
NONLOCAL_DOMAIN = REPO / "benchmarks/nonlocal-exit-domain/run.py"
AUTOMORPHISM = REPO / "benchmarks/root-domain-automorphism/run.py"


def load_controls():
    root_ns = runpy.run_path(str(ROOT_CLOSEOUT))
    d6_ns = runpy.run_path(str(D6_CLOSEOUT))
    nonlocal_ns = runpy.run_path(str(NONLOCAL_DOMAIN))
    automorphism_ns = runpy.run_path(str(AUTOMORPHISM))

    rows = root_ns["ROWS"]
    roots = [row for row in rows if row["root_status"] == "PROVEN-ROOT"]
    carrier = [row for row in rows if row["root_status"] == "CARRIER-PREMISE"]
    policy = [row for row in rows if row["root_status"] == "POLICY-OVER-ROOT"]

    assert len(roots) == 1
    assert roots[0]["factor"] == "non-local-exit"
    assert roots[0]["width"] == "UNKNOWN"
    assert roots[0]["coordinate"] == "UNPLACED"
    assert len(carrier) == 4
    assert len(policy) == 2

    d6_rows = d6_ns["build_map"]()
    selectors = [row for row in d6_rows if row["status"] == "generated"]
    assert len(selectors) == 16
    assert all(row["semantic_family"] == "selector" for row in selectors)

    # Reuse the merged positive-control logic without executing its CLI.
    d5_row, root_row, d6_map, frontier, _ = nonlocal_ns["load_inputs"]()
    domain_status = nonlocal_ns["validate_inputs"](d5_row, root_row, d6_map, frontier)
    assert domain_status["d5"]["eligible"] == "NO"
    assert domain_status["d6"]["eligible"] == "UNRESOLVED"

    automorphism = automorphism_ns["build_result"]()
    assert automorphism["verdict"]["root_domain"] == "TABLE-RELOCATION-UNDER-CURRENT-EVIDENCE"
    assert automorphism["verdict"]["exact_width"] == "UNRESOLVED"
    assert automorphism["verdict"]["coordinate"] == "UNPLACED"

    return {
        "rows": rows,
        "roots": roots,
        "carrier": carrier,
        "policy": policy,
        "selectors": selectors,
        "domain_status": domain_status,
        "automorphism": automorphism,
    }


def membership_control(controls):
    """Research-class membership predicate, not a ratified domain."""
    admitted = [
        row["factor"]
        for row in controls["rows"]
        if row["root_status"] == "PROVEN-ROOT"
    ]
    rejected = {
        row["factor"]: row["root_status"]
        for row in controls["rows"]
        if row["root_status"] != "PROVEN-ROOT"
    }

    assert admitted == ["non-local-exit"]
    assert set(rejected.values()) == {"CARRIER-PREMISE", "POLICY-OVER-ROOT"}

    return {
        "rule": "post-D4 factor qualifies only after executable PROVEN-ROOT theorem",
        "current_members": admitted,
        "negative_controls": rejected,
        "selector_negative_control_count": len(controls["selectors"]),
        "status": "COHERENT-RESEARCH-CLASS",
        "semantic_domain_ratified": False,
    }


def width_from_population(n: int) -> int:
    if n <= 1:
        return 0
    return math.ceil(math.log2(n))


def constructor_attacks(membership):
    members = membership["current_members"]
    n = len(members)

    return [
        {
            "model": "E0-discovery-order-ordinal",
            "identity_rule": "assign ordinals in research discovery order",
            "current_population": n,
            "implied_width": width_from_population(n),
            "stable_under_new_root": False,
            "semantic_law_driven": False,
            "uses_human_or_history_authority": True,
            "proof_address_dependency": False,
            "verdict": "TABLE-RELOCATION",
            "reason": (
                "chronology becomes identity authority; adding/reordering roots can "
                "renumber existing identities"
            ),
        },
        {
            "model": "E1-display-label-sort",
            "identity_rule": "sort roots by human/research label and number them",
            "current_population": n,
            "implied_width": width_from_population(n),
            "stable_under_new_root": False,
            "semantic_law_driven": False,
            "uses_human_or_history_authority": True,
            "proof_address_dependency": False,
            "verdict": "TABLE-RELOCATION",
            "reason": "surface/research names become canonical identity authority",
        },
        {
            "model": "E2-population-minimum-width",
            "identity_rule": "choose ceil(log2(root-count)) bits and enumerate current roots",
            "current_population": n,
            "implied_width": width_from_population(n),
            "stable_under_new_root": False,
            "semantic_law_driven": False,
            "uses_human_or_history_authority": False,
            "proof_address_dependency": False,
            "verdict": "TABLE-RELOCATION",
            "reason": (
                "root count is accounting, not a semantic width theorem; width may change "
                "when another root is proved"
            ),
        },
        {
            "model": "E3-root-membership-only",
            "identity_rule": "PROVEN-ROOT predicate defines class membership only",
            "current_population": n,
            "implied_width": None,
            "stable_under_new_root": True,
            "semantic_law_driven": True,
            "uses_human_or_history_authority": False,
            "proof_address_dependency": False,
            "verdict": "MEMBERSHIP-ONLY",
            "reason": (
                "the predicate separates roots from carrier/policy factors but supplies "
                "no canonical binary number or exact width"
            ),
        },
        {
            "model": "E4-proof-derived-constructor",
            "identity_rule": "derive canonical binary identity from normalized proof/certificate",
            "current_population": n,
            "implied_width": None,
            "stable_under_new_root": "unknown",
            "semantic_law_driven": "candidate",
            "uses_human_or_history_authority": False,
            "proof_address_dependency": True,
            "verdict": "DEFER-TO-R4-#2669",
            "reason": (
                "this may avoid a flat table, but proof normalization/addressing is the "
                "separate #2669 lane and cannot be assumed here"
            ),
        },
    ]


def validate_attacks(attacks):
    table_models = [row for row in attacks if row["verdict"] == "TABLE-RELOCATION"]
    assert len(table_models) == 3
    assert all(row["semantic_law_driven"] is False for row in table_models)

    membership = next(row for row in attacks if row["model"] == "E3-root-membership-only")
    assert membership["implied_width"] is None
    assert membership["verdict"] == "MEMBERSHIP-ONLY"

    proof = next(row for row in attacks if row["model"] == "E4-proof-derived-constructor")
    assert proof["verdict"] == "DEFER-TO-R4-#2669"

    return {
        "ROOT-DOMAIN": "TABLE-RELOCATION-UNDER-CURRENT-EVIDENCE",
        "MEMBERSHIP-PREDICATE": "COHERENT-RESEARCH-CLASS",
        "EXACT-WIDTH": "UNKNOWN",
        "COORDINATE": "UNPLACED",
        "NEW-DOMAIN-RATIFIED": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    controls = load_controls()
    membership = membership_control(controls)
    attacks = constructor_attacks(membership)
    final = validate_attacks(attacks)

    result = {
        "schema": "independent-root-domain-attack/v1",
        "issue": "#2668",
        "phase": "SENS-DERIVATION",
        "membership": membership,
        "constructor_attacks": attacks,
        "relations": {
            "R3-automorphism": "merged #2681 proves lawless one-root exact domain is table relocation",
            "D5": "non-local-exit independently ineligible under #2616/#2670",
            "D6": "unresolved; free/overlay frontier is not membership evidence",
            "selectors": "generated children remain in selector family/domain law",
            "carrier_policy_factors": "explicitly excluded from root membership",
            "transport": "mechanism only; framing cannot select semantic width",
        },
        "handoff": {
            "#2662": "membership law alone is insufficient; exact identity constructor remains missing",
            "#2669": "E4 proof-derived constructor is delegated, not assumed",
        },
        "final": final,
        "guards": [
            "root count != bit width",
            "research order != identity",
            "human label != identity",
            "membership predicate != binary coordinate",
            "transport width != semantic-domain theorem",
            "proof-address model belongs to #2669",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = f"""# Independent root-domain attack — #2668

Current verdict:

- ROOT-DOMAIN = **{final['ROOT-DOMAIN']}**
- MEMBERSHIP-PREDICATE = **{final['MEMBERSHIP-PREDICATE']}**
- EXACT-WIDTH = **{final['EXACT-WIDTH']}**
- COORDINATE = **{final['COORDINATE']}**

What survives:
- a non-tabular research membership predicate: executable PROVEN-ROOT status;
- current member set = non-local-exit only;
- carrier premises, policy-over-root factors and generated selectors remain outside.

What fails:
- merged #2681 automorphism: a lawless one-root exact domain -> TABLE-RELOCATION;
- discovery-order numbering -> TABLE-RELOCATION;
- label-sorted numbering -> TABLE-RELOCATION;
- width from current root count -> TABLE-RELOCATION / numerology.

What remains missing:
- an internal root-domain law that breaks the #2681 width/coordinate symmetries;
- a canonical binary identity constructor that earns exact width without names,
  chronology, current population, free capacity, or a hidden table.

A proof-derived constructor is deliberately delegated to #2669.
"""
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
