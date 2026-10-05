#!/usr/bin/env python3
"""#3622 — bounded TAKE/DROP × edge product witness for D8 research.

Research-only. This script does not admit D8 residency or callability.

Semantic inputs:
- current D6 TAKE/DROP partition law (#3368);
- current D5 REVERSE law (#3305 / #3293 / #3379);
- D8 remains research under Contract 11.6 (#3572 / #3281).

The script tests whether two independently observable binary choices exist:
  mode: take vs drop
  edge: left vs right

Right-oriented forms are defined by REVERSE conjugation, not by donor names.
"""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

D6_PARENT = "110000"   # current D6 TAKE identity under #3393
D6_SIBLING = "110001"  # current D6 DROP identity under #3393
D3_SELECTOR_ROOTS = ("011", "100")

ALPHABET = (0, 1)
MAX_LENGTH = 5
N_SLACK = 2


def reverse(xs: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(reversed(xs))


def take_left(n: int, xs: tuple[int, ...]) -> tuple[int, ...]:
    return xs[: min(n, len(xs))]


def drop_left(n: int, xs: tuple[int, ...]) -> tuple[int, ...]:
    return xs[min(n, len(xs)) :]


def take_right(n: int, xs: tuple[int, ...]) -> tuple[int, ...]:
    return reverse(take_left(n, reverse(xs)))


def drop_right(n: int, xs: tuple[int, ...]) -> tuple[int, ...]:
    return reverse(drop_left(n, reverse(xs)))


def bad_take_right_missing_final_reverse(
    n: int, xs: tuple[int, ...]
) -> tuple[int, ...]:
    return take_left(n, reverse(xs))


def bad_drop_right_missing_final_reverse(
    n: int, xs: tuple[int, ...]
) -> tuple[int, ...]:
    return drop_left(n, reverse(xs))


def bad_drop_right_is_suffix(
    n: int, xs: tuple[int, ...]
) -> tuple[int, ...]:
    return take_right(n, xs)


def corpus() -> list[tuple[int, tuple[int, ...]]]:
    out: list[tuple[int, tuple[int, ...]]] = []
    for length in range(MAX_LENGTH + 1):
        for xs in product(ALPHABET, repeat=length):
            for n in range(length + N_SLACK + 1):
                out.append((n, xs))
    return out


def truth_table(fn, cases):
    return tuple(fn(n, xs) for n, xs in cases)


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


def coordinate_gauge() -> dict[str, object]:
    family = {D6_PARENT + suffix for suffix in ("00", "01", "10", "11")}
    selectors = selector_d8_candidates()
    assert family.isdisjoint(selectors)

    mode_then_edge = {
        "00": "take_left",
        "01": "take_right",
        "10": "drop_left",
        "11": "drop_right",
    }
    edge_then_mode = {
        "00": "take_left",
        "01": "drop_left",
        "10": "take_right",
        "11": "drop_right",
    }

    assert mode_then_edge["00"] == edge_then_mode["00"] == "take_left"
    assert mode_then_edge["11"] == edge_then_mode["11"] == "drop_right"
    assert {mode_then_edge["01"], mode_then_edge["10"]} == {
        edge_then_mode["01"],
        edge_then_mode["10"],
    } == {"take_right", "drop_left"}

    return {
        "d6_parent": D6_PARENT,
        "d6_known_sibling": D6_SIBLING,
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_a": {
            "order": ["mode", "edge"],
            "corners": mode_then_edge,
        },
        "axis_order_b": {
            "order": ["edge", "mode"],
            "corners": edge_then_mode,
        },
        "invariants": {
            D6_PARENT + "00": "take_left / lower-domain duplicate",
            D6_PARENT + "11": "drop_right / novel semantic candidate",
        },
        "orientation_gauge_orbit": {
            "coordinates": [D6_PARENT + "01", D6_PARENT + "10"],
            "meanings": ["take_right / novel semantic candidate", "drop_left / lower-domain duplicate"],
            "rule": "axis order swaps these two middle corners",
        },
    }


