#!/usr/bin/env python3
"""#2527 — non-prefix representation falsifier for the D6 local lower bound.

Research-only.

The four binding-policy states are already witnessed as observationally distinct.
This experiment asks whether they can be represented canonically *without* the
local D4 DEFINE prefix.

Result scope:
- local parent+delta placement may still require D6;
- standalone representation width is a different question.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DONOR = ROOT / "scripts" / "research-2506-d6-binding-policy-generator.py"

PARENT_PREFIX = "0011"
SEMANTIC_STATES = (
    "DEFINE",
    "CURRENT_FAIL",
    "NEAREST_CREATE",
    "SETQ_CORE",
)
CODES_2BIT = ("00", "01", "10", "11")


def load_donor():
    spec = importlib.util.spec_from_file_location("d6_policy_2506_nonprefix", DONOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def min_binary_width(n_states: int) -> int:
    if n_states < 1:
        raise ValueError
    return math.ceil(math.log2(n_states)) if n_states > 1 else 0


def factor_preserving(mapping: dict[str, str]) -> bool:
    """Preserve the oriented product law from the fixed DEFINE parent.

    DEFINE is the no-refinement endpoint; SETQ_CORE is both refinements.
    The two one-axis semantic states may exchange coordinate-axis order, but
    arbitrary semantic-to-code table permutations are not factor coordinates.
    """
    if mapping["DEFINE"] != "00":
        return False
    if mapping["SETQ_CORE"] != "11":
        return False
    return {
        mapping["CURRENT_FAIL"],
        mapping["NEAREST_CREATE"],
    } == {"01", "10"}


def enumerate_permutations():
    rows = []
    for perm in itertools.permutations(CODES_2BIT):
        mapping = dict(zip(SEMANTIC_STATES, perm, strict=True))
        rows.append({
            "mapping": mapping,
            "factor_preserving": factor_preserving(mapping),
        })
    assert len(rows) == 24
    assert sum(row["factor_preserving"] for row in rows) == 2
    return rows


def quotient_certificate(policy: Any, donor: Any):
    active = []
    if policy.scope is donor.Scope.NEAREST:
        active.append("scope")
    if policy.miss is donor.Miss.FAIL:
        active.append("miss")
    return frozenset(active)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    donor = load_donor()
    square = {
        "DEFINE": donor.DEFINE,
        "CURRENT_FAIL": donor.CURRENT_FAIL,
        "NEAREST_CREATE": donor.NEAREST_CREATE,
        "SETQ_CORE": donor.SETQ_CORE,
    }

    signatures = {state: donor.signature(policy) for state, policy in square.items()}
    assert len(set(signatures.values())) == 4

    info_lower_bound = min_binary_width(len(signatures))
    assert info_lower_bound == 2
    assert (1 << 1) < len(signatures) <= (1 << 2)

    # Model 1: local ordered path under D4 DEFINE.
    canonical_factor_mapping = {
        "DEFINE": "00",
        "CURRENT_FAIL": "01",
        "NEAREST_CREATE": "10",
        "SETQ_CORE": "11",
    }

    local_mapping = {
        state: PARENT_PREFIX + canonical_factor_mapping[state]
        for state in SEMANTIC_STATES
    }
    assert all(len(code) == 6 for code in local_mapping.values())
    assert local_mapping["SETQ_CORE"] == "001111"

    # Model 2: standalone two-factor product coordinate. The semantic state
    # names remain bit-free; the encoder supplies the 2-bit coordinates.
    factor_mapping = dict(canonical_factor_mapping)
    assert len(set(factor_mapping.values())) == 4
    assert all(len(code) == 2 for code in factor_mapping.values())

    # Axis relabel swaps only the two one-axis coordinate assignments.
    axis_swapped = {
        "DEFINE": "00",
        "CURRENT_FAIL": "10",
        "NEAREST_CREATE": "01",
        "SETQ_CORE": "11",
    }
    assert factor_preserving(canonical_factor_mapping)
    assert factor_preserving(axis_swapped)
    assert canonical_factor_mapping != axis_swapped

    # Model 3: quotient commuting derivation paths by active-factor set.
    quotient = {
        state: quotient_certificate(policy, donor)
        for state, policy in square.items()
    }
    assert len(set(quotient.values())) == 4
    assert quotient["SETQ_CORE"] == frozenset({"scope", "miss"})
    scope_then_miss = frozenset(["scope", "miss"])
    miss_then_scope = frozenset(["miss", "scope"])
    assert scope_then_miss == miss_then_scope == quotient["SETQ_CORE"]

    # Model 4/5 permutation attack.
    permutations = enumerate_permutations()
    factor_preserving_count = sum(row["factor_preserving"] for row in permutations)
    table_dependent_count = len(permutations) - factor_preserving_count
    assert factor_preserving_count == 2
    assert table_dependent_count == 22

    models = [
        {
            "model": "local-ordered-path",
            "domain": "Core D4 DEFINE local refinement path",
            "printed_width": 6,
            "independent_axis_facts": 2,
            "mapping_table_rows": 0,
            "extra_structure": "D4 parent relation + ordered two-axis path",
            "derivation_order_invariant": False,
            "axis_relabel_target_invariant": True,
            "arbitrary_enumeration_dependency": False,
            "evidence_class": "semantic-law+coordinate-law",
            "decision": "VALID-LOCAL-D6",
        },
        {
            "model": "standalone-two-factor",
            "domain": "hypothetical BindingPolicyProduct-D2",
            "printed_width": 2,
            "independent_axis_facts": 2,
            "mapping_table_rows": 0,
            "extra_structure": "new explicit product-domain authority",
            "derivation_order_invariant": True,
            "axis_relabel_target_invariant": True,
            "arbitrary_enumeration_dependency": False,
            "evidence_class": "canonical-factor-coordinate-law",
            "decision": "VALID-STANDALONE-D2-DIFFERENT-DOMAIN",
        },
        {
            "model": "quotient-of-paths",
            "domain": "hypothetical BindingPolicyProduct-D2 quotient",
            "printed_width": 2,
            "independent_axis_facts": 2,
            "mapping_table_rows": 0,
            "extra_structure": "commutation/quotient law + product-domain authority",
            "derivation_order_invariant": True,
            "axis_relabel_target_invariant": True,
            "arbitrary_enumeration_dependency": False,
            "evidence_class": "semantic-law+canonical-factor-coordinate-law",
            "decision": "VALID-ORDER-INVARIANT-D2-DIFFERENT-DOMAIN",
        },
        {
            "model": "explicit-residue-root-table",
            "domain": "opaque four-state residue domain",
            "printed_width": 2,
            "independent_axis_facts": 2,
            "mapping_table_rows": 4,
            "extra_structure": "four explicit semantic-to-code rows",
            "derivation_order_invariant": True,
            "axis_relabel_target_invariant": False,
            "arbitrary_enumeration_dependency": True,
            "evidence_class": "accidental",
            "decision": "REPRESENTS-STATES-BUT-IMPORTS-TABLE-AUTHORITY",
        },
        {
            "model": "arbitrary-global-numbering",
            "domain": "unstructured 2-bit numbering",
            "printed_width": 2,
            "independent_axis_facts": 2,
            "mapping_table_rows": 4,
            "extra_structure": "arbitrary enumeration table",
            "derivation_order_invariant": False,
            "axis_relabel_target_invariant": False,
            "arbitrary_enumeration_dependency": True,
            "evidence_class": "accidental",
            "decision": "REJECT-AS-CANONICAL-WITHOUT-TABLE",
        },
    ]

    with (args.out / "model-tournament.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(models[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(models)

    perm_rows = []
    for row in permutations:
        m = row["mapping"]
        perm_rows.append({
            "map_DEFINE": m["DEFINE"],
            "map_CURRENT_FAIL": m["CURRENT_FAIL"],
            "map_NEAREST_CREATE": m["NEAREST_CREATE"],
            "map_SETQ_CORE": m["SETQ_CORE"],
            "factor_preserving": row["factor_preserving"],
            "requires_arbitrary_table_authority": not row["factor_preserving"],
        })
    with (args.out / "permutation-attack.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(perm_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(perm_rows)

    artifact = {
        "schema": "d6-nonprefix-falsifier/v1",
        "authority": "research-only",
        "semantic_state_count": 4,
        "semantic_signatures_distinct": 4,
        "information_lower_bound_bits": info_lower_bound,
        "local_parent_delta_result": {
            "parent": PARENT_PREFIX,
            "delta_axes": 2,
            "local_total_width": 6,
            "status": "D6-SUFFICIENT-AND-LOCAL-LOWER-BOUND-SURVIVES",
        },
        "standalone_representation_result": {
            "minimum_injective_binary_width": 2,
            "product_domain_possible": True,
            "requires_new_domain_authority": True,
            "status": "GLOBAL-D6-WIDTH-NOT-MINIMAL",
        },
        "quotient_result": {
            "scope_then_miss_equals_miss_then_scope": True,
            "semantic_target": sorted(quotient["SETQ_CORE"]),
            "reduces_independent_axis_count": False,
        },
        "permutation_attack": {
            "semantic_states_are_bit_free": True,
            "all_injective_2bit_numberings": 24,
            "oriented_parent_factor_preserving": factor_preserving_count,
            "arbitrary_table_dependent": table_dependent_count,
            "exact_intermediate_axis_orientation_forced": False,
        },
        "models": models,
        "decision": (
            "D6 is justified only under the local D4-parent + two-delta placement law; "
            "the four-state algebra itself needs only two standalone factor bits."
        ),
        "non_conclusions": [
            "standalone D2 product representation does not allocate a Core D2 binding-policy domain",
            "standalone D2 does not make SETQ a D2 Core resident",
            "two semantic axes are not reduced by shorter printed coordinates",
            "axis order/orientation of intermediate 01/10 is not forced",
            "no D6 residency or polarity is ratified",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D6 non-prefix representation falsifier — #2527",
        "",
        f"Observed semantic states: **{len(signatures)}**",
        f"Standalone binary information lower bound: **{info_lower_bound} bits**",
        "",
        "| model | printed width | mapping rows | evidence class | result |",
        "|---|---:|---:|---|---|",
    ]
    for row in models:
        report.append(
            f"| {row['model']} | {row['printed_width']} | "
            f"{row['mapping_table_rows']} | {row['evidence_class']} | "
            f"{row['decision']} |"
        )

    report += [
        "",
        "Permutation attack:",
        f"- all injective 2-bit numberings: {len(permutations)};",
        f"- anchored factor-preserving: {factor_preserving_count};",
        f"- arbitrary/table-dependent: {table_dependent_count}.",
        "",
        "Critical scope result:",
        "- D6 survives as the local D4 DEFINE + two independent deltas placement width;",
        "- D6 is **not** a global minimum for representing the four-state algebra;",
        "- a standalone D2 product domain can represent the same distinctions, but that is a different domain/authority decision;",
        "- no representation reduces the two independent semantic axes.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
