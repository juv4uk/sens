#!/usr/bin/env python3
"""#3729 — NEG/ABS × reciprocal-involution D8 research witness.

Research only. No D8 resident is admitted or made callable.

Finite exact-Q carrier:
- every distinct reduced rational n/d;
- n in -8..8 excluding 0;
- d in 1..8;
- exact fractions only.

The candidate axes are:
  operation   = NEG | ABS
  reciprocal  = identity | RECIP

The witness requires RECIP to be an independently observable involution
that commutes with both current D6 operations. A deliberate sign-negation
control must collapse to only three global function tables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"
D3_SELECTOR_ROOTS = ("011", "100")


def load_d6_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coordinate for coordinate, name in doc["residents"].items()}
    assert by_name["NEG"] == "010010"
    assert by_name["ABS"] == "010011"
    assert by_name["RECIP"] == "010110"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "neg": by_name["NEG"],
        "abs": by_name["ABS"],
        "recip": by_name["RECIP"],
    }


def corpus() -> list[Fraction]:
    values = {
        Fraction(n, d)
        for n in range(-8, 9)
        if n != 0
        for d in range(1, 9)
    }
    out = sorted(values)
    assert len(out) == 86
    assert Fraction(0, 1) not in out
    return out


def neg(x: Fraction) -> Fraction:
    return -x


def absolute(x: Fraction) -> Fraction:
    return abs(x)


def reciprocal(x: Fraction) -> Fraction:
    assert x != 0
    return Fraction(x.denominator, x.numerator)


def neg_recip(x: Fraction) -> Fraction:
    return neg(reciprocal(x))


def abs_recip(x: Fraction) -> Fraction:
    return absolute(reciprocal(x))


def selector_d8_candidates() -> set[str]:
    d6_parents = {
        root + "".join(suffix)
        for root in D3_SELECTOR_ROOTS
        for suffix in product("01", repeat=3)
    }
    assert len(d6_parents) == 16
    out = {
        parent + "".join(suffix)
        for parent in d6_parents
        for suffix in product("01", repeat=2)
    }
    assert len(out) == 64
    return out


def coordinate_gauge(d6: dict[str, object]) -> dict[str, object]:
    parent = str(d6["neg"])
    sibling = str(d6["abs"])
    family = {parent + suffix for suffix in ("00", "01", "10", "11")}
    assert family.isdisjoint(selector_d8_candidates())

    return {
        "d6_parent": parent,
        "d6_known_sibling": sibling,
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_a": {
            "order": ["operation", "reciprocal"],
            "corners": {
                "00": "neg",
                "01": "neg_recip",
                "10": "abs",
                "11": "abs_recip",
            },
        },
        "axis_order_b": {
            "order": ["reciprocal", "operation"],
            "corners": {
                "00": "neg",
                "01": "abs",
                "10": "neg_recip",
                "11": "abs_recip",
            },
        },
        "invariants": {
            parent + "00": "NEG / lower-domain duplicate",
            parent + "11": "ABS∘RECIP / generated nonzero-Q candidate",
        },
        "middle_gauge_orbit": {
            "coordinates": [parent + "01", parent + "10"],
            "meanings": [
                "ABS / lower-domain duplicate",
                "NEG∘RECIP / generated nonzero-Q candidate",
            ],
            "rule": "swapping axis order swaps only the middle corners",
        },
    }


def truth_table(fn, cases: list[Fraction]) -> tuple[str, ...]:
    return tuple(str(fn(x)) for x in cases)


def run() -> dict[str, object]:
    d6 = load_d6_authority()
    cases = corpus()
    total = len(cases)

    reciprocal_involution = sum(reciprocal(reciprocal(x)) == x for x in cases)
    neg_commutes = sum(neg(reciprocal(x)) == reciprocal(neg(x)) for x in cases)
    abs_commutes = sum(
        absolute(reciprocal(x)) == reciprocal(absolute(x))
        for x in cases
    )

    operation_observable_base = sum(neg(x) != absolute(x) for x in cases)
    operation_observable_recip = sum(
        neg_recip(x) != abs_recip(x)
        for x in cases
    )
    reciprocal_observable_neg = sum(neg(x) != neg_recip(x) for x in cases)
    reciprocal_observable_abs = sum(absolute(x) != abs_recip(x) for x in cases)

    functions = {
        "neg": neg,
        "abs": absolute,
        "neg_recip": neg_recip,
        "abs_recip": abs_recip,
    }
    tables = {name: truth_table(fn, cases) for name, fn in functions.items()}
    pairwise_distinct = {
        f"{a} != {b}": tables[a] != tables[b]
        for a, b in combinations(functions, 2)
    }

    # Strong negative control: use input sign-negation instead of RECIP.
    # ABS(-x) == ABS(x), so one entire axis corner collapses.
    collapsed = {
        "neg": truth_table(neg, cases),
        "abs": truth_table(absolute, cases),
        "neg_after_input_neg": tuple(str(neg(neg(x))) for x in cases),
        "abs_after_input_neg": tuple(str(absolute(neg(x))) for x in cases),
    }
    collapsed_unique_tables = len(set(collapsed.values()))

    assert reciprocal_involution == total
    assert neg_commutes == total
    assert abs_commutes == total
    assert operation_observable_base > 0
    assert operation_observable_recip > 0
    assert reciprocal_observable_neg > 0
    assert reciprocal_observable_abs > 0
    assert all(pairwise_distinct.values())
    assert collapsed_unique_tables == 3

    gauge = coordinate_gauge(d6)
    parent = str(d6["neg"])

    return {
        "schema": "d8-neg-abs-recip/v1",
        "status": "PRODUCT-CANDIDATE-NONZERO-Q",
        "authority": {
            "d6_neg_abs_recip": "#3393 / #3334 / #3356 / #3366",
            "d6_source": d6,
            "d8": "#3281 research",
            "task": "#3729",
        },
        "corpus": {
            "numerator_min": -8,
            "numerator_max": 8,
            "numerator_zero_excluded": True,
            "denominator_min": 1,
            "denominator_max": 8,
            "distinct_reduced_nonzero_q": total,
        },
        "algebraic_laws": {
            "reciprocal_involution": "RECIP(RECIP(x)) = x, x != 0",
            "neg_commutation": "NEG(RECIP(x)) = RECIP(NEG(x)), x != 0",
            "abs_commutation": "ABS(RECIP(x)) = RECIP(ABS(x)), x != 0",
        },
        "witness": {
            "reciprocal_involution_pass": reciprocal_involution,
            "neg_commutes_with_recip_pass": neg_commutes,
            "abs_commutes_with_recip_pass": abs_commutes,
            "operation_axis_observable_base_cases": operation_observable_base,
            "operation_axis_observable_recip_cases": operation_observable_recip,
            "reciprocal_axis_observable_neg_cases": reciprocal_observable_neg,
            "reciprocal_axis_observable_abs_cases": reciprocal_observable_abs,
            "four_functions_pairwise_distinct": all(pairwise_distinct.values()),
            "pairwise_distinct_details": pairwise_distinct,
        },
        "negative_control": {
            "axis": "input sign-negation",
            "expected_collapse": "ABS(NEG(x)) = ABS(x)",
            "unique_global_function_tables": collapsed_unique_tables,
            "status": "PARTIAL-COLLAPSE",
        },
        "semantic_corners": {
            "neg": "current D6 parent semantics; lower-domain duplicate",
            "abs": "current D6 sibling semantics; lower-domain duplicate",
            "neg_recip": "generated nonzero-Q semantic candidate",
            "abs_recip": "generated nonzero-Q semantic candidate",
        },
        "coordinate_gauge": gauge,
        "result": {
            "generated_novel_semantics": 2,
            "invariant_coordinate_candidate": parent + "11",
            "invariant_coordinate_meaning": "ABS∘RECIP",
            "gauge_orbit_for_neg_recip": [parent + "01", parent + "10"],
            "orientation_theorem_missing": True,
        },
        "non_conclusions": [
            "No D8 resident is admitted or callable.",
            "The candidate is restricted to the nonzero exact-rational protocol.",
            "NEG∘RECIP absolute middle coordinate is unresolved.",
            "The current D6 ABS duplicate does not earn a D8 resident.",
            "Zero is outside the protocol; no division-by-zero coercion is introduced.",
            "No D7 ancestry or historical D8 donor is used.",
        ],
    }


def render(report: dict[str, object]) -> str:
    w = report["witness"]
    n = report["negative_control"]
    g = report["coordinate_gauge"]
    r = report["result"]
    total = report["corpus"]["distinct_reduced_nonzero_q"]
    return "\n".join([
        "# D8 NEG/ABS × reciprocal witness — #3729",
        "",
        f"Finite exact-Q corpus: {total} distinct reduced nonzero rationals.",
        "",
        "Positive witnesses:",
        f"- RECIP involution: {w['reciprocal_involution_pass']}/{total}",
        f"- NEG commutes with RECIP: {w['neg_commutes_with_recip_pass']}/{total}",
        f"- ABS commutes with RECIP: {w['abs_commutes_with_recip_pass']}/{total}",
        f"- operation axis observable at base: {w['operation_axis_observable_base_cases']} cases",
        f"- operation axis observable after RECIP: {w['operation_axis_observable_recip_cases']} cases",
        f"- reciprocal axis observable with NEG fixed: {w['reciprocal_axis_observable_neg_cases']} cases",
        f"- reciprocal axis observable with ABS fixed: {w['reciprocal_axis_observable_abs_cases']} cases",
        f"- four functionals pairwise distinct: {w['four_functions_pairwise_distinct']}",
        "",
        "Negative control:",
        f"- {n['axis']} -> {n['unique_global_function_tables']} unique global tables",
        f"- status: {n['status']}",
        "",
        "Coordinate/gauge:",
        f"- D6 anchor: {g['d6_parent']} (NEG)",
        f"- family: {' '.join(g['d8_family_coordinates'])}",
        f"- selector collision: {g['selector_collision']}",
        f"- invariant 11 candidate: {r['invariant_coordinate_candidate']} = ABS∘RECIP",
        f"- NEG∘RECIP gauge orbit: {' / '.join(r['gauge_orbit_for_neg_recip'])}",
        "",
        "Research result: **PRODUCT-CANDIDATE-NONZERO-Q**.",
        "",
        "No D8 admission follows from this witness.",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    report = run()
    text = render(report)

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "witness.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
