#!/usr/bin/env python3
"""#3674 — REDUCE/SCAN × fold-direction D8 product witness.

Research-only and restricted to nonempty lists because #3370 does not fully pin
the empty-list SCAN presentation.

Finite carrier:
- bits {0,1};
- all 16 binary operations on bits;
- both initial accumulator bits;
- all nonempty bit lists of lengths 1..4.

No historical D8 donor is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"
D3_SELECTOR_ROOTS = ("011", "100")

BITS = (0, 1)
OPS = tuple(product(BITS, repeat=4))
MAX_LENGTH = 4


def load_d6_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coordinate for coordinate, name in doc["residents"].items()}
    assert by_name["REDUCE"] == "101110"
    assert by_name["SCAN"] == "101111"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "reduce": by_name["REDUCE"],
        "scan": by_name["SCAN"],
    }


def apply_op(op: tuple[int, int, int, int], a: int, b: int) -> int:
    return op[a * 2 + b]


def reduce_left(op, z, xs):
    acc = z
    for x in xs:
        acc = apply_op(op, acc, x)
    return acc


def scan_left(op, z, xs):
    acc = z
    out = []
    for x in xs:
        acc = apply_op(op, acc, x)
        out.append(acc)
    return tuple(out)


def reduce_right(op, z, xs):
    acc = z
    for x in reversed(xs):
        acc = apply_op(op, x, acc)
    return acc


def scan_right(op, z, xs):
    """Right fold history in computation order; final item is REDUCE-right."""
    acc = z
    out = []
    for x in reversed(xs):
        acc = apply_op(op, x, acc)
        out.append(acc)
    return tuple(out)


def wrong_reduce_right_without_flip(op, z, xs):
    acc = z
    for x in reversed(xs):
        acc = apply_op(op, acc, x)
    return acc


def lists():
    out = []
    for length in range(1, MAX_LENGTH + 1):
        out.extend(product(BITS, repeat=length))
    return out


def corpus():
    return [(op, z, xs) for op in OPS for z in BITS for xs in lists()]


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


def coordinate_gauge(d6):
    parent = str(d6["reduce"])
    sibling = str(d6["scan"])
    family = {parent + suffix for suffix in ("00", "01", "10", "11")}
    assert family.isdisjoint(selector_d8_candidates())

    return {
        "d6_parent": parent,
        "d6_known_sibling": sibling,
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_a": {
            "order": ["exposure", "direction"],
            "corners": {
                "00": "reduce_left",
                "01": "reduce_right",
                "10": "scan_left",
                "11": "scan_right",
            },
        },
        "axis_order_b": {
            "order": ["direction", "exposure"],
            "corners": {
                "00": "reduce_left",
                "01": "scan_left",
                "10": "reduce_right",
                "11": "scan_right",
            },
        },
        "invariants": {
            parent + "00": "REDUCE-left / lower-domain duplicate",
            parent + "11": "SCAN-right / generated novel nonempty candidate",
        },
        "orientation_gauge_orbit": {
            "coordinates": [parent + "01", parent + "10"],
            "meanings": [
                "REDUCE-right / generated novel nonempty candidate",
                "SCAN-left / lower-domain duplicate",
            ],
            "rule": "axis order swaps only the middle corners",
        },
    }


def run():
    d6 = load_d6_authority()
    parent = str(d6["reduce"])
    cases = corpus()
    assert len(OPS) == 16
    assert len(lists()) == 30
    assert len(cases) == 960

    left_law = sum(
        scan_left(op, z, xs)[-1] == reduce_left(op, z, xs)
        for op, z, xs in cases
    )
    right_law = sum(
        scan_right(op, z, xs)[-1] == reduce_right(op, z, xs)
        for op, z, xs in cases
    )

    direction_reduce = sum(
        reduce_left(op, z, xs) != reduce_right(op, z, xs)
        for op, z, xs in cases
    )
    direction_scan = sum(
        scan_left(op, z, xs) != scan_right(op, z, xs)
        for op, z, xs in cases
    )

    history_exposure_cases = sum(len(xs) > 1 for _, _, xs in cases)

    wrong_scan_presentation_failures = sum(
        tuple(reversed(scan_right(op, z, xs)))[-1] != reduce_right(op, z, xs)
        for op, z, xs in cases
    )
    missing_flip_differences = sum(
        wrong_reduce_right_without_flip(op, z, xs) != reduce_right(op, z, xs)
        for op, z, xs in cases
    )

    total = len(cases)
    assert left_law == total
    assert right_law == total
    assert direction_reduce > 0
    assert direction_scan > 0
    assert history_exposure_cases > 0
    assert wrong_scan_presentation_failures > 0
    assert missing_flip_differences > 0

    # Product-coordinate toggles commute.
    exposure_toggle = {"reduce": "scan", "scan": "reduce"}
    direction_toggle = {"left": "right", "right": "left"}

    def exposure(state):
        mode, direction = state
        return (exposure_toggle[mode], direction)

    def direction(state):
        mode, side = state
        return (mode, direction_toggle[side])

    commutativity = 0
    for mode in ("reduce", "scan"):
        for side in ("left", "right"):
            start = (mode, side)
            assert direction(exposure(start)) == exposure(direction(start))
            commutativity += 1
    assert commutativity == 4

    gauge = coordinate_gauge(d6)

    return {
        "schema": "d8-reduce-scan-direction/v1",
        "status": "PRODUCT-CANDIDATE-NONEMPTY",
        "authority": {
            "d6_reduce_scan": "#3393 / #3370",
            "reverse": "#3305",
            "flip": "#3393 / #3384",
            "d6_source": d6,
            "d8": "#3281 research",
            "task": "#3674",
        },
        "protocol_boundary": {
            "empty_list": "UNRESOLVED",
            "reason": "#3370 pins last(SCAN)=REDUCE but does not fully specify empty-list SCAN presentation",
        },
        "corpus": {
            "carrier": [0, 1],
            "binary_operations": len(OPS),
            "initial_accumulators": 2,
            "nonempty_lists": len(lists()),
            "max_length": MAX_LENGTH,
            "cases": total,
        },
        "witness": {
            "left_last_scan_equals_reduce": left_law,
            "right_last_scan_equals_reduce": right_law,
            "direction_observable_reduce_cases": direction_reduce,
            "direction_observable_scan_cases": direction_scan,
            "scan_exposes_multi_step_history_cases": history_exposure_cases,
            "axis_commutativity_corners": commutativity,
        },
        "negative_controls": {
            "wrong_right_scan_presentation_failures": wrong_scan_presentation_failures,
            "missing_flip_differences": missing_flip_differences,
        },
        "semantic_corners": {
            "reduce_left": "current D6 parent semantics; lower-domain duplicate",
            "scan_left": "current D6 sibling semantics; lower-domain duplicate",
            "reduce_right": "generated novel semantic candidate on nonempty lane",
            "scan_right": "generated novel semantic candidate on nonempty lane",
        },
        "coordinate_gauge": gauge,
        "result": {
            "generated_novel_semantics": 2,
            "invariant_coordinate_candidate": parent + "11",
            "invariant_coordinate_meaning": "scan_right",
            "gauge_orbit_for_reduce_right": [parent + "01", parent + "10"],
            "orientation_theorem_missing": True,
            "empty_protocol_missing": True,
        },
        "non_conclusions": [
            "No D8 resident is admitted or callable.",
            "No claim is made for empty-list SCAN semantics.",
            "Generated semantics need not become primitive residents.",
            "REDUCE-right absolute middle coordinate is not fixed.",
            "No D7 ancestry or historical D8 donor is used.",
        ],
    }


def render(report):
    w = report["witness"]
    n = report["negative_controls"]
    g = report["coordinate_gauge"]
    r = report["result"]
    total = report["corpus"]["cases"]
    return "\n".join([
        "# D8 REDUCE/SCAN × direction witness — #3674",
        "",
        f"Finite exhaustive nonempty corpus: {total} cases.",
        "All 16 binary bit operations × 2 initial bits × 30 nonempty bit lists.",
        "",
        f"- left last(SCAN)=REDUCE: {w['left_last_scan_equals_reduce']}/{total}",
        f"- right last(SCAN)=REDUCE: {w['right_last_scan_equals_reduce']}/{total}",
        f"- direction observable for REDUCE: {w['direction_observable_reduce_cases']} cases",
        f"- direction observable for SCAN: {w['direction_observable_scan_cases']} cases",
        f"- multi-step SCAN history exposed: {w['scan_exposes_multi_step_history_cases']} cases",
        "",
        "Negative controls:",
        f"- wrong right-SCAN presentation breaks terminal law: {n['wrong_right_scan_presentation_failures']} cases",
        f"- reversing without FLIP differs from right fold: {n['missing_flip_differences']} cases",
        "",
        "Coordinate/gauge:",
        f"- D6 anchor: {g['d6_parent']} (REDUCE)",
        f"- family: {' '.join(g['d8_family_coordinates'])}",
        f"- selector collision: {g['selector_collision']}",
        f"- invariant 11 candidate: {r['invariant_coordinate_candidate']} = SCAN-right",
        f"- REDUCE-right gauge orbit: {' / '.join(r['gauge_orbit_for_reduce_right'])}",
        "",
        "Research result: **PRODUCT-CANDIDATE-NONEMPTY**.",
        "Empty-list SCAN protocol remains explicitly unresolved.",
        "",
    ])


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
