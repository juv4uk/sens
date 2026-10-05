#!/usr/bin/env python3
"""#3669 — cheap D8 second-axis collapse screen.

Research-only falsifier. No D8 coordinate is allocated here.

The screen tests several tempting second axes and rejects them when they are
invisible, dependent on the first family axis, or collapse one of four corners.
"""

from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FAMILIES_PATH = REPO / "knowledge" / "d6-v2-binary-law-families.json"


def load_families() -> dict[tuple[str, str], str]:
    doc = json.loads(FAMILIES_PATH.read_text(encoding="utf-8"))
    assert doc["schema"] == "d6-v2-binary-law-families/v1"
    out: dict[tuple[str, str], str] = {}
    for family in doc["families"]:
        members = tuple(family["members"])
        assert len(members) == 2
        out[members] = family["id"]
    return out


def all_lists(alphabet, max_length):
    out = []
    for length in range(max_length + 1):
        out.extend(product(alphabet, repeat=length))
    return out


def screen_length_reverse(families):
    key = ("LENGTH", "LENGTH-ONTO")
    assert key in families
    lists = all_lists((0, 1), 5)
    accs = tuple(range(-2, 3))

    length_invariant = sum(
        len(tuple(reversed(xs))) == len(xs)
        for xs in lists
    )
    onto_invariant = sum(
        acc + len(tuple(reversed(xs))) == acc + len(xs)
        for xs in lists
        for acc in accs
    )

    assert length_invariant == len(lists)
    assert onto_invariant == len(lists) * len(accs)

    return {
        "family_id": families[key],
        "members": list(key),
        "proposed_second_axis": "list-reversal",
        "status": "AXIS-INVISIBLE",
        "witness": {
            "lists": len(lists),
            "accumulators": len(accs),
            "length_invariant": length_invariant,
            "length_onto_invariant": onto_invariant,
        },
        "collapse_identity": "LENGTH(reverse(xs))=LENGTH(xs); LENGTH-ONTO(reverse(xs),a)=LENGTH-ONTO(xs,a)",
        "further_d8_work_on_this_axis": False,
    }


def screen_minmax_neg(families):
    key = ("MIN-LIST", "MAX-LIST")
    assert key in families
    lists = []
    for length in range(1, 5):
        lists.extend(product(range(-2, 3), repeat=length))

    min_to_max = 0
    max_to_min = 0
    for xs in lists:
        neg_xs = tuple(-x for x in xs)
        min_conjugated = -min(neg_xs)
        max_conjugated = -max(neg_xs)
        min_to_max += min_conjugated == max(xs)
        max_to_min += max_conjugated == min(xs)

    assert min_to_max == len(lists)
    assert max_to_min == len(lists)

    return {
        "family_id": families[key],
        "members": list(key),
        "proposed_second_axis": "numeric-negation-conjugation",
        "status": "AXIS-DEPENDENT",
        "witness": {
            "nonempty_lists": len(lists),
            "min_conjugates_to_max": min_to_max,
            "max_conjugates_to_min": max_to_min,
        },
        "collapse_identity": "NEG∘MIN∘NEG = MAX and NEG∘MAX∘NEG = MIN",
        "further_d8_work_on_this_axis": False,
    }


def screen_addsub_neg(families):
    key = ("ADD1", "SUB1")
    assert key in families
    xs = tuple(range(-32, 33))

    add_to_sub = sum(-((-x) + 1) == x - 1 for x in xs)
    sub_to_add = sum(-((-x) - 1) == x + 1 for x in xs)

    assert add_to_sub == len(xs)
    assert sub_to_add == len(xs)

    return {
        "family_id": families[key],
        "members": list(key),
        "proposed_second_axis": "numeric-negation-conjugation",
        "status": "AXIS-DEPENDENT",
        "witness": {
            "integers": len(xs),
            "add1_conjugates_to_sub1": add_to_sub,
            "sub1_conjugates_to_add1": sub_to_add,
        },
        "collapse_identity": "NEG∘ADD1∘NEG = SUB1 and NEG∘SUB1∘NEG = ADD1",
        "further_d8_work_on_this_axis": False,
    }


