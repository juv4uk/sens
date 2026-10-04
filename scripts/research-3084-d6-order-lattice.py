#!/usr/bin/env python3
"""#3084 — coordinate-independent D6 order/lattice law witness.

Consumes opaque stable resident IDs from #3051 and tests semantic equations on
an exact-rational oracle. CURRENT coordinates are never used as evidence.
A finite-set lattice is included as a cross-domain anti-collapse control:
sharing one abstract lattice signature does not merge semantic carriers.
"""

from __future__ import annotations

import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge" / "d3-d8-stable-residents.json"
ARTIFACT = ROOT / "knowledge" / "d6-order-lattice-law.json"

STABLE = {
    "LEQ": "sr-yrkaryqscnkp",
    "GEQ": "sr-wtfwqasswbym",
    "MIN": "sr-bbzkrkjhkqts",
    "MAX": "sr-xpftsrbepvhk",
}

EXPECTED = {
    "LEQ": ("predicate", "non-strict less-than-or-equal (<=)"),
    "GEQ": ("predicate", "non-strict greater-than-or-equal (>=)"),
    "MIN": ("arithmetic", "extremum minimum of numbers"),
    "MAX": ("arithmetic", "extremum maximum of numbers"),
}


def q_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def exact_q_corpus() -> list[Fraction]:
    return sorted(
        {
            Fraction(numerator, denominator)
            for denominator in range(1, 7)
            for numerator in range(-12, 13)
        }
    )


