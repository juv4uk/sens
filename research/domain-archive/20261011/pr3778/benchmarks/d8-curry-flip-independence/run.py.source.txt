#!/usr/bin/env python3
"""#3748 — CURRY/FLIP swapped-argument independence falsifier.

Research-only D8 screen. The candidate second axis is argument orientation:
normal | swapped. If SWAP is extensionally identical to current D6 FLIP,
then the axis is not independent and must allocate zero D8 coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"

BITS = (0, 1)
INPUTS = tuple(product(BITS, repeat=2))


def load_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coord for coord, name in doc["residents"].items()}
    assert by_name["CURRY"] == "101100"
    assert by_name["FLIP"] == "101101"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "curry": by_name["CURRY"],
        "flip": by_name["FLIP"],
    }


def all_boolean_functions() -> list[tuple[int, int, int, int]]:
    # Truth-table order: 00, 01, 10, 11.
    return list(product(BITS, repeat=4))


def call(table: tuple[int, int, int, int], a: int, b: int) -> int:
    return table[(a << 1) | b]


def swap_inputs(table: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return tuple(call(table, b, a) for a, b in INPUTS)


def flip(table: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    # Independently stated current D6 semantic law.
    return tuple(call(table, b, a) for a, b in INPUTS)


def curry_left(
    table: tuple[int, int, int, int], bound: int
) -> tuple[int, int]:
    return tuple(call(table, bound, b) for b in BITS)


def curry_right(
    table: tuple[int, int, int, int], bound: int
) -> tuple[int, int]:
    return tuple(call(table, b, bound) for b in BITS)


def compose(f, g, table):
    return f(g(table))


def run() -> dict[str, object]:
    authority = load_authority()
    functions = all_boolean_functions()

    swap_equals_flip = 0
    swap_involution = 0
    curry_observations = 0
    curry_right_via_flip = 0
    orientation_observable = 0

    transforms = {
        "ID": lambda t: t,
        "FLIP": flip,
        "SWAP": swap_inputs,
        "FLIP_AFTER_SWAP": lambda t: flip(swap_inputs(t)),
    }
    transform_tables: dict[str, tuple[tuple[int, int, int, int], ...]] = {
        name: tuple(fn(t) for t in functions)
        for name, fn in transforms.items()
    }

    for table in functions:
        swap_equals_flip += swap_inputs(table) == flip(table)
        swap_involution += swap_inputs(swap_inputs(table)) == table
        orientation_observable += swap_inputs(table) != table

        for bound in BITS:
            left = curry_left(table, bound)
            right = curry_right(table, bound)
            right_via_flip = curry_left(flip(table), bound)

            for b in BITS:
                curry_observations += 1
                curry_right_via_flip += right[b] == right_via_flip[b]

    unique_global_transforms = len(set(transform_tables.values()))

    assert len(functions) == 16
    assert curry_observations == 64
    assert swap_equals_flip == 16
    assert swap_involution == 16
    assert curry_right_via_flip == 64
    assert orientation_observable > 0
    assert unique_global_transforms == 2
    assert transform_tables["ID"] == transform_tables["FLIP_AFTER_SWAP"]
    assert transform_tables["FLIP"] == transform_tables["SWAP"]

    return {
        "schema": "d8-curry-flip-independence/v1",
        "status": "DEPENDENT-AXIS-REJECTED",
        "authority": {
            "d6": authority,
            "d8": "#3281 research",
            "task": "#3748",
        },
        "carrier": {
            "boolean_binary_functions": 16,
            "bound_values": 2,
            "call_values": 2,
            "curry_observations": curry_observations,
        },
        "witness": {
            "swap_equals_flip_functions": swap_equals_flip,
            "swap_involution_functions": swap_involution,
            "curry_right_equals_curry_left_after_flip_observations": (
                curry_right_via_flip
            ),
            "orientation_observable_functions": orientation_observable,
            "putative_product_global_transforms": 4,
            "unique_global_transforms": unique_global_transforms,
        },
        "collapse": {
            "FLIP": "SWAP",
            "FLIP_AFTER_SWAP": "ID",
            "curry_right": "curry_left after current D6 FLIP",
        },
        "result": {
            "axis_independent": False,
            "analyzed_d8_coordinates": 0,
            "candidate_footprint": [],
            "reason": (
                "The proposed swapped-argument axis is extensionally the "
                "existing D6 FLIP operation, so the 2x2 transform product "
                "collapses from four global transformations to two."
            ),
        },
        "non_conclusions": [
            "This does not reject CURRY or FLIP from D6.",
            "This rejects only swapped-argument orientation as an independent D8 axis.",
            "No D8 resident, coordinate, or callability is admitted.",
            "No D7 ancestry or historical D8 donor is used.",
        ],
    }


def render(report: dict[str, object]) -> str:
    w = report["witness"]
    return "\n".join([
        "# D8 CURRY/FLIP independence screen — #3748",
        "",
        "Result: **DEPENDENT-AXIS-REJECTED**.",
        "",
        f"- SWAP = FLIP: {w['swap_equals_flip_functions']}/16 functions",
        f"- SWAP involution: {w['swap_involution_functions']}/16 functions",
        (
            "- CURRY-RIGHT = CURRY-LEFT after FLIP: "
            f"{w['curry_right_equals_curry_left_after_flip_observations']}/64 observations"
        ),
        (
            "- putative product transformations: "
            f"{w['putative_product_global_transforms']}"
        ),
        f"- unique global transformations: {w['unique_global_transforms']}",
        "",
        "D8 coordinates allocated: **0**.",
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
