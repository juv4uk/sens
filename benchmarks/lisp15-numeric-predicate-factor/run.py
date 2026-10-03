#!/usr/bin/env python3
"""#2720 — factor historical LISP 1.5 numeric predicates before modern identity.

This executable witness consumes the primary-source ledger but does not place
any historical predicate into a Core domain.

It separates:
- exact order relations;
- historical tolerance policy;
- signed-zero representation policy;
- historical carrier classifiers;
- general structural equality.

Shared spelling is never identity authority.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "research" / "2709-lisp15-arithmetic-ledger.json"
EXACT_Q_CONTRACT = ROOT / "contracts" / "exact-q-binary-contract.lisp"

EPSILON = Fraction(3, 1_000_000)

NAMES = (
    "LESSP",
    "GREATERP",
    "ZEROP",
    "ONEP",
    "MINUSP",
    "NUMBERP",
    "FIXP",
    "FLOATP",
    "EQUAL",
)


@dataclass(frozen=True)
class HistoricalNumber:
    value: Fraction
    carrier: str  # fixed | float
    negative_zero: bool = False


def historical_zerop(x: HistoricalNumber) -> bool:
    return abs(x.value) <= EPSILON


def historical_onep(x: HistoricalNumber) -> bool:
    return abs(x.value - 1) <= EPSILON


def historical_equal_float(x: HistoricalNumber, y: HistoricalNumber) -> bool:
    return abs(x.value - y.value) < EPSILON


def historical_minusp(x: HistoricalNumber) -> bool:
    return x.negative_zero or x.value < 0


def bridge_exact_value(x: HistoricalNumber) -> Fraction:
    # Value-only bridge intentionally erases historical carrier and signed-zero
    # representation.  That erasure is the point of the counterexamples below.
    return Fraction(x.value)


def exact_q_sign_negative(x: Fraction) -> bool:
    return x < 0


def exact_q_zerop(x: Fraction) -> bool:
    return x == 0


def exact_q_onep(x: Fraction) -> bool:
    return x == 1


def decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "historical_row": "LESSP",
            "modern_domain": "exact-q-order + historical-float-order-adapter",
            "shared_law": "partial",
            "policy_carrier_delta": "exact fixed inputs commute; historical floating carrier remains separate",
            "derivable": "fixed branch yes from exact order",
            "binary_object": "UNPLACED",
            "relation": "BRIDGE-CANDIDATE",
        },
        {
            "historical_row": "GREATERP",
            "modern_domain": "exact-q-order + historical-float-order-adapter",
            "shared_law": "partial",
            "policy_carrier_delta": "exact fixed inputs commute; historical floating carrier remains separate",
            "derivable": "fixed branch yes from exact order",
            "binary_object": "UNPLACED",
            "relation": "BRIDGE-CANDIDATE",
        },
        {
            "historical_row": "ZEROP",
            "modern_domain": "historical-tolerance-policy over numeric magnitude",
            "shared_law": "no",
            "policy_carrier_delta": "historical <= 3e-6 policy; modern exact-Q zero is equality to 0",
            "derivable": "yes from magnitude/order + explicit epsilon policy",
            "binary_object": "UNPLACED",
            "relation": "DERIVED",
        },
        {
            "historical_row": "ONEP",
            "modern_domain": "historical-tolerance-policy over distance from 1",
            "shared_law": "no",
            "policy_carrier_delta": "historical <= 3e-6 policy; modern exact-Q one is equality to 1",
            "derivable": "yes from subtraction/magnitude/order + explicit epsilon policy",
            "binary_object": "UNPLACED",
            "relation": "DERIVED",
        },
        {
            "historical_row": "MINUSP",
            "modern_domain": "historical-signed-zero/carrier-representation-policy",
            "shared_law": "partial",
            "policy_carrier_delta": "historical -0 is negative; normalized exact-Q has one zero",
            "derivable": "ordinary negative values yes; historical -0 branch no after normalization",
            "binary_object": "UNPLACED",
            "relation": "DOMAIN-MISMATCH",
        },
        {
            "historical_row": "NUMBERP",
            "modern_domain": "historical-numeric-carrier classifier / typed bridge",
            "shared_law": "partial",
            "policy_carrier_delta": "historical fixed+floating classification precedes modern domain split",
            "derivable": "bridge can preserve a separate historical numeric-tag fact",
            "binary_object": "UNPLACED",
            "relation": "BRIDGE-CANDIDATE",
        },
        {
            "historical_row": "FIXP",
            "modern_domain": "historical-machine-carrier classifier",
            "shared_law": "no",
            "policy_carrier_delta": "fixed tag is erased by value-only exact-Q bridge",
            "derivable": "not from exact-Q value alone",
            "binary_object": "UNPLACED",
            "relation": "HISTORICAL-MECHANISM",
        },
        {
            "historical_row": "FLOATP",
            "modern_domain": "historical-machine-carrier classifier",
            "shared_law": "no",
            "policy_carrier_delta": "floating tag is erased by value-only exact-Q bridge",
            "derivable": "not from exact-Q value alone",
            "binary_object": "UNPLACED",
            "relation": "HISTORICAL-MECHANISM",
        },
        {
            "historical_row": "EQUAL",
            "modern_domain": "structural-equality + historical-floating-tolerance-policy",
            "shared_law": "no",
            "policy_carrier_delta": "general S-expression equality plus strict <3e-6 floating branch; not one numeric exact-Q law",
            "derivable": "branches factor separately",
            "binary_object": "UNPLACED",
            "relation": "DOMAIN-MISMATCH",
        },
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = ledger["rows"]
    selected = {
        row["historical_name"].upper(): row
        for row in rows
        if row["historical_name"].upper() in NAMES
    }
    assert tuple(sorted(selected)) == tuple(sorted(NAMES))
    assert len(selected) == 9

    exact_contract = EXACT_Q_CONTRACT.read_text(encoding="utf-8")
    assert "(approximation-policy . forbidden)" in exact_contract
    assert "(result-form . predicate-one-bit)" in exact_contract
    assert "(operand-domain . exact-rational-sequence)" in exact_contract

    # A — exact fixed order commutes with value bridge.
    fixed = [
        HistoricalNumber(Fraction(-3), "fixed"),
        HistoricalNumber(Fraction(0), "fixed"),
        HistoricalNumber(Fraction(2), "fixed"),
    ]
    order_checks = 0
    for left in fixed:
        for right in fixed:
            assert (left.value < right.value) == (
                bridge_exact_value(left) < bridge_exact_value(right)
            )
            assert (left.value > right.value) == (
                bridge_exact_value(left) > bridge_exact_value(right)
            )
            order_checks += 2

    # B — tolerance is an explicit policy and is observably not exact equality.
    at_epsilon = HistoricalNumber(EPSILON, "float")
    inside_epsilon = HistoricalNumber(EPSILON - Fraction(1, 10_000_000), "float")
    just_over_epsilon = HistoricalNumber(EPSILON + Fraction(1, 10_000_000), "float")
    assert historical_zerop(at_epsilon)
    assert historical_zerop(inside_epsilon)
    assert not historical_zerop(just_over_epsilon)
    assert not exact_q_zerop(bridge_exact_value(at_epsilon))

    one_at_boundary = HistoricalNumber(Fraction(1) + EPSILON, "float")
    assert historical_onep(one_at_boundary)
    assert not exact_q_onep(bridge_exact_value(one_at_boundary))

    equal_left = HistoricalNumber(Fraction(1), "float")
    equal_inside = HistoricalNumber(Fraction(1) + EPSILON - Fraction(1, 10_000_000), "float")
    equal_boundary = HistoricalNumber(Fraction(1) + EPSILON, "float")
    assert historical_equal_float(equal_left, equal_inside)
    assert not historical_equal_float(equal_left, equal_boundary)

    # C — historical signed zero is destroyed by exact-Q normalization.
    historical_negative_zero = HistoricalNumber(Fraction(0), "fixed", negative_zero=True)
    assert historical_minusp(historical_negative_zero)
    bridged_zero = bridge_exact_value(historical_negative_zero)
    assert bridged_zero == 0
    assert not exact_q_sign_negative(bridged_zero)

    # D — FIXP/FLOATP are not functions of mathematical value.
    fixed_one = HistoricalNumber(Fraction(1), "fixed")
    float_one = HistoricalNumber(Fraction(1), "float")
    assert fixed_one.value == float_one.value
    assert bridge_exact_value(fixed_one) == bridge_exact_value(float_one)
    assert fixed_one.carrier != float_one.carrier
    carrier_recoverable_from_exact_value = False

    # E — EQUAL has a nonnumeric structural branch, so the historical row
    # cannot be identified with the modern exact-Q numeric-equality predicate.
    sexpr_a = ("PAIR", ("ATOM", "a"), ("ATOM", "b"))
    sexpr_b = ("PAIR", ("ATOM", "a"), ("ATOM", "b"))
    assert sexpr_a == sexpr_b
    structural_equal_accepts_nonnumeric = True

    decisions = decision_rows()
    assert {row["historical_row"] for row in decisions} == set(NAMES)
    assert all(row["binary_object"] == "UNPLACED" for row in decisions)
    assert all(
        row["relation"]
        in {"DOMAIN-MISMATCH", "BRIDGE-CANDIDATE", "DERIVED", "HISTORICAL-MECHANISM"}
        for row in decisions
    )

    # Ledger spellings are evidence only.  Preserve exact historical details
    # used by the attacks so drift fails loudly.
    assert "3e-6" in selected["ZEROP"]["historical_behavior"]
    assert "3e-6" in selected["ONEP"]["historical_behavior"]
    assert "-0" in selected["MINUSP"]["historical_behavior"]
    assert "general S-expression equality" in selected["EQUAL"]["historical_behavior"]

    with (args.out / "predicate-factorization.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(decisions[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(decisions)

    artifact = {
        "schema": "lisp15-numeric-predicate-factorization/v1",
        "authority": "research-only",
        "phase": "STRUCTURAL-DISCOVERY",
        "source_rows": list(NAMES),
        "modern_exact_q_contract": {
            "approximation_policy": "forbidden",
            "result": "PredicateBit",
        },
        "attacks": {
            "fixed_order_bridge_checks": order_checks,
            "zerop_epsilon_boundary_differs_from_exact_zero": True,
            "onep_epsilon_boundary_differs_from_exact_one": True,
            "equal_float_boundary_is_strict": True,
            "historical_negative_zero_survives_minusp": True,
            "exact_q_normalization_preserves_negative_zero": False,
            "fixed_and_float_same_value_bridge_equal": True,
            "carrier_tag_recoverable_from_exact_value": carrier_recoverable_from_exact_value,
            "structural_equal_accepts_nonnumeric": structural_equal_accepts_nonnumeric,
        },
        "decision_rows": decisions,
        "counts": {
            relation: sum(row["relation"] == relation for row in decisions)
            for relation in (
                "DERIVED",
                "BRIDGE-CANDIDATE",
                "DOMAIN-MISMATCH",
                "HISTORICAL-MECHANISM",
            )
        },
        "d5_d6_allocations": 0,
        "non_conclusions": [
            "historical *T*/NIL is not modern PredicateBit identity authority",
            "a historical carrier tag is not an exact-Q value property",
            "tolerance policy is not exact equality",
            "shared spelling does not imply shared identity",
            "no historical predicate receives a Core coordinate here",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# LISP 1.5 numeric predicate factorization — #2720",
        "",
        "Nine historical rows factor into distinct modern classes before identity comparison.",
        "",
        f"Fixed exact-order bridge checks: **{order_checks}**",
        "",
        "Key counterexamples:",
        "- ZEROP accepts +3e-6 historically, while exact-Q zero equality rejects it;",
        "- ONEP accepts 1+3e-6 historically, while exact-Q equality-to-one rejects it;",
        "- floating EQUAL uses strict <3e-6, not <=;",
        "- historical MINUSP accepts signed -0, while normalized exact-Q has one unsigned zero value;",
        "- historical FIXP(1) and FLOATP(1.0) differ despite the value-only exact bridge mapping both to Q=1;",
        "- general EQUAL accepts nonnumeric S-expressions and therefore is not one numeric exact-Q predicate.",
        "",
        "Decision counts:",
    ]
    for relation, count in artifact["counts"].items():
        report.append(f"- {relation}: {count}")
    report += [
        "",
        "All binary objects remain **UNPLACED**.",
        "D5/D6 allocation delta: **0**.",
        "",
        "Principle: factor the law first; only then compare modern domains.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
