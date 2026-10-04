#!/usr/bin/env python3
"""#3085 — coordinate-independent D6 set-lattice witness.

Research-only. Stable resident handles are semantic research identities.
CURRENT coordinates and human names are diagnostics only and do not enter
the law proof or geometry conclusion.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
from typing import FrozenSet, Iterable

SET_DOMAIN = "finite-set/lattice/v1"
ORDER_DOMAIN = "exact-number/total-order-lattice/control-v1"

MEET_RESIDENT = "sr-svxqxmwqfxrj"
JOIN_RESIDENT = "sr-kugyrdnvubfp"

UNIVERSE = frozenset({"a", "b", "c"})


def powerset(items: Iterable[str]) -> list[FrozenSet[str]]:
    seq = tuple(sorted(items))
    out: list[FrozenSet[str]] = []
    for width in range(len(seq) + 1):
        for combo in itertools.combinations(seq, width):
            out.append(frozenset(combo))
    return out


SETS = powerset(UNIVERSE)


def meet(a: FrozenSet[str], b: FrozenSet[str]) -> FrozenSet[str]:
    return a & b


def join(a: FrozenSet[str], b: FrozenSet[str]) -> FrozenSet[str]:
    return a | b


def member(x: str, value: FrozenSet[str]) -> int:
    return 1 if x in value else 0


def normalized_list_set(items: list[str]) -> FrozenSet[str]:
    """Projection helper only: order/duplicates are erased before set semantics."""
    return frozenset(items)


def assert_set_lattice() -> dict[str, int]:
    counts = {
        "commutativity_cases": 0,
        "associativity_cases": 0,
        "idempotence_cases": 0,
        "absorption_cases": 0,
        "identity_cases": 0,
        "annihilator_cases": 0,
        "membership_cases": 0,
        "projection_controls": 0,
    }

    for a in SETS:
        assert meet(a, a) == a
        assert join(a, a) == a
        counts["idempotence_cases"] += 2

        assert meet(a, UNIVERSE) == a
        assert join(a, frozenset()) == a
        counts["identity_cases"] += 2

        assert meet(a, frozenset()) == frozenset()
        assert join(a, UNIVERSE) == UNIVERSE
        counts["annihilator_cases"] += 2

        for b in SETS:
            assert meet(a, b) == meet(b, a)
            assert join(a, b) == join(b, a)
            counts["commutativity_cases"] += 2

            assert meet(a, join(a, b)) == a
            assert join(a, meet(a, b)) == a
            counts["absorption_cases"] += 2

            for x in sorted(UNIVERSE):
                assert member(x, meet(a, b)) == (member(x, a) & member(x, b))
                assert member(x, join(a, b)) == (member(x, a) | member(x, b))
                counts["membership_cases"] += 2

            for c in SETS:
                assert meet(meet(a, b), c) == meet(a, meet(b, c))
                assert join(join(a, b), c) == join(a, join(b, c))
                counts["associativity_cases"] += 2

    # Duplicate/order controls. These establish the mathematical set carrier,
    # not any particular runtime list-order convention.
    projection_pairs = [
        (["a", "b", "a"], ["b", "a"]),
        (["c", "a", "b", "c"], ["b", "c", "a"]),
        (["a", "a"], ["a"]),
        ([], []),
    ]
    for left, right in projection_pairs:
        assert normalized_list_set(left) == normalized_list_set(right)
        counts["projection_controls"] += 1

    return counts


def assert_false_controls() -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []

    a = frozenset({"a"})
    b = frozenset({"b"})
    assert meet(a, b) != join(a, b)
    controls.append({
        "control": "meet-equals-join",
        "status": "REFUTED",
        "counterexample": {
            "a": sorted(a),
            "b": sorted(b),
            "meet": sorted(meet(a, b)),
            "join": sorted(join(a, b)),
        },
    })

    # Deliberately false identity assignment: empty set is not meet identity.
    assert meet(a, frozenset()) != a
    controls.append({
        "control": "empty-is-meet-identity",
        "status": "REFUTED",
        "counterexample": {
            "a": sorted(a),
            "meet_with_empty": sorted(meet(a, frozenset())),
        },
    })

    return controls


def assert_order_lattice_control() -> dict[str, object]:
    values = (-2, -1, 0, 1, 2)
    checked = 0

    for a in values:
        assert min(a, a) == a
        assert max(a, a) == a
        for b in values:
            assert min(a, b) == min(b, a)
            assert max(a, b) == max(b, a)
            assert min(a, max(a, b)) == a
            assert max(a, min(a, b)) == a
            for c in values:
                assert min(min(a, b), c) == min(a, min(b, c))
                assert max(max(a, b), c) == max(a, max(b, c))
                checked += 2

    # Same abstract lattice signature, deliberately distinct semantic domains.
    set_object = {"domain": SET_DOMAIN, "value": ["a"]}
    order_object = {"domain": ORDER_DOMAIN, "value": 1}
    assert set_object["domain"] != order_object["domain"]

    return {
        "same_abstract_signature": [
            "commutative",
            "associative",
            "idempotent",
            "absorption",
        ],
        "order_cases": checked,
        "set_domain": SET_DOMAIN,
        "order_domain": ORDER_DOMAIN,
        "semantic_domain_equal": False,
        "cross_domain_apply": "DOMAIN-MISMATCH",
    }


def relation_record(counts: dict[str, int], false_controls, cross_control) -> dict[str, object]:
    return {
        "schema": "d6-multilaw-relation/v1",
        "authority": "research-only",
        "parent": "#3077",
        "issue": "#3085",
        "stable_resident_ids": [MEET_RESIDENT, JOIN_RESIDENT],
        "diagnostic_projection": {
            MEET_RESIDENT: "INTERSECTION",
            JOIN_RESIDENT: "UNION",
        },
        "relation_type": "LATTICE",
        "carrier_domain": SET_DOMAIN,
        "semantic_equations": {
            "meet": "A ∩ B",
            "join": "A ∪ B",
            "commutativity": "x⋀y=y⋀x; x⋁y=y⋁x",
            "associativity": "(x⋀y)⋀z=x⋀(y⋀z); (x⋁y)⋁z=x⋁(y⋁z)",
            "idempotence": "x⋀x=x; x⋁x=x",
            "absorption": "x⋀(x⋁y)=x; x⋁(x⋀y)=x",
            "identity": "x⋀U=x; x⋁∅=x",
            "annihilator": "x⋀∅=∅; x⋁U=U",
            "membership": "m(e,A∩B)=m(e,A)∧m(e,B); m(e,A∪B)=m(e,A)∨m(e,B)",
        },
        "partiality": "total-on-explicit-finite-set-carrier",
        "result_domain": SET_DOMAIN,
        "proof_witness": {
            "universe_cardinality": len(UNIVERSE),
            "carrier_values": len(SETS),
            "exhaustive_counts": counts,
        },
        "representation_policy": {
            "duplicate_policy": "erased-by-mathematical-set-projection",
            "order_policy": "erased-by-mathematical-set-projection",
            "runtime_list_order_claim": "UNKNOWN/NOT-USED",
            "runtime_duplicate_claim": "UNKNOWN/NOT-USED",
        },
        "negative_controls": false_controls,
        "cross_domain_control": cross_control,
        "geometry": {
            "classification": "RELATION-ONLY",
            "fixes_absolute_coordinates": False,
            "fixes_adjacency": False,
            "fixes_orientation": False,
            "leaves_translation_permutation_symmetry": True,
            "coordinate_theorem_status": "UNKNOWN",
            "current_adjacency_authority": 0,
        },
        "status": "BOUNDED-CONFIRMED",
        "non_conclusions": [
            "set-lattice laws do not imply one-bit adjacency",
            "shared lattice signature does not merge set and numeric-order domains",
            "mathematical set normalization does not specify runtime list ordering",
            "CURRENT coordinates are not evidence",
            "no production remap is proposed",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    counts = assert_set_lattice()
    false_controls = assert_false_controls()
    cross_control = assert_order_lattice_control()
    record = relation_record(counts, false_controls, cross_control)

    (args.out / "relation.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = []
    for law in (
        "commutativity",
        "associativity",
        "idempotence",
        "absorption",
        "identity",
        "annihilator",
        "membership",
    ):
        rows.append({
            "stable_resident_a": MEET_RESIDENT,
            "stable_resident_b": JOIN_RESIDENT,
            "relation_type": "LATTICE",
            "law": law,
            "carrier_domain": SET_DOMAIN,
            "semantic_status": "BOUNDED-CONFIRMED",
            "geometry_status": "RELATION-ONLY",
            "current_bits_used": False,
        })

    with (args.out / "relation.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    report = [
        "# D6 set-lattice witness — #3085",
        "",
        f"Stable resident A: `{MEET_RESIDENT}`",
        f"Stable resident B: `{JOIN_RESIDENT}`",
        "",
        f"Carrier: all **{len(SETS)}** subsets of a {len(UNIVERSE)}-element universe.",
        "",
        "Confirmed exhaustively:",
        "- commutativity;",
        "- associativity;",
        "- idempotence;",
        "- absorption;",
        "- identity and annihilator laws;",
        "- membership semantics.",
        "",
        "Representation boundary:",
        "duplicate/order variation is erased by the explicit mathematical-set projection;",
        "no runtime list-order or duplicate-preservation behavior is inferred.",
        "",
        "Cross-domain firewall:",
        "numeric MIN/MAX satisfies the same abstract lattice signature on its own carrier,",
        "but Number-order and finite-set domains remain distinct; cross-domain use is DOMAIN-MISMATCH.",
        "",
        "Geometry status: **RELATION-ONLY**.",
        "No adjacency, orientation, or absolute coordinate theorem is claimed.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