def run() -> dict[str, object]:
    cases = corpus()

    # Base algebraic witnesses.
    reverse_involution = sum(reverse(reverse(xs)) == xs for _, xs in cases)
    left_partition = sum(
        take_left(n, xs) + drop_left(n, xs) == xs
        for n, xs in cases
    )
    right_partition = sum(
        drop_right(n, xs) + take_right(n, xs) == xs
        for n, xs in cases
    )

    # Independent observability of both axes.
    edge_observable_take = sum(
        take_left(n, xs) != take_right(n, xs)
        for n, xs in cases
    )
    edge_observable_drop = sum(
        drop_left(n, xs) != drop_right(n, xs)
        for n, xs in cases
    )
    mode_observable_left = sum(
        take_left(n, xs) != drop_left(n, xs)
        for n, xs in cases
    )
    mode_observable_right = sum(
        take_right(n, xs) != drop_right(n, xs)
        for n, xs in cases
    )

    functions = {
        "take_left": take_left,
        "drop_left": drop_left,
        "take_right": take_right,
        "drop_right": drop_right,
    }
    tables = {name: truth_table(fn, cases) for name, fn in functions.items()}
    pairwise_distinct = {
        f"{a} != {b}": tables[a] != tables[b]
        for i, a in enumerate(functions)
        for b in list(functions)[i + 1 :]
    }

    # Negative controls.
    bad_missing_reverse_failures = sum(
        bad_drop_right_missing_final_reverse(n, xs)
        + bad_take_right_missing_final_reverse(n, xs)
        != xs
        for n, xs in cases
    )
    bad_suffix_drop_failures = sum(
        bad_drop_right_is_suffix(n, xs) + take_right(n, xs) != xs
        for n, xs in cases
    )

    # Product-axis commutativity at semantic-coordinate level:
    # toggling mode then edge reaches the same corner as edge then mode.
    square = {
        ("take", "left"): "take_left",
        ("drop", "left"): "drop_left",
        ("take", "right"): "take_right",
        ("drop", "right"): "drop_right",
    }
    mode_toggle = {"take": "drop", "drop": "take"}
    edge_toggle = {"left": "right", "right": "left"}

    def apply_mode(state: tuple[str, str]) -> tuple[str, str]:
        mode, edge = state
        return (mode_toggle[mode], edge)

    def apply_edge(state: tuple[str, str]) -> tuple[str, str]:
        mode, edge = state
        return (mode, edge_toggle[edge])

    commutativity_checks = 0
    for mode in ("take", "drop"):
        for edge in ("left", "right"):
            start = (mode, edge)
            mode_then_edge = apply_edge(apply_mode(start))
            edge_then_mode = apply_mode(apply_edge(start))
            assert mode_then_edge == edge_then_mode
            assert square[mode_then_edge] == square[edge_then_mode]
            commutativity_checks += 1

    total = len(cases)

    assert total == 447
    assert reverse_involution == total
    assert left_partition == total
    assert right_partition == total
    assert all(pairwise_distinct.values())
    assert edge_observable_take > 0
    assert edge_observable_drop > 0
    assert mode_observable_left > 0
    assert mode_observable_right > 0
    assert bad_missing_reverse_failures > 0
    assert bad_suffix_drop_failures > 0
    assert commutativity_checks == 4

    gauge = coordinate_gauge()

    return {
        "schema": "d8-take-drop-edge/v1",
        "status": "PRODUCT-CANDIDATE",
        "authority": {
            "d5_reverse": "#3305 / #3293 / #3379",
            "d6_take_drop": "#3393 / #3368",
            "d8": "#3281 research",
            "task": "#3622",
        },
        "definitions": {
            "take_right": "reverse(take_left(n, reverse(xs)))",
            "drop_right": "reverse(drop_left(n, reverse(xs)))",
        },
        "corpus": {
            "alphabet": list(ALPHABET),
            "max_length": MAX_LENGTH,
            "n_slack": N_SLACK,
            "cases": total,
        },
        "witness": {
            "reverse_involution_pass": reverse_involution,
            "left_partition_pass": left_partition,
            "right_partition_pass": right_partition,
            "edge_observable_take_cases": edge_observable_take,
            "edge_observable_drop_cases": edge_observable_drop,
            "mode_observable_left_cases": mode_observable_left,
            "mode_observable_right_cases": mode_observable_right,
            "four_functions_pairwise_distinct": all(pairwise_distinct.values()),
            "pairwise_distinct_details": pairwise_distinct,
            "axis_commutativity_corners": commutativity_checks,
        },
        "negative_controls": {
            "missing_final_reverse_partition_failures": bad_missing_reverse_failures,
            "wrong_suffix_drop_partition_failures": bad_suffix_drop_failures,
        },
        "semantic_corners": {
            "take_left": "current D6 parent semantics; lower-domain duplicate",
            "drop_left": "current D6 sibling semantics; lower-domain duplicate",
            "take_right": "new derived semantic candidate",
            "drop_right": "new derived semantic candidate",
        },
        "coordinate_gauge": gauge,
        "result": {
            "novel_semantic_candidates": 2,
            "invariant_coordinate_candidate": D6_PARENT + "11",
            "invariant_coordinate_meaning": "drop_right",
            "gauge_orbit_for_take_right": [D6_PARENT + "01", D6_PARENT + "10"],
            "orientation_theorem_missing": True,
        },
        "non_conclusions": [
            "No D8 resident is admitted or callable.",
            "The take_right absolute middle coordinate is not fixed.",
            "The current D6 DROP duplicate does not earn a D8 resident.",
            "No D7 semantic ancestry is used.",
            "No historical D8 donor row is input.",
        ],
    }