def screen_numeric_predicates_neg(families):
    key = ("INTEGERP", "RATIONALP")
    assert key in families

    values = sorted({
        Fraction(n, d)
        for n in range(-4, 5)
        for d in range(1, 5)
    })

    def integerp(x):
        return x.denominator == 1

    def rationalp(x):
        return isinstance(x, Fraction)

    integer_invariant = sum(integerp(-x) == integerp(x) for x in values)
    rational_invariant = sum(rationalp(-x) == rationalp(x) for x in values)

    assert integer_invariant == len(values)
    assert rational_invariant == len(values)

    return {
        "family_id": families[key],
        "members": list(key),
        "proposed_second_axis": "numeric-negation",
        "status": "AXIS-INVISIBLE",
        "witness": {
            "exact_rationals": len(values),
            "integerp_invariant": integer_invariant,
            "rationalp_invariant": rational_invariant,
        },
        "collapse_identity": "INTEGERP(-x)=INTEGERP(x); RATIONALP(-x)=RATIONALP(x)",
        "further_d8_work_on_this_axis": False,
    }


def screen_remainder_gcd_swap(families):
    key = ("REMAINDER", "GCD")
    assert key in families
    pairs = [(a, b) for a in range(1, 17) for b in range(1, 17)]

    funcs = {
        "remainder_ab": tuple(a % b for a, b in pairs),
        "gcd_ab": tuple(math.gcd(a, b) for a, b in pairs),
        "remainder_ba": tuple(b % a for a, b in pairs),
        "gcd_ba": tuple(math.gcd(b, a) for a, b in pairs),
    }
    unique_tables = len(set(funcs.values()))
    gcd_swap_equal = funcs["gcd_ab"] == funcs["gcd_ba"]
    remainder_swap_diff = sum(
        x != y for x, y in zip(funcs["remainder_ab"], funcs["remainder_ba"])
    )

    assert gcd_swap_equal
    assert remainder_swap_diff > 0
    assert unique_tables == 3

    return {
        "family_id": families[key],
        "members": list(key),
        "proposed_second_axis": "argument-swap",
        "status": "PARTIAL-COLLAPSE",
        "witness": {
            "positive_integer_pairs": len(pairs),
            "unique_corner_truth_tables": unique_tables,
            "gcd_swap_equal": gcd_swap_equal,
            "remainder_swap_differing_cases": remainder_swap_diff,
        },
        "collapse_identity": "GCD(a,b)=GCD(b,a), so two of four corners are identical",
        "further_d8_work_on_this_axis": False,
    }


def run():
    families = load_families()
    rows = [
        screen_length_reverse(families),
        screen_minmax_neg(families),
        screen_addsub_neg(families),
        screen_numeric_predicates_neg(families),
        screen_remainder_gcd_swap(families),
    ]
    assert all(row["status"] != "SURVIVES" for row in rows)

    return {
        "schema": "d8-collapse-screen/v1",
        "task": "#3669",
        "status": "FALSIFIER",
        "rows": rows,
        "summary": {
            "families_screened": len(rows),
            "survives": sum(row["status"] == "SURVIVES" for row in rows),
            "axis_invisible": sum(row["status"] == "AXIS-INVISIBLE" for row in rows),
            "axis_dependent": sum(row["status"] == "AXIS-DEPENDENT" for row in rows),
            "partial_collapse": sum(row["status"] == "PARTIAL-COLLAPSE" for row in rows),
        },
        "non_conclusions": [
            "A rejected axis does not prove the D6 family can never support another D8 axis.",
            "No D8 coordinate is allocated by this screen.",
            "No historical D8 donor row is used.",
        ],
    }


def render(report):
    s = report["summary"]
    lines = [
        "# D8 cheap second-axis collapse screen — #3669",
        "",
        f"Families screened: {s['families_screened']}",
        f"Surviving proposed axes: {s['survives']}",
        f"Axis-invisible: {s['axis_invisible']}",
        f"Axis-dependent: {s['axis_dependent']}",
        f"Partial collapse: {s['partial_collapse']}",
        "",
        "| family | proposed second axis | result | reason |",
        "|---|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {' / '.join(row['members'])} | {row['proposed_second_axis']} | "
            f"{row['status']} | {row['collapse_identity']} |"
        )
    lines += [
        "",
        "Result: **0/5 tempting axes survive**.",
        "",
        "This eliminates axes, not families. A family may still support a different",
        "independently proved second axis.",
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
        (args.out / "screen.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
