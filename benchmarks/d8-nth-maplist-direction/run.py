#!/usr/bin/env python3
"""#3744 — NTH/MAPLIST × traversal-direction D8 research witness.

Research only. No D8 resident is admitted or made callable.

Current D6 family:
    indexed observation = NTH
    all successive views = MAPLIST

Independent direction involution is induced by current D5 REVERSE:

    NTH-RIGHT(i,xs) = NTH(i, REVERSE(xs))

    MAPLIST-RIGHT(xs,f)
      = MAPLIST(REVERSE(xs), lambda tail: f(REVERSE(tail)))

Structurally, MAPLIST exposes successive list views. The identity observer is
therefore a complete witness of the view geometry before an arbitrary callback
is post-composed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Callable, TypeVar

REPO = Path(__file__).resolve().parents[2]
D5_AUTHORITY_PATH = REPO / "knowledge" / "d5-ratified.json"
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"
D3_SELECTOR_ROOTS = ("011", "100")

BITS = (0, 1)
MAX_LENGTH = 6
T = TypeVar("T")


def load_authority() -> dict[str, object]:
    d5_raw = D5_AUTHORITY_PATH.read_bytes()
    d5 = json.loads(d5_raw)
    assert d5["schema"] == "d5-ratified/v1"
    assert d5["status"] == "owner-ratified"
    assert d5["authority"] == "#3305"
    d5_by_name = {name: coord for coord, name in d5["residents"].items()}
    assert d5_by_name["REVERSE"] == "10100"

    d6_raw = D6_AUTHORITY_PATH.read_bytes()
    d6 = json.loads(d6_raw)
    assert d6["schema"] == "d6-ratified/v1"
    assert d6["status"] == "owner-ratified"
    assert d6["authority"] == "#3393"
    d6_by_name = {name: coord for coord, name in d6["residents"].items()}
    assert d6_by_name["NTH"] == "000100"
    assert d6_by_name["MAPLIST"] == "000101"

    return {
        "d5": {
            "path": str(D5_AUTHORITY_PATH.relative_to(REPO)),
            "sha256": hashlib.sha256(d5_raw).hexdigest(),
            "authority": d5["authority"],
            "reverse": d5_by_name["REVERSE"],
        },
        "d6": {
            "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
            "sha256": hashlib.sha256(d6_raw).hexdigest(),
            "authority": d6["authority"],
            "nth": d6_by_name["NTH"],
            "maplist": d6_by_name["MAPLIST"],
        },
    }


def reverse(xs: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(reversed(xs))


def lists() -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []
    for length in range(MAX_LENGTH + 1):
        out.extend(product(BITS, repeat=length))
    assert len(out) == 127
    return out


def left_views(xs: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(xs[i:] for i in range(len(xs)))


def right_views(xs: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    # Same ordinal i means "drop i elements from the right".
    return tuple(reverse(view) for view in left_views(reverse(xs)))


def maplist_left(
    xs: tuple[int, ...],
    observer: Callable[[tuple[int, ...]], T],
) -> tuple[T, ...]:
    return tuple(observer(view) for view in left_views(xs))


def maplist_right(
    xs: tuple[int, ...],
    observer: Callable[[tuple[int, ...]], T],
) -> tuple[T, ...]:
    # Conjugate the source and every callback view by REVERSE.
    return tuple(
        observer(reverse(view))
        for view in left_views(reverse(xs))
    )


def nth_left(index: int, xs: tuple[int, ...]) -> int:
    return xs[index]


def nth_right(index: int, xs: tuple[int, ...]) -> int:
    return nth_left(index, reverse(xs))


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


def coordinate_gauge(authority: dict[str, object]) -> dict[str, object]:
    d6 = authority["d6"]
    parent = str(d6["nth"])
    sibling = str(d6["maplist"])
    family = {parent + suffix for suffix in ("00", "01", "10", "11")}
    assert family.isdisjoint(selector_d8_candidates())

    return {
        "d6_parent": parent,
        "d6_sibling": sibling,
        "d5_reverse": str(authority["d5"]["reverse"]),
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_mode_then_direction": {
            "00": "NTH-LEFT",
            "01": "NTH-RIGHT",
            "10": "MAPLIST-LEFT",
            "11": "MAPLIST-RIGHT",
        },
        "axis_order_direction_then_mode": {
            "00": "NTH-LEFT",
            "01": "MAPLIST-LEFT",
            "10": "NTH-RIGHT",
            "11": "MAPLIST-RIGHT",
        },
        "invariants": {
            parent + "00": "NTH / current D6 lower-domain duplicate",
            parent + "11": "MAPLIST-RIGHT / generated typed candidate",
        },
        "middle_gauge_orbit": {
            "coordinates": [parent + "01", parent + "10"],
            "meanings": [
                "MAPLIST / current D6 lower-domain duplicate",
                "NTH-RIGHT / generated typed candidate",
            ],
            "absolute_assignment": "UNRESOLVED",
        },
    }


def run() -> dict[str, object]:
    authority = load_authority()
    corpus = lists()
    nonempty = [xs for xs in corpus if xs]

    reverse_involution = sum(reverse(reverse(xs)) == xs for xs in corpus)

    structural_right_views = 0
    direction_involution_views = 0
    maplist_identity_left = 0
    maplist_identity_right = 0
    view_direction_observable = 0

    indexed_cases = 0
    nth_left_view_law = 0
    nth_right_view_law = 0
    nth_direction_involution = 0
    nth_direction_observable = 0

    bad_input_reverse_only_failures = 0

    identity = lambda view: view

    for xs in corpus:
        lv = left_views(xs)
        rv = right_views(xs)

        expected_right = tuple(
            xs[: len(xs) - i]
            for i in range(len(xs))
        )
        structural_right_views += rv == expected_right

        # Apply the same conjugation to the already-right-oriented view family.
        restored_left = tuple(
            reverse(view)
            for view in right_views(reverse(xs))
        )
        direction_involution_views += restored_left == lv

        maplist_identity_left += maplist_left(xs, identity) == lv
        maplist_identity_right += maplist_right(xs, identity) == rv

        if xs:
            view_direction_observable += lv != rv
            bad = left_views(reverse(xs))
            bad_input_reverse_only_failures += bad != rv

            for i in range(len(xs)):
                indexed_cases += 1
                left = nth_left(i, xs)
                right = nth_right(i, xs)

                nth_left_view_law += left == lv[i][0]
                nth_right_view_law += right == rv[i][-1]
                nth_direction_involution += (
                    nth_right(i, reverse(xs)) == left
                )
                nth_direction_observable += left != right

    total_lists = len(corpus)
    nonempty_lists = len(nonempty)

    assert total_lists == 127
    assert nonempty_lists == 126
    assert indexed_cases == 642

    assert reverse_involution == total_lists
    assert structural_right_views == total_lists
    assert direction_involution_views == total_lists
    assert maplist_identity_left == total_lists
    assert maplist_identity_right == total_lists

    assert nth_left_view_law == indexed_cases
    assert nth_right_view_law == indexed_cases
    assert nth_direction_involution == indexed_cases

    assert nth_direction_observable == 300
    assert view_direction_observable == 114

    assert bad_input_reverse_only_failures == 114
    bad_degenerate_equal = (
        nonempty_lists - bad_input_reverse_only_failures
    )
    assert bad_degenerate_equal == 12

    gauge = coordinate_gauge(authority)
    parent = str(authority["d6"]["nth"])

    return {
        "schema": "d8-nth-maplist-direction/v1",
        "status": "PRODUCT-CANDIDATE-TYPED",
        "authority": {
            "d5_reverse": "#3305",
            "d6_nth_maplist": "#3393 / #3384 f02 / #3366",
            "sources": authority,
            "d8": "#3281 research",
            "task": "#3744",
        },
        "carrier": {
            "alphabet": list(BITS),
            "max_length": MAX_LENGTH,
            "total_lists": total_lists,
            "nonempty_lists": nonempty_lists,
            "valid_indexed_observations": indexed_cases,
        },
        "laws": {
            "nth_right": "NTH-RIGHT(i,xs)=NTH(i,REVERSE(xs))",
            "maplist_right": (
                "MAPLIST-RIGHT(xs,f)="
                "MAPLIST(REVERSE(xs),lambda tail:f(REVERSE(tail)))"
            ),
            "right_views": (
                "RIGHT-VIEWS(xs)="
                "map(REVERSE,LEFT-VIEWS(REVERSE(xs)))"
            ),
        },
        "witness": {
            "reverse_involution_pass": reverse_involution,
            "right_views_structural_pass": structural_right_views,
            "view_direction_involution_pass": direction_involution_views,
            "maplist_identity_left_pass": maplist_identity_left,
            "maplist_identity_right_pass": maplist_identity_right,
            "nth_left_view_law_pass": nth_left_view_law,
            "nth_right_view_law_pass": nth_right_view_law,
            "nth_direction_involution_pass": nth_direction_involution,
            "nth_direction_observable_cases": nth_direction_observable,
            "maplist_view_direction_observable_lists": (
                view_direction_observable
            ),
        },
        "negative_control": {
            "axis": "reverse input only; do not reverse callback views",
            "nonempty_lists": nonempty_lists,
            "failures": bad_input_reverse_only_failures,
            "degenerate_equal_lists": bad_degenerate_equal,
            "status": "REJECTED-INCOMPLETE-CONJUGATION",
        },
        "semantic_corners": {
            "nth_left": "current D6 parent; lower-domain duplicate",
            "maplist_left": "current D6 sibling; lower-domain duplicate",
            "nth_right": "generated typed semantic candidate",
            "maplist_right": "generated typed semantic candidate",
        },
        "coordinate_gauge": gauge,
        "result": {
            "generated_novel_semantics": 2,
            "invariant_coordinate_candidate": parent + "11",
            "invariant_coordinate_meaning": "MAPLIST-RIGHT",
            "middle_orbit": [parent + "01", parent + "10"],
            "middle_meanings": ["MAPLIST", "NTH-RIGHT"],
            "orientation_theorem_missing": True,
        },
        "non_conclusions": [
            "No D8 resident or primitive is admitted.",
            "MAPLIST appearing in the D8 square is a lower-domain duplicate.",
            "The absolute middle assignment remains gauge-unresolved.",
            "Structural identity-view equality is a pre-callback view theorem, not a restriction to identity callbacks.",
            "No D7 ancestry is used.",
            "No historical D8 donor row is input.",
        ],
    }


def render(report: dict[str, object]) -> str:
    c = report["carrier"]
    w = report["witness"]
    n = report["negative_control"]
    g = report["coordinate_gauge"]
    r = report["result"]

    return "\n".join([
        "# D8 NTH/MAPLIST × traversal direction — #3744",
        "",
        "Status: **PRODUCT-CANDIDATE-TYPED** (research only).",
        "",
        f"- total bit lists: {c['total_lists']}",
        f"- nonempty bit lists: {c['nonempty_lists']}",
        f"- valid indexed observations: {c['valid_indexed_observations']}",
        "",
        "Positive witnesses:",
        f"- REVERSE involution: {w['reverse_involution_pass']}/{c['total_lists']}",
        f"- RIGHT-VIEWS structural law: {w['right_views_structural_pass']}/{c['total_lists']}",
        f"- view direction involution: {w['view_direction_involution_pass']}/{c['total_lists']}",
        f"- MAPLIST-left identity views: {w['maplist_identity_left_pass']}/{c['total_lists']}",
        f"- MAPLIST-right identity views: {w['maplist_identity_right_pass']}/{c['total_lists']}",
        f"- NTH-left/view law: {w['nth_left_view_law_pass']}/{c['valid_indexed_observations']}",
        f"- NTH-right/view law: {w['nth_right_view_law_pass']}/{c['valid_indexed_observations']}",
        f"- NTH direction involution: {w['nth_direction_involution_pass']}/{c['valid_indexed_observations']}",
        f"- NTH direction observable: {w['nth_direction_observable_cases']} cases",
        f"- MAPLIST view direction observable: {w['maplist_view_direction_observable_lists']} lists",
        "",
        "Negative control:",
        f"- incomplete conjugation failures: {n['failures']}/{n['nonempty_lists']}",
        f"- explicit degenerate equal lists: {n['degenerate_equal_lists']}",
        "",
        "Coordinate/gauge:",
        f"- D6 anchor: {g['d6_parent']} (NTH)",
        f"- family: {' '.join(g['d8_family_coordinates'])}",
        f"- selector collision: {g['selector_collision']}",
        f"- invariant 11 candidate: {r['invariant_coordinate_candidate']} = MAPLIST-RIGHT",
        f"- middle gauge orbit: {' / '.join(r['middle_orbit'])} = MAPLIST / NTH-RIGHT",
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
