#!/usr/bin/env python3
"""#3663 — bounded ANY/ALL × predicate-polarity D8 product witness.

Research-only. This script does not admit D8 residency or callability.

Semantic inputs:
- current D6 ANY/ALL dual law (#3370);
- current D6 coordinate authority (#3393);
- D8 remains research (#3281 / Contract 11.6).

Finite carrier:
- values {0,1};
- all four predicates over that carrier;
- all lists of lengths 0..5.

The second axis is not guessed. We exhaust all 24 permutations of the four
predicate truth tables and require both De Morgan equations. Exactly one
permutation must survive: pointwise predicate complement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import permutations, product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"
D3_SELECTOR_ROOTS = ("011", "100")

ALPHABET = (0, 1)
MAX_LENGTH = 5
PREDICATES = tuple(product((0, 1), repeat=2))


def load_d6_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    residents = doc["residents"]
    by_name = {name: coordinate for coordinate, name in residents.items()}
    assert len(residents) == 64
    assert by_name["ANY"] == "111100"
    assert by_name["ALL"] == "111101"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "any": by_name["ANY"],
        "all": by_name["ALL"],
    }


def bit_not(x: int) -> int:
    assert x in (0, 1)
    return 1 - x


def predicate_value(table: tuple[int, int], x: int) -> int:
    return table[x]


def predicate_not(table: tuple[int, int]) -> tuple[int, int]:
    return tuple(bit_not(x) for x in table)  # type: ignore[return-value]


def any_p(table: tuple[int, int], xs: tuple[int, ...]) -> int:
    return int(any(predicate_value(table, x) == 1 for x in xs))


def all_p(table: tuple[int, int], xs: tuple[int, ...]) -> int:
    return int(all(predicate_value(table, x) == 1 for x in xs))


def any_not_p(table: tuple[int, int], xs: tuple[int, ...]) -> int:
    return any_p(predicate_not(table), xs)


def all_not_p(table: tuple[int, int], xs: tuple[int, ...]) -> int:
    return all_p(predicate_not(table), xs)


def lists() -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []
    for length in range(MAX_LENGTH + 1):
        out.extend(product(ALPHABET, repeat=length))
    return out


def corpus() -> list[tuple[tuple[int, int], tuple[int, ...]]]:
    return [(table, xs) for table in PREDICATES for xs in lists()]


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


def permutation_control(cases) -> dict[str, object]:
    passing: list[tuple[int, ...]] = []
    for perm in permutations(range(len(PREDICATES))):
        transform = {PREDICATES[i]: PREDICATES[perm[i]] for i in range(4)}
        ok = True
        for table, xs in cases:
            transformed = transform[table]
            if all_p(transformed, xs) != bit_not(any_p(table, xs)):
                ok = False
                break
            if any_p(transformed, xs) != bit_not(all_p(table, xs)):
                ok = False
                break
        if ok:
            passing.append(perm)

    expected = tuple(
        PREDICATES.index(predicate_not(table))
        for table in PREDICATES
    )
    assert passing == [expected]
    return {
        "permutations_tested": 24,
        "passing": len(passing),
        "unique_passing_permutation": list(passing[0]),
        "expected_complement_permutation": list(expected),
    }


def coordinate_gauge(d6: dict[str, object]) -> dict[str, object]:
    parent = str(d6["any"])
    sibling = str(d6["all"])
    family = {parent + suffix for suffix in ("00", "01", "10", "11")}
    selectors = selector_d8_candidates()
    assert family.isdisjoint(selectors)

    quantifier_then_polarity = {
        "00": "any_p",
        "01": "any_not_p",
        "10": "all_p",
        "11": "all_not_p",
    }
    polarity_then_quantifier = {
        "00": "any_p",
        "01": "all_p",
        "10": "any_not_p",
        "11": "all_not_p",
    }

    return {
        "d6_parent": parent,
        "d6_known_sibling": sibling,
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_a": {
            "order": ["quantifier", "polarity"],
            "corners": quantifier_then_polarity,
        },
        "axis_order_b": {
            "order": ["polarity", "quantifier"],
            "corners": polarity_then_quantifier,
        },
        "invariants": {
            parent + "00": "ANY(p) / lower-domain duplicate",
            parent + "11": "ALL(NOT p) / generated novel candidate",
        },
        "orientation_gauge_orbit": {
            "coordinates": [parent + "01", parent + "10"],
            "meanings": [
                "ANY(NOT p) / generated novel candidate",
                "ALL(p) / lower-domain duplicate",
            ],
            "rule": "axis order swaps only the two middle corners",
        },
    }


def run() -> dict[str, object]:
    d6 = load_d6_authority()
    parent = str(d6["any"])
    cases = corpus()
    assert len(cases) == 252

    functions = {
        "any_p": any_p,
        "all_p": all_p,
        "any_not_p": any_not_p,
        "all_not_p": all_not_p,
    }
    tables = {
        name: tuple(fn(table, xs) for table, xs in cases)
        for name, fn in functions.items()
    }

    pairwise_distance = {
        f"{a} != {b}": sum(x != y for x, y in zip(tables[a], tables[b]))
        for i, a in enumerate(functions)
        for b in list(functions)[i + 1 :]
    }
    assert all(distance > 0 for distance in pairwise_distance.values())

    de_morgan_all_not = sum(
        all_not_p(table, xs) == bit_not(any_p(table, xs))
        for table, xs in cases
    )
    de_morgan_any_not = sum(
        any_not_p(table, xs) == bit_not(all_p(table, xs))
        for table, xs in cases
    )

    quantifier_observable_p = sum(
        any_p(table, xs) != all_p(table, xs)
        for table, xs in cases
    )
    quantifier_observable_not_p = sum(
        any_not_p(table, xs) != all_not_p(table, xs)
        for table, xs in cases
    )
    polarity_observable_any = sum(
        any_p(table, xs) != any_not_p(table, xs)
        for table, xs in cases
    )
    polarity_observable_all = sum(
        all_p(table, xs) != all_not_p(table, xs)
        for table, xs in cases
    )

    # Negative control 1: "polarity" is identity -> exact collapse.
    identity_polarity_collapses = sum(
        any_p(table, xs) == any_p(table, xs)
        and all_p(table, xs) == all_p(table, xs)
        for table, xs in cases
    )

    # Negative control 2: result-complement substituted for predicate-complement.
    # NOT(ANY(p)) is ALL(NOT p), not ANY(NOT p): wrong corner identity.
    result_complement_wrong_corner = sum(
        bit_not(any_p(table, xs)) != any_not_p(table, xs)
        for table, xs in cases
    )

    total = len(cases)
    assert de_morgan_all_not == total
    assert de_morgan_any_not == total
    assert quantifier_observable_p > 0
    assert quantifier_observable_not_p > 0
    assert polarity_observable_any > 0
    assert polarity_observable_all > 0
    assert identity_polarity_collapses == total
    assert result_complement_wrong_corner > 0

    # Coordinate-level product commutativity.
    quantifier_toggle = {"any": "all", "all": "any"}
    polarity_toggle = {"p": "not_p", "not_p": "p"}

    def apply_quantifier(state: tuple[str, str]) -> tuple[str, str]:
        q, p = state
        return (quantifier_toggle[q], p)

    def apply_polarity(state: tuple[str, str]) -> tuple[str, str]:
        q, p = state
        return (q, polarity_toggle[p])

    commutativity_checks = 0
    for q in ("any", "all"):
        for p in ("p", "not_p"):
            start = (q, p)
            assert apply_polarity(apply_quantifier(start)) == apply_quantifier(
                apply_polarity(start)
            )
            commutativity_checks += 1
    assert commutativity_checks == 4

    permutation = permutation_control(cases)
    gauge = coordinate_gauge(d6)

    return {
        "schema": "d8-any-all-polarity/v1",
        "status": "PRODUCT-CANDIDATE",
        "authority": {
            "d6_any_all": "#3393 / #3370",
            "d6_source": d6,
            "d8": "#3281 research",
            "task": "#3663",
        },
        "corpus": {
            "alphabet": list(ALPHABET),
            "all_predicate_truth_tables": [list(x) for x in PREDICATES],
            "max_list_length": MAX_LENGTH,
            "lists": len(lists()),
            "cases": total,
        },
        "witness": {
            "de_morgan_all_not_pass": de_morgan_all_not,
            "de_morgan_any_not_pass": de_morgan_any_not,
            "quantifier_observable_p_cases": quantifier_observable_p,
            "quantifier_observable_not_p_cases": quantifier_observable_not_p,
            "polarity_observable_any_cases": polarity_observable_any,
            "polarity_observable_all_cases": polarity_observable_all,
            "pairwise_truth_table_distance": pairwise_distance,
            "four_functionals_pairwise_distinct": all(
                distance > 0 for distance in pairwise_distance.values()
            ),
            "axis_commutativity_corners": commutativity_checks,
        },
        "uniqueness_control": permutation,
        "negative_controls": {
            "identity_polarity_collapse_cases": identity_polarity_collapses,
            "result_complement_wrong_corner_cases": result_complement_wrong_corner,
        },
        "semantic_corners": {
            "any_p": "current D6 parent semantics; lower-domain duplicate",
            "all_p": "current D6 sibling semantics; lower-domain duplicate",
            "any_not_p": "generated novel semantic candidate",
            "all_not_p": "generated novel semantic candidate",
        },
        "coordinate_gauge": gauge,
        "result": {
            "generated_novel_semantics": 2,
            "invariant_coordinate_candidate": parent + "11",
            "invariant_coordinate_meaning": "all_not_p",
            "gauge_orbit_for_any_not_p": [parent + "01", parent + "10"],
            "orientation_theorem_missing": True,
        },
        "non_conclusions": [
            "No D8 resident is admitted or callable.",
            "Generated semantics need not become primitive residents.",
            "ANY(NOT p) absolute middle coordinate is not fixed.",
            "No D7 semantic ancestry is used.",
            "No historical D8 donor row is input.",
        ],
    }


def render(report: dict[str, object]) -> str:
    w = report["witness"]
    u = report["uniqueness_control"]
    n = report["negative_controls"]
    g = report["coordinate_gauge"]
    r = report["result"]
    total = report["corpus"]["cases"]
    distances = w["pairwise_truth_table_distance"]

    lines = [
        "# D8 ANY/ALL × predicate polarity witness — #3663",
        "",
        f"Finite exhaustive corpus: {total} cases.",
        "All 4 predicates over {0,1}; all 63 lists of lengths 0..5.",
        "",
        "Positive witnesses:",
        f"- ALL(NOT p) = NOT ANY(p): {w['de_morgan_all_not_pass']}/{total}",
        f"- ANY(NOT p) = NOT ALL(p): {w['de_morgan_any_not_pass']}/{total}",
        f"- quantifier observable at p: {w['quantifier_observable_p_cases']} cases",
        f"- quantifier observable at NOT p: {w['quantifier_observable_not_p_cases']} cases",
        f"- polarity observable under ANY: {w['polarity_observable_any_cases']} cases",
        f"- polarity observable under ALL: {w['polarity_observable_all_cases']} cases",
        f"- four functionals pairwise distinct: {w['four_functionals_pairwise_distinct']}",
        "",
        "Pairwise truth-table distances:",
    ]
    lines.extend(f"- {name}: {distance}/{total}" for name, distance in distances.items())
    lines += [
        "",
        "Uniqueness control:",
        f"- predicate permutations tested: {u['permutations_tested']}",
        f"- permutations satisfying both De Morgan laws: **{u['passing']}**",
        "- the unique survivor is pointwise predicate complement.",
        "",
        "Negative controls:",
        f"- identity polarity collapses the axis on {n['identity_polarity_collapse_cases']}/{total} cases",
        f"- result-complement substituted for predicate-complement hits the wrong corner in {n['result_complement_wrong_corner_cases']} cases",
        "",
        "Coordinate/gauge result:",
        f"- D6 anchor: {g['d6_parent']} (ANY)",
        f"- D8 family: {' '.join(g['d8_family_coordinates'])}",
        f"- selector collision: {g['selector_collision']}",
        f"- invariant base duplicate: {g['d6_parent']}00 = ANY(p)",
        f"- invariant 11 candidate: {r['invariant_coordinate_candidate']} = ALL(NOT p)",
        f"- ANY(NOT p) remains in gauge orbit: {' / '.join(r['gauge_orbit_for_any_not_p'])}",
        "- the other middle corner is lower-domain ALL(p).",
        "",
        "Research result: **PRODUCT-CANDIDATE**.",
        "",
        "These are generated semantic candidates, not primitive admissions.",
        "",
    ]
    return "\n".join(lines)


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
