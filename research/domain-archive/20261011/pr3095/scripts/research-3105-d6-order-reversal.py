#!/usr/bin/env python3
"""#3105 — prove D6 NEG as shared order-reversal transform.

Semantic proof only. CURRENT bits are diagnostics, never evidence.
Geometry credit remains zero until #3099 finds a coordinate theorem that beats
matched conditional nulls.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge" / "d3-d8-stable-residents.json"
ARTIFACT = ROOT / "knowledge" / "d6-order-reversal-law.json"

STABLE = {
    "NEG": "sr-jksmnurxmrzb",
    "LEQ": "sr-yrkaryqscnkp",
    "GEQ": "sr-wtfwqasswbym",
    "MIN": "sr-bbzkrkjhkqts",
    "MAX": "sr-xpftsrbepvhk",
}

EXPECTED = {
    "NEG": ("arithmetic", "additive inverse negation (-x)"),
    "LEQ": ("predicate", "non-strict less-than-or-equal (<=)"),
    "GEQ": ("predicate", "non-strict greater-than-or-equal (>=)"),
    "MIN": ("arithmetic", "extremum minimum of numbers"),
    "MAX": ("arithmetic", "extremum maximum of numbers"),
}


def values() -> list[Fraction]:
    return sorted({
        Fraction(n, d)
        for d in range(1, 7)
        for n in range(-12, 13)
    })


def load_rows():
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    rows = {r["stable_resident_id"]: r for r in data["rows"]}
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
            "current_bits_diagnostic_only": row["current_bits"],
        }
    return data, selected


def build():
    corpus, selected = load_rows()
    xs = values()
    pairs = [(a, b) for a in xs for b in xs]

    checks = {
        "neg_involution": all(-(-a) == a for a in xs),
        "geq_via_neg_leq": all((a >= b) == ((-a) <= (-b)) for a, b in pairs),
        "leq_via_neg_geq": all((a <= b) == ((-a) >= (-b)) for a, b in pairs),
        "max_via_neg_min": all(max(a, b) == -min(-a, -b) for a, b in pairs),
        "min_via_neg_max": all(min(a, b) == -max(-a, -b) for a, b in pairs),
    }
    assert all(checks.values())

    false_control = all((a >= b) == ((-a) <= b) for a, b in pairs)
    assert not false_control

    return {
        "schema": "d6-order-reversal-law/v1",
        "issue": "#3105",
        "parents": ["#3095", "#3099", "#3077", "#3039"],
        "stable_corpus": {
            "schema": corpus["schema"],
            "corpus_hash": corpus["corpus_hash"],
            "current_coordinates_used_as_evidence": False,
        },
        "residents": selected,
        "semantic_transform": {
            "law_id": "D6-ORDER-REVERSAL-BY-NEG",
            "relation_type": "INVOLUTION+DUALITY+LATTICE-AUTOMORPHISM",
            "generator_resident": STABLE["NEG"],
            "affected_residents": [
                STABLE["LEQ"], STABLE["GEQ"], STABLE["MIN"], STABLE["MAX"]
            ],
            "equations": [
                "NEG(NEG(a)) = a",
                "GEQ(a,b) = LEQ(NEG(a),NEG(b))",
                "LEQ(a,b) = GEQ(NEG(a),NEG(b))",
                "MAX(a,b) = NEG(MIN(NEG(a),NEG(b)))",
                "MIN(a,b) = NEG(MAX(NEG(a),NEG(b)))",
            ],
        },
        "oracle": {
            "carrier": "python.fractions.Fraction exact Q",
            "value_count": len(xs),
            "pair_count": len(pairs),
            "checks": checks,
            "false_control_single_operand_negation": false_control,
        },
        "geometry": {
            "status": "RELATION-ONLY",
            "solver_credit": 0,
            "candidate_transform": "UNKNOWN",
            "required_next_gate": "#3099 matched conditional geometry search",
        },
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rendered = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if args.write:
        ARTIFACT.write_text(rendered, encoding="utf-8")
        print(ARTIFACT)
        return 0

    actual = ARTIFACT.read_text(encoding="utf-8")
    if actual != rendered:
        raise SystemExit(
            "d6-order-reversal artifact drift: run "
            "python3 scripts/research-3105-d6-order-reversal.py --write"
        )
    data = json.loads(actual)
    print(
        "d6-order-reversal: PASS "
        f"Q={data['oracle']['value_count']} "
        f"pairs={data['oracle']['pair_count']} "
        "geometry=RELATION-ONLY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