def load_residents(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = {row["stable_resident_id"]: row for row in data["rows"]}
    selected = {}
    for name, stable_id in STABLE.items():
        row = rows[stable_id]
        role, behavior = EXPECTED[name]
        assert row["semantic_status"] == "RECOVERED"
        assert row["current_domain"] == "D6"
        assert row["semantic_role"] == role
        assert row["typed_behavior"] == behavior
        selected[name] = {
            "stable_resident_id": stable_id,
            "semantic_role": role,
            "typed_behavior": behavior,
        }
    return data, selected


def numeric_oracle(values: list[Fraction]):
    pairs = list(itertools.product(values, repeat=2))
    triples = list(itertools.product(values, repeat=3))

    checks = {
        "geq_leq_duality": all((a >= b) == (b <= a) for a, b in pairs),
        "min_commutativity": all(min(a, b) == min(b, a) for a, b in pairs),
        "max_commutativity": all(max(a, b) == max(b, a) for a, b in pairs),
        "min_idempotence": all(min(a, a) == a for a in values),
        "max_idempotence": all(max(a, a) == a for a in values),
        "absorption_min": all(min(a, max(a, b)) == a for a, b in pairs),
        "absorption_max": all(max(a, min(a, b)) == a for a, b in pairs),
        "leq_recovery_min": all((a <= b) == (min(a, b) == a) for a, b in pairs),
        "leq_recovery_max": all((a <= b) == (max(a, b) == b) for a, b in pairs),
        "geq_recovery_min": all((a >= b) == (min(a, b) == b) for a, b in pairs),
        "geq_recovery_max": all((a >= b) == (max(a, b) == a) for a, b in pairs),
        "min_associativity": all(
            min(min(a, b), c) == min(a, min(b, c))
            for a, b, c in triples
        ),
        "max_associativity": all(
            max(max(a, b), c) == max(a, max(b, c))
            for a, b, c in triples
        ),
        "min_monotonicity": all(
            not (a <= b) or min(a, c) <= min(b, c)
            for a, b, c in triples
        ),
        "max_monotonicity": all(
            not (a <= b) or max(a, c) <= max(b, c)
            for a, b, c in triples
        ),
    }
    assert all(checks.values())
    return {
        "oracle": "python.fractions.Fraction exact Q",
        "generator": {
            "numerator_min": -12,
            "numerator_max": 12,
            "denominator_min": 1,
            "denominator_max": 6,
            "deduplicate_reduced_values": True,
        },
        "value_count": len(values),
        "pair_count": len(pairs),
        "triple_count": len(triples),
        "min_value": q_text(values[0]),
        "max_value": q_text(values[-1]),
        "checks": checks,
    }


def set_lattice_control():
    universe = {0, 1, 2}
    values = [
        frozenset(combo)
        for size in range(4)
        for combo in itertools.combinations(universe, size)
    ]
    pairs = list(itertools.product(values, repeat=2))
    triples = list(itertools.product(values, repeat=3))
    checks = {
        "meet_commutativity": all((a & b) == (b & a) for a, b in pairs),
        "join_commutativity": all((a | b) == (b | a) for a, b in pairs),
        "meet_idempotence": all((a & a) == a for a in values),
        "join_idempotence": all((a | a) == a for a in values),
        "absorption_meet": all((a & (a | b)) == a for a, b in pairs),
        "absorption_join": all((a | (a & b)) == a for a, b in pairs),
        "meet_associativity": all(
            ((a & b) & c) == (a & (b & c))
            for a, b, c in triples
        ),
        "join_associativity": all(
            ((a | b) | c) == (a | (b | c))
            for a, b, c in triples
        ),
    }
    assert all(checks.values())
    return {
        "carrier": "finite powerset over 3 opaque elements",
        "value_count": len(values),
        "pair_count": len(pairs),
        "triple_count": len(triples),
        "checks": checks,
        "conclusion": (
            "same abstract lattice signature as numeric MIN/MAX; "
            "carrier/domain identity must remain distinct"
        ),
    }


def build_artifact(corpus_path: Path):
    corpus, selected = load_residents(corpus_path)
    numeric = numeric_oracle(exact_q_corpus())
    set_control = set_lattice_control()

    return {
        "schema": "d6-order-lattice-law/v1",
        "issue": "#3084",
        "parent_atlas": "#3077",
        "stable_corpus": {
            "schema": corpus["schema"],
            "corpus_hash": corpus["corpus_hash"],
            "stable_ids_are_research_handles_only": True,
            "current_coordinates_used_as_evidence": False,
        },
        "residents": selected,
        "runtime_status": {
            "d6_runtime_witness": "NOT-AUDITED",
            "exact_number_runtime_oracle": "PENDING-D6-ADMISSION",
            "predicate_result_domain_expected": "D1",
            "predicate_value_bridge": "#3076-MERGED",
        },
        "numeric_oracle": numeric,
        "relations": [
            {
                "law_id": "D6-ORDER-DUALITY-LEQ-GEQ",
                "relation_type": "DUALITY",
                "stable_resident_ids": [STABLE["LEQ"], STABLE["GEQ"]],
                "equation": "GEQ(a,b) = LEQ(b,a)",
                "carrier": "exact Number / Q",
                "result_domain": "D1",
                "geometry_status": "RELATION-ONLY",
                "solver_credit": 0,
            },
            {
                "law_id": "D6-NUMERIC-MEET-JOIN",
                "relation_type": "LATTICE",
                "stable_resident_ids": [STABLE["MIN"], STABLE["MAX"]],
                "equations": [
                    "MIN is commutative, associative, idempotent",
                    "MAX is commutative, associative, idempotent",
                    "MIN(a,MAX(a,b)) = a",
                    "MAX(a,MIN(a,b)) = a",
                    "MIN and MAX are monotone in the total numeric order",
                ],
                "carrier": "exact Number / Q",
                "geometry_status": "RELATION-ONLY",
                "solver_credit": 0,
            },
            {
                "law_id": "D6-ORDER-RECOVERED-FROM-EXTREMA",
                "relation_type": "ENTAILMENT",
                "stable_resident_ids": [
                    STABLE["LEQ"],
                    STABLE["GEQ"],
                    STABLE["MIN"],
                    STABLE["MAX"],
                ],
                "equations": [
                    "LEQ(a,b) iff MIN(a,b)=a iff MAX(a,b)=b",
                    "GEQ(a,b) iff MIN(a,b)=b iff MAX(a,b)=a",
                ],
                "carrier": "exact Number / Q",
                "result_domain": "D1 for LEQ/GEQ",
                "geometry_status": "RELATION-ONLY",
                "solver_credit": 0,
            },
        ],
        "cross_domain_falsifier": {
            "issue": "#3085",
            "control": set_control,
            "anti_collapse_law": (
                "equal lattice equations do not identify numeric MIN/MAX "
                "with set INTERSECTION/UNION"
            ),
            "geometry_status": "NO-GEOMETRY-CLAIM",
            "solver_credit": 0,
        },
        "geometry_conclusion": {
            "current_adjacency_used": False,
            "one_bit_axis_proved": False,
            "prefix_generator_proved": False,
            "neighborhood_bonus_allowed": False,
            "status": "RELATION-ONLY",
            "reason": (
                "semantic equations are proved in the oracle, but no coordinate "
                "economy theorem distinguishes a bit placement"
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, default=CORPUS)
    ap.add_argument("--artifact", type=Path, default=ARTIFACT)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    artifact = build_artifact(args.corpus)
    rendered = json.dumps(artifact, indent=2, sort_keys=True) + "\n"

    if args.write:
        args.artifact.write_text(rendered, encoding="utf-8")
        print(args.artifact)
        return 0

    current = args.artifact.read_text(encoding="utf-8")
    if current != rendered:
        raise SystemExit(
            "d6-order-lattice artifact drift: run "
            "python3 scripts/research-3084-d6-order-lattice.py --write"
        )

    print(
        f"d6-order-lattice: PASS "
        f"Q={artifact['numeric_oracle']['value_count']} "
        f"pairs={artifact['numeric_oracle']['pair_count']} "
        f"triples={artifact['numeric_oracle']['triple_count']} "
        "geometry=RELATION-ONLY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
