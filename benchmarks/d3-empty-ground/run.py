#!/usr/bin/env python3
"""#3176 — EMPTY structural-ground law + exhaustive D3 placement audit.

Research-only.  The semantic witness and the coordinate audit are deliberately
separate:

1. prove currently admitted EMPTY relations without using D3 coordinates;
2. ask whether those typed relations force the absolute coordinate 000.

The placement diagnostic exhausts all 8! D3 bijections.  Its score is only the
sum of Hamming distances on explicitly declared typed interaction edges.  It is
NOT semantic authority and gives no credit to the human intuition "empty=zero".
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROLES = ("EMPTY", "QUOTE", "ATOM", "COND", "CONS", "CAR", "CDR", "EQ")
CURRENT = {
    "EMPTY": 0b000,
    "QUOTE": 0b001,
    "ATOM": 0b010,
    "COND": 0b011,
    "CONS": 0b100,
    "CAR": 0b101,
    "CDR": 0b110,
    "EQ": 0b111,
}

YES = ("D1", 1)
NO = ("D1", 0)
EMPTY = ("EMPTY",)


@dataclass(frozen=True)
class Pair:
    first: Any
    rest: Any


def is_atom(value: Any) -> bool:
    # Current exact-domain law: every non-pair structural value, including
    # EMPTY, is an atom.
    return not isinstance(value, Pair)


def atom_pred(value: Any):
    return YES if is_atom(value) else NO


def eq_pred(left: Any, right: Any):
    # D3:111 is partial outside its admitted atom domain.
    if not is_atom(left) or not is_atom(right):
        return EMPTY
    return YES if left == right else NO


def cons(first: Any, rest: Any) -> Pair:
    return Pair(first, rest)


def car(value: Any):
    if not isinstance(value, Pair):
        raise TypeError("CAR requires a pair")
    return value.first


def cdr(value: Any):
    if not isinstance(value, Pair):
        raise TypeError("CDR requires a pair")
    return value.rest


def to_py_list(value: Any) -> list[Any]:
    out = []
    cursor = value
    while isinstance(cursor, Pair):
        out.append(cursor.first)
        cursor = cursor.rest
    if cursor != EMPTY:
        raise TypeError("proper list required")
    return out


def from_py_list(values: Iterable[Any]):
    out: Any = EMPTY
    for value in reversed(list(values)):
        out = Pair(value, out)
    return out


def append(left: Any, right: Any):
    if left == EMPTY:
        return right
    if not isinstance(left, Pair):
        raise TypeError("APPEND requires a proper list on the left")
    return Pair(left.first, append(left.rest, right))


def reverse(value: Any):
    values = to_py_list(value)
    return from_py_list(reversed(values))


def length(value: Any) -> int:
    return len(to_py_list(value))


def member(needle: Any, value: Any):
    for item in to_py_list(value):
        if item == needle:
            return YES
    return NO


def cond(clauses: list[tuple[Any, Any]]):
    for test, result in clauses:
        if test == YES:
            return result
        if test == NO or test == EMPTY:
            continue
        raise TypeError("exact COND accepts only D1 YES/NO or structural EMPTY")
    return EMPTY


def semantic_witnesses() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    x, y = ("ATOM", "x"), ("ATOM", "y")
    xs = from_py_list([x, y])
    singleton = cons(x, EMPTY)

    rows = [
        {
            "family": "PREDICATE-GROUND",
            "relation": "ATOM(EMPTY)=YES",
            "class": "GROUND",
            "pass": atom_pred(EMPTY) == YES,
            "independent_fact": "empty-is-atom-ground",
        },
        {
            "family": "PREDICATE-GROUND",
            "relation": "EQ(EMPTY,EMPTY)=YES",
            "class": "GROUND",
            "pass": eq_pred(EMPTY, EMPTY) == YES,
            "independent_fact": "empty-is-atom-ground",
        },
        {
            "family": "CONSTRUCTOR-BASE",
            "relation": "CONS(x,EMPTY)=singleton(x)",
            "class": "CONSTRUCTOR-BASE",
            "pass": singleton == from_py_list([x]),
            "independent_fact": "proper-list-base",
        },
        {
            "family": "CONSTRUCTOR-BASE",
            "relation": "CAR(CONS(x,EMPTY))=x",
            "class": "CONSTRUCTOR-BASE",
            "pass": car(singleton) == x,
            "independent_fact": "proper-list-base",
        },
        {
            "family": "CONSTRUCTOR-BASE",
            "relation": "CDR(CONS(x,EMPTY))=EMPTY",
            "class": "TERMINATOR",
            "pass": cdr(singleton) == EMPTY,
            "independent_fact": "proper-list-base",
        },
        {
            "family": "LIST-IDENTITY",
            "relation": "APPEND(EMPTY,xs)=xs",
            "class": "IDENTITY",
            "pass": append(EMPTY, xs) == xs,
            "independent_fact": "append-empty-identity",
        },
        {
            "family": "LIST-IDENTITY",
            "relation": "APPEND(xs,EMPTY)=xs",
            "class": "IDENTITY",
            "pass": append(xs, EMPTY) == xs,
            "independent_fact": "append-empty-identity",
        },
        {
            "family": "LIST-FIXEDPOINT",
            "relation": "REVERSE(EMPTY)=EMPTY",
            "class": "FIXED-POINT",
            "pass": reverse(EMPTY) == EMPTY,
            "independent_fact": "reverse-empty-fixedpoint",
        },
        {
            "family": "LIST-FIXEDPOINT",
            "relation": "REVERSE(REVERSE(xs))=xs",
            "class": "FIXED-POINT",
            "pass": reverse(reverse(xs)) == xs,
            "independent_fact": "reverse-involution",
        },
        {
            "family": "GROUND-MEASURE",
            "relation": "LENGTH(EMPTY)=0",
            "class": "GROUND",
            "pass": length(EMPTY) == 0,
            "independent_fact": "length-ground",
        },
        {
            "family": "SEARCH-TERMINATOR",
            "relation": "MEMBER(x,EMPTY)=NO",
            "class": "TERMINATOR",
            "pass": member(x, EMPTY) == NO,
            "independent_fact": "search-empty-terminator",
        },
        {
            "family": "CONTROL-BOUNDARY",
            "relation": "COND(EMPTY,...;YES,right)=right",
            "class": "NO-WITNESS",
            "pass": cond([(EMPTY, "wrong"), (YES, "right")]) == "right",
            "independent_fact": "empty-control-force",
        },
        {
            "family": "CONTROL-BOUNDARY",
            "relation": "COND exhaustion=EMPTY",
            "class": "CONTROL-BOUNDARY",
            "pass": cond([(NO, "wrong"), (EMPTY, "wrong2")]) == EMPTY,
            "independent_fact": "empty-control-force",
        },
        {
            "family": "TRUTH-SEPARATION",
            "relation": "EMPTY!=D1:NO",
            "class": "NO-WITNESS",
            "pass": EMPTY != NO,
            "independent_fact": "empty-not-false",
        },
        {
            "family": "PARTIAL-EQ",
            "relation": "EQ(pair,x)=EMPTY",
            "class": "NO-WITNESS",
            "pass": eq_pred(singleton, x) == EMPTY,
            "independent_fact": "eq-partial-outside-atom-domain",
        },
    ]
    assert all(row["pass"] for row in rows)

    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        family = grouped.setdefault(
            row["family"],
            {
                "family": row["family"],
                "witnesses": 0,
                "independent_facts": set(),
                "classes": set(),
            },
        )
        family["witnesses"] += 1
        family["independent_facts"].add(row["independent_fact"])
        family["classes"].add(row["class"])

    serializable = {}
    for name, row in grouped.items():
        serializable[name] = {
            "family": name,
            "witnesses": row["witnesses"],
            "independent_fact_count": len(row["independent_facts"]),
            "independent_facts": sorted(row["independent_facts"]),
            "classes": sorted(row["classes"]),
        }
    return rows, serializable


# Placement diagnostic.  These are typed interaction edges among D3 residents,
# not independent semantic facts and not a theorem that Hamming distance should
# be minimized.  They let #2150 ask a controlled geometric question.
EDGE_FAMILIES: dict[str, tuple[tuple[str, str], ...]] = {
    "PREDICATE-GROUND": (
        ("EMPTY", "ATOM"),
        ("EMPTY", "EQ"),
    ),
    "CONSTRUCTOR-BASE": (
        ("EMPTY", "CONS"),
        ("CONS", "CAR"),
        ("CONS", "CDR"),
    ),
    "CONTROL-BOUNDARY": (
        ("EMPTY", "COND"),
        ("ATOM", "COND"),
        ("EQ", "COND"),
    ),
}


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def placement_cost(placement: dict[str, int], active_families=None) -> int:
    families = EDGE_FAMILIES if active_families is None else {
        k: EDGE_FAMILIES[k] for k in active_families
    }
    return sum(
        hamming(placement[a], placement[b])
        for edges in families.values()
        for a, b in edges
    )


def placements():
    for coords in itertools.permutations(range(8)):
        yield dict(zip(ROLES, coords, strict=True))


def bits(value: int) -> str:
    return format(value, "03b")


def exhaustive(active_families=None, constrain_selectors=False):
    records = []
    for placement in placements():
        if constrain_selectors and (
            placement["CAR"] != CURRENT["CAR"]
            or placement["CDR"] != CURRENT["CDR"]
        ):
            continue
        records.append((placement_cost(placement, active_families), placement))
    return records


def best_by_role_coordinate(records, role: str):
    out = {}
    for coord in range(8):
        scores = [score for score, p in records if p[role] == coord]
        out[bits(coord)] = min(scores) if scores else None
    return out


def best_by_resident_at_zero(records):
    return {
        role: min(score for score, p in records if p[role] == 0)
        for role in ROLES
    }


def summarize_records(records, current=CURRENT):
    scores = [score for score, _ in records]
    current_score = placement_cost(current)
    lower = sum(score < current_score for score in scores)
    equal = sum(score == current_score for score in scores)
    minimum = min(scores)
    optima = [p for score, p in records if score == minimum]

    empty_opt = Counter(bits(p["EMPTY"]) for p in optima)
    histogram = dict(sorted(Counter(scores).items()))
    return {
        "placements": len(records),
        "minimum_cost": minimum,
        "optimum_count": len(optima),
        "current_cost": current_score,
        "current_rank": 1 + lower,
        "strictly_better_than_current": lower,
        "tied_with_current": equal,
        "mean_cost": statistics.mean(scores),
        "median_cost": statistics.median(scores),
        "score_histogram": {str(k): v for k, v in histogram.items()},
        "best_cost_by_EMPTY_coordinate": best_by_role_coordinate(records, "EMPTY"),
        "optimum_count_by_EMPTY_coordinate": {
            bits(coord): empty_opt.get(bits(coord), 0) for coord in range(8)
        },
        "best_cost_by_resident_fixed_at_000": best_by_resident_at_zero(records),
    }


def xor_translation_invariance() -> dict[str, Any]:
    seed = CURRENT
    score = placement_cost(seed)
    checks = []
    for mask in range(8):
        moved = {role: coord ^ mask for role, coord in seed.items()}
        moved_score = placement_cost(moved)
        checks.append({
            "xor_mask": bits(mask),
            "score": moved_score,
            "preserved": moved_score == score,
            "EMPTY_coordinate": bits(moved["EMPTY"]),
        })
    assert all(row["preserved"] for row in checks)
    return {
        "theorem": "pairwise Hamming-distance score is invariant under global XOR translation",
        "checks": checks,
        "consequence": (
            "without an independent absolute-coordinate/orientation law, "
            "no resident can be forced to 000 by this diagnostic"
        ),
    }


def remove_one_family_sensitivity():
    out = []
    families = tuple(EDGE_FAMILIES)
    for removed in families:
        active = tuple(x for x in families if x != removed)
        records = exhaustive(active_families=active)
        summary = summarize_records(records)
        out.append({
            "removed_family": removed,
            "active_families": list(active),
            "minimum_cost": summary["minimum_cost"],
            "best_cost_by_EMPTY_coordinate": summary["best_cost_by_EMPTY_coordinate"],
            "zero_forced": len(set(summary["best_cost_by_EMPTY_coordinate"].values())) > 1
                and min(
                    k for k, v in summary["best_cost_by_EMPTY_coordinate"].items()
                    if v == min(x for x in summary["best_cost_by_EMPTY_coordinate"].values() if x is not None)
                ) == "000",
        })
    # The important calibration is equality of best EMPTY score over all 8 cube
    # translations, not the helper boolean above.
    for row in out:
        values = [v for v in row["best_cost_by_EMPTY_coordinate"].values() if v is not None]
        assert len(set(values)) == 1
        row["absolute_EMPTY_coordinate_forced"] = False
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    witness_rows, law_families = semantic_witnesses()

    records = exhaustive()
    summary = summarize_records(records)

    constrained = exhaustive(constrain_selectors=True)
    constrained_summary = summarize_records(constrained)

    translation = xor_translation_invariance()
    sensitivity = remove_one_family_sensitivity()

    # Strong anti-numerology calibration from the exhaustive set.
    assert summary["placements"] == 40320
    assert summary["minimum_cost"] == 9
    assert summary["optimum_count"] == 96
    assert set(summary["best_cost_by_EMPTY_coordinate"].values()) == {9}
    assert set(summary["optimum_count_by_EMPTY_coordinate"].values()) == {12}
    assert set(summary["best_cost_by_resident_fixed_at_000"].values()) == {9}
    assert summary["current_cost"] == 11
    assert summary["strictly_better_than_current"] == 672
    assert summary["tied_with_current"] == 2496

    assert constrained_summary["placements"] == 720
    assert constrained_summary["minimum_cost"] == 9
    assert constrained_summary["optimum_count"] == 4
    assert constrained_summary["current_rank"] == 21

    # EMPTY@000 is consistent with some optimums but not uniquely derived.
    empty000_optima = sum(
        score == summary["minimum_cost"] and placement["EMPTY"] == 0
        for score, placement in records
    )
    assert empty000_optima == 12

    placement_rows = []
    for score, placement in records:
        placement_rows.append({
            "score": score,
            **{role: bits(placement[role]) for role in ROLES},
            "is_current": placement == CURRENT,
            "is_global_optimum": score == summary["minimum_cost"],
        })

    with (args.out / "semantic-witnesses.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(witness_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(witness_rows)

    with (args.out / "placements.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(placement_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(placement_rows)

    artifact = {
        "schema": "d3-empty-ground-law/v1",
        "authority": "research-only",
        "semantic_result": {
            "status": "BOUNDED-CONFIRMED",
            "EMPTY": "structural EMPTY / NO-WITNESS",
            "not_equal_to_D1_NO": True,
            "witness_count": len(witness_rows),
            "law_families": law_families,
        },
        "placement_diagnostic": {
            "metric": "sum of Hamming distances over typed D3 interaction edges",
            "edges_by_family": EDGE_FAMILIES,
            "semantic_authority": False,
            "unconstrained_8_factorial": summary,
            "selector_positive_control_CAR_101_CDR_110": constrained_summary,
            "xor_translation": translation,
            "remove_one_family": sensitivity,
        },
        "absolute_EMPTY_000_hypothesis": {
            "status": "NOT-FORCED / GAUGE-UNDERDETERMINED",
            "globally_optimal_placements_with_EMPTY_000": empty000_optima,
            "globally_optimal_placements_total": summary["optimum_count"],
            "best_score_is_same_for_every_EMPTY_coordinate": True,
            "best_score_is_same_for_every_resident_at_000": True,
            "explicit_EMPTY_000_premise_effect": (
                "filters the optimum set; it does not derive the premise"
            ),
        },
        "production_boundary": {
            "current_ratified_EMPTY_coordinate": "000",
            "research_changes_production": False,
            "interpretation": (
                "current placement remains production authority; this experiment "
                "does not derive its absolute address from ground semantics alone"
            ),
        },
        "non_conclusions": [
            "Hamming adjacency is a diagnostic, not semantic evidence by itself",
            "unique structural ground does not imply numeric zero without an absolute coordinate law",
            "selector anchors in the positive-control run are external constraints",
            "list-library witnesses do not become D3 placement edges automatically",
            "EMPTY is never identified with D1:NO",
        ],
    }

    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D3 EMPTY structural-ground / placement audit — #3176",
        "",
        "Semantic result: **BOUNDED-CONFIRMED structural ground**.",
        f"Executable semantic witnesses: **{len(witness_rows)}**.",
        f"Independent law families recorded: **{len(law_families)}**.",
        "D1:NO and structural EMPTY remain distinct.",
        "",
        "## Unconstrained 8! placement diagnostic",
        "",
        f"- placements: **{summary['placements']}**;",
        f"- minimum interaction cost: **{summary['minimum_cost']}**;",
        f"- optimal placements: **{summary['optimum_count']}**;",
        f"- current-map cost: **{summary['current_cost']}**;",
        f"- placements strictly better than current under this diagnostic: **{summary['strictly_better_than_current']}**;",
        f"- current rank: **{summary['current_rank']} / {summary['placements']}**.",
        "",
        "EMPTY coordinate calibration:",
        "- best cost is **9 at every coordinate 000..111**;",
        "- every EMPTY coordinate appears in **12** global optima;",
        "- fixing any one of the eight residents at 000 still permits best cost **9**.",
        "",
        "Therefore absolute placement result: **EMPTY=000 is NOT FORCED** by the",
        "coordinate-independent ground/interaction laws under this cube diagnostic.",
        "The 3-bit cube is XOR-translation symmetric: pairwise Hamming relations",
        "cannot choose an absolute origin without an additional proved coordinate law.",
        "",
        "## Selector-positive-control run",
        "",
        "With CAR=101 and CDR=110 externally fixed:",
        f"- placements: **{constrained_summary['placements']}**;",
        f"- minimum cost: **{constrained_summary['minimum_cost']}**;",
        f"- current rank: **{constrained_summary['current_rank']} / {constrained_summary['placements']}**.",
        "",
        "In that constrained run EMPTY=000 is among the best coordinates, but it",
        "ties another coordinate; the preference comes from the external selector",
        "anchors plus the diagnostic graph, not from EMPTY-ground semantics alone.",
        "",
        "## Interpretation",
        "",
        "**EMPTY is strongly meaningful as structural ground/no-witness.  Its current",
        "000 coordinate remains ratified production placement, but this experiment",
        "does not derive the absolute address 000.**",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