def render(report: dict[str, object]) -> str:
    w = report["witness"]
    n = report["negative_controls"]
    g = report["coordinate_gauge"]
    r = report["result"]
    return "\n".join(
        [
            "# D8 TAKE/DROP × edge product witness — #3622",
            "",
            f"Corpus: {report['corpus']['cases']} deterministic cases.",
            "",
            "Positive witnesses:",
            f"- REVERSE involution: {w['reverse_involution_pass']}/{report['corpus']['cases']}",
            f"- left partition: {w['left_partition_pass']}/{report['corpus']['cases']}",
            f"- right partition: {w['right_partition_pass']}/{report['corpus']['cases']}",
            f"- edge observable with TAKE fixed: {w['edge_observable_take_cases']} cases",
            f"- edge observable with DROP fixed: {w['edge_observable_drop_cases']} cases",
            f"- mode observable on left: {w['mode_observable_left_cases']} cases",
            f"- mode observable on right: {w['mode_observable_right_cases']} cases",
            f"- four functions pairwise distinct: {w['four_functions_pairwise_distinct']}",
            "",
            "Negative controls:",
            f"- missing final REVERSE breaks partition in {n['missing_final_reverse_partition_failures']} cases",
            f"- treating right DROP as suffix breaks partition in {n['wrong_suffix_drop_partition_failures']} cases",
            "",
            "Coordinate/gauge result:",
            f"- D6 anchor: {g['d6_parent']}",
            f"- D8 family coordinate set: {' '.join(g['d8_family_coordinates'])}",
            f"- selector collision: {g['selector_collision']}",
            f"- invariant base duplicate: {g['d6_parent']}00 = TAKE-left",
            f"- invariant novel 11 candidate: {r['invariant_coordinate_candidate']} = DROP-right",
            f"- TAKE-right remains in gauge orbit: {' / '.join(r['gauge_orbit_for_take_right'])}",
            "- the other middle coordinate is the lower-domain DROP duplicate;",
            "- swapping axis order swaps only the two middle corners.",
            "",
            "Research result: **PRODUCT-CANDIDATE**.",
            "",
            "No D8 semantic admission follows without owner ratification and an",
            "independent coordinate-orientation theorem for the middle corners.",
            "",
        ]
    )


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
