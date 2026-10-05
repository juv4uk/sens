#!/usr/bin/env python3
"""#3729 — NEG/ABS × RECIP D8 research witness on nonzero exact-Q.

Research-only. No D8 resident is admitted or made callable.

The two axes are:
  operation  = NEG | ABS
  reciprocal = identity | RECIP

The reciprocal axis is admitted only on nonzero exact rationals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"
D3_SELECTOR_ROOTS = ("011", "100")


def load_d6_authority():
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coord for coord, name in doc["residents"].items()}
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


def carrier():
    values = {
        Fraction(n, d)
        for n in range(-8, 9)
        if n != 0
        for d in range(1, 9)
    }
    out = tuple(sorted(values))
    assert len(out) == 86
    assert Fraction(0, 1) not in out
    return out


def neg(x: Fraction) -> Fraction:
    return -x


def abs_q(x: Fraction) -> Fraction:
    return abs(x)


def recip(x: Fraction) -> Fraction:
    assert x != 0
    return Fraction(1, 1) / x


def neg_recip(x: Fraction) -> Fraction:
    return neg(recip(x))


def abs_recip(x: Fraction) -> Fraction:
    return abs_q(recip(x))


def selector_d8_candidates():
    parents = {
        root + "".join(bits)
        for root in D3_SELECTOR_ROOTS
        for bits in product("01", repeat=3)
    }
    assert len(parents) == 16
    out = {
        parent + "".join(bits)
        for parent in parents
        for bits in product("01", repeat=2)
    }
    assert len(out) == 64
    return out


def coordinate_gauge(d6):
    parent = str(d6["neg"])
    sibling = str(d6["abs"])
    family = {parent + suffix for suffix in ("00", "01", "10", "11")}
    selectors = selector_d8_candidates()
    assert family.isdisjoint(selectors)

    return {
        "d6_parent": parent,
        "d6_known_sibling": sibling,
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_a": {
            "order": ["operation", "reciprocal"],
            "corners": {
                "00": "NEG",
                "01": "NEG∘RECIP",
                "10": "ABS",
                "11": "ABS∘RECIP",
            },
        },
        "axis_order_b": {
            "order": ["reciprocal", "operation"],
            "corners": {
                "00": "NEG",
                "01": "ABS",
                "10": "RECIP∘NEG",
                "11": "RECIP∘ABS",
            },
        },
        "invariants": {
            parent + "00": "NEG / lower-domain duplicate",
            parent + "11": "ABS∘RECIP / generated novel candidate",
        },
        "orientation_gauge_orbit": {
            "coordinates": [parent + "01", parent + "10"],
            "meanings": [
                "NEG∘RECIP / generated novel candidate",
                "ABS / lower-domain duplicate",
            ],
            "rule": "axis order swaps only the two middle corners",
        },
    }


def run():
    d6 = load_d6_authority()
    xs = carrier()
    total = len(xs)

    recip_involution = sum(recip(recip(x)) == x for x in xs)
    neg_commutes = sum(neg(recip(x)) == recip(neg(x)) for x in xs)
    abs_commutes = sum(abs_q(recip(x)) == recip(abs_q(x)) for x in xs)

    functions = {
        "NEG": neg,
        "ABS": abs_q,
        "NEG_RECIP": neg_recip,
        "ABS_RECIP": abs_recip,
    }
    tables = {
        name: tuple(fn(x) for x in xs)
        for name, fn in functions.items()
    }
    pairwise_distance = {
        f"{a} != {b}": sum(x != y for x, y in zip(tables[a], tables[b]))
        for i, a in enumerate(functions)
        for b in list(functions)[i + 1:]
    }

    op_observable_plain = sum(neg(x) != abs_q(x) for x in xs)
    op_observable_recip = sum(neg_recip(x) != abs_recip(x) for x in xs)
    recip_observable_neg = sum(neg(x) != neg_recip(x) for x in xs)
    recip_observable_abs = sum(abs_q(x) != abs_recip(x) for x in xs)

    assert recip_involution == total
    assert neg_commutes == total
    assert abs_commutes == total
    assert all(distance > 0 for distance in pairwise_distance.values())
    assert len(set(tables.values())) == 4
    assert op_observable_plain > 0
    assert op_observable_recip > 0
    assert recip_observable_neg > 0
    assert recip_observable_abs > 0

    # Negative control: using input NEG as the proposed second axis collapses
    # the ABS corner because ABS(NEG(x)) == ABS(x).
    bad_tables = {
        "NEG": tuple(neg(x) for x in xs),
        "ABS": tuple(abs_q(x) for x in xs),
        "NEG_NEG": tuple(neg(neg(x)) for x in xs),
        "ABS_NEG": tuple(abs_q(neg(x)) for x in xs),
    }
    bad_unique = len(set(bad_tables.values()))
    bad_abs_collapse = sum(abs_q(neg(x)) == abs_q(x) for x in xs)
    assert bad_unique == 3
    assert bad_abs_collapse == total

    gauge = coordinate_gauge(d6)
    parent = str(d6["neg"])

    return {
        "schema": "d8-neg-abs-recip/v1",
        "status": "PRODUCT-CANDIDATE-NONZERO-Q",
        "authority": {
            "d6_neg_abs": "#3334 / #3366 / #3393",
            "d6_recip": "#3356 / #3393",
            "d6_source": d6,
            "d8": "#3281 research",
            "task": "#3729",
        },
        "protocol": {
            "carrier": "exact rational",
            "zero_admitted": False,
            "reason": "RECIP is undefined at zero",
        },
        "corpus": {
            "numerator_range": [-8, 8],
            "denominator_range": [1, 8],
            "distinct_nonzero_reduced_rationals": total,
        },
        "witness": {
            "recip_involution_pass": recip_involution,
            "neg_recip_commutation_pass": neg_commutes,
            "abs_recip_commutation_pass": abs_commutes,
            "operation_observable_plain_cases": op_observable_plain,
            "operation_observable_recip_cases": op_observable_recip,
            "reciprocal_observable_neg_cases": recip_observable_neg,
            "reciprocal_observable_abs_cases": recip_observable_abs,
            "pairwise_truth_table_distance": pairwise_distance,
            "four_functionals_pairwise_distinct": True,
        },
        "negative_control": {
            "axis": "input NEG instead of RECIP",
            "unique_corner_tables": bad_unique,
            "abs_axis_collapse_cases": bad_abs_collapse,
            "status": "PARTIAL-COLLAPSE",
        },
        "semantic_corners": {
            "NEG": "current D6 parent semantics; lower-domain duplicate",
            "ABS": "current D6 sibling semantics; lower-domain duplicate",
            "NEG_RECIP": "generated novel semantic candidate",
            "ABS_RECIP": "generated novel semantic candidate",
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
            "The product protocol excludes zero.",
            "Generated meanings need not become primitives.",
            "NEG∘RECIP absolute middle coordinate is unresolved.",
            "No D7 ancestry or historical D8 donor is used.",
        ],
    }


def render(report):
    w = report["witness"]
    n = report["negative_control"]
    g = report["coordinate_gauge"]
    r = report["result"]
    total = report["corpus"]["distinct_nonzero_reduced_rationals"]

    lines = [
        "# D8 NEG/ABS × reciprocal involution — #3729",
        "",
        f"Finite exhaustive nonzero exact-Q corpus: {total} values.",
        "",
        f"- RECIP involution: {w['recip_involution_pass']}/{total}",
        f"- NEG/RECIP commute: {w['neg_recip_commutation_pass']}/{total}",
        f"- ABS/RECIP commute: {w['abs_recip_commutation_pass']}/{total}",
        f"- operation observable, plain: {w['operation_observable_plain_cases']} cases",
        f"- operation observable, reciprocal: {w['operation_observable_recip_cases']} cases",
        f"- reciprocal observable under NEG: {w['reciprocal_observable_neg_cases']} cases",
        f"- reciprocal observable under ABS: {w['reciprocal_observable_abs_cases']} cases",
        f"- four functionals pairwise distinct: {w['four_functionals_pairwise_distinct']}",
        "",
        "Negative control:",
        f"- input NEG as second axis -> {n['unique_corner_tables']} unique corners",
        f"- ABS(NEG x)=ABS(x): {n['abs_axis_collapse_cases']}/{total}",
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
    ]
    return "\n".join(lines)


def main():
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
