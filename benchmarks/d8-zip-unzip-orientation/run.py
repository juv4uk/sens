#!/usr/bin/env python3
"""#3710 — ZIP/UNZIP × product-orientation D8 research witness.

Research only. No D8 resident is admitted or made callable.

Finite typed carrier:
- bit lists over {0,1};
- equal-length pair lane;
- lengths 0..4;
- 341 exhaustive (xs, ys) input pairs.

The product square is typed:
  role        = constructor | destructor
  orientation = normal | swapped

ZIP-SWAPPED(xs,ys) = ZIP(ys,xs)
UNZIP-SWAPPED(ps)  = swap(UNZIP(ps))
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
MAX_LENGTH = 4


def load_d6_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coord for coord, name in doc["residents"].items()}
    assert by_name["ZIP"] == "111000"
    assert by_name["UNZIP"] == "111001"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "zip": by_name["ZIP"],
        "unzip": by_name["UNZIP"],
    }


def bit_lists(length: int):
    return list(product(BITS, repeat=length))


def corpus():
    out = []
    for length in range(MAX_LENGTH + 1):
        values = bit_lists(length)
        for xs in values:
            for ys in values:
                out.append((xs, ys))
    return out


def zip_normal(xs, ys):
    assert len(xs) == len(ys)
    return tuple(zip(xs, ys))


def zip_swapped(xs, ys):
    return zip_normal(ys, xs)


def unzip_normal(ps):
    left = tuple(a for a, _ in ps)
    right = tuple(b for _, b in ps)
    return left, right


def unzip_swapped(ps):
    left, right = unzip_normal(ps)
    return right, left


def swap_pair(pair):
    a, b = pair
    return b, a


def selector_d8_candidates():
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
    parent = str(d6["zip"])
    sibling = str(d6["unzip"])
    family = {parent + suffix for suffix in ("00", "01", "10", "11")}
    assert family.isdisjoint(selector_d8_candidates())

    return {
        "d6_parent": parent,
        "d6_known_sibling": sibling,
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_a": {
            "order": ["role", "orientation"],
            "corners": {
                "00": "zip_normal",
                "01": "zip_swapped",
                "10": "unzip_normal",
                "11": "unzip_swapped",
            },
        },
        "axis_order_b": {
            "order": ["orientation", "role"],
            "corners": {
                "00": "zip_normal",
                "01": "unzip_normal",
                "10": "zip_swapped",
                "11": "unzip_swapped",
            },
        },
        "invariants": {
            parent + "00": "ZIP / lower-domain duplicate",
            parent + "11": "UNZIP-SWAPPED / generated novel candidate",
        },
        "orientation_gauge_orbit": {
            "coordinates": [parent + "01", parent + "10"],
            "meanings": [
                "ZIP-SWAPPED / generated novel candidate",
                "UNZIP / lower-domain duplicate",
            ],
            "rule": "axis order swaps only the middle corners",
        },
    }


def run():
    d6 = load_d6_authority()
    cases = corpus()
    assert len(cases) == 341

    normal_roundtrip = 0
    swapped_roundtrip = 0
    zip_orientation_observable = 0
    unzip_orientation_observable = 0
    orientation_involution_zip = 0
    orientation_involution_unzip = 0
    negative_zip_only_failures = 0
    negative_unzip_only_failures = 0

    for xs, ys in cases:
        zn = zip_normal(xs, ys)
        zs = zip_swapped(xs, ys)

        normal_roundtrip += unzip_normal(zn) == (xs, ys)
        swapped_roundtrip += unzip_swapped(zs) == (xs, ys)

        zip_orientation_observable += zn != zs
        unzip_orientation_observable += unzip_normal(zn) != unzip_swapped(zn)

        orientation_involution_zip += zip_swapped(ys, xs) == zn
        orientation_involution_unzip += swap_pair(unzip_swapped(zn)) == unzip_normal(zn)

        negative_zip_only_failures += unzip_normal(zs) != (xs, ys)
        negative_unzip_only_failures += unzip_swapped(zn) != (xs, ys)

    total = len(cases)
    assert normal_roundtrip == total
    assert swapped_roundtrip == total
    assert zip_orientation_observable > 0
    assert unzip_orientation_observable > 0
    assert orientation_involution_zip == total
    assert orientation_involution_unzip == total
    assert negative_zip_only_failures > 0
    assert negative_unzip_only_failures > 0
    assert zip_orientation_observable == negative_zip_only_failures
    assert unzip_orientation_observable == negative_unzip_only_failures

    # Typed commuting-square check:
    # toggling role and orientation reaches the same semantic corner label
    # regardless of axis order.
    role_toggle = {"constructor": "destructor", "destructor": "constructor"}
    orientation_toggle = {"normal": "swapped", "swapped": "normal"}

    def apply_role(state):
        role, orientation = state
        return role_toggle[role], orientation

    def apply_orientation(state):
        role, orientation = state
        return role, orientation_toggle[orientation]

    commuting = 0
    for role in ("constructor", "destructor"):
        for orientation in ("normal", "swapped"):
            start = (role, orientation)
            assert apply_orientation(apply_role(start)) == apply_role(
                apply_orientation(start)
            )
            commuting += 1
    assert commuting == 4

    gauge = coordinate_gauge(d6)
    parent = str(d6["zip"])

    return {
        "schema": "d8-zip-unzip-orientation/v1",
        "status": "PRODUCT-CANDIDATE-TYPED",
        "authority": {
            "d6_zip_unzip": "#3393 / #3370",
            "d6_source": d6,
            "d8": "#3281 research",
            "task": "#3710",
        },
        "corpus": {
            "carrier": list(BITS),
            "max_length": MAX_LENGTH,
            "equal_length_pairs": total,
        },
        "witness": {
            "normal_roundtrip_pass": normal_roundtrip,
            "swapped_roundtrip_pass": swapped_roundtrip,
            "zip_orientation_observable_cases": zip_orientation_observable,
            "unzip_orientation_observable_cases": unzip_orientation_observable,
            "zip_orientation_involution_pass": orientation_involution_zip,
            "unzip_orientation_involution_pass": orientation_involution_unzip,
            "typed_axis_commutativity_corners": commuting,
        },
        "negative_controls": {
            "swap_zip_only_roundtrip_failures": negative_zip_only_failures,
            "swap_unzip_only_roundtrip_failures": negative_unzip_only_failures,
        },
        "semantic_corners": {
            "zip_normal": "current D6 parent semantics; lower-domain duplicate",
            "unzip_normal": "current D6 sibling semantics; lower-domain duplicate",
            "zip_swapped": "generated novel typed semantic candidate",
            "unzip_swapped": "generated novel typed semantic candidate",
        },
        "coordinate_gauge": gauge,
        "result": {
            "generated_novel_semantics": 2,
            "invariant_coordinate_candidate": parent + "11",
            "invariant_coordinate_meaning": "unzip_swapped",
            "gauge_orbit_for_zip_swapped": [parent + "01", parent + "10"],
            "orientation_theorem_missing": True,
        },
        "non_conclusions": [
            "No D8 resident is admitted or callable.",
            "Generated meanings need not become primitives.",
            "ZIP-SWAPPED absolute middle coordinate is unresolved.",
            "No D7 ancestry or historical D8 donor is used.",
        ],
    }


def render(report):
    w = report["witness"]
    n = report["negative_controls"]
    g = report["coordinate_gauge"]
    r = report["result"]
    total = report["corpus"]["equal_length_pairs"]
    return "\n".join([
        "# D8 ZIP/UNZIP × product orientation — #3710",
        "",
        f"Finite exhaustive equal-length corpus: {total} cases.",
        "",
        f"- UNZIP(ZIP(xs,ys)) roundtrip: {w['normal_roundtrip_pass']}/{total}",
        f"- UNZIP-SWAPPED(ZIP-SWAPPED(xs,ys)) roundtrip: {w['swapped_roundtrip_pass']}/{total}",
        f"- ZIP orientation observable: {w['zip_orientation_observable_cases']} cases",
        f"- UNZIP orientation observable: {w['unzip_orientation_observable_cases']} cases",
        f"- ZIP orientation involution: {w['zip_orientation_involution_pass']}/{total}",
        f"- UNZIP orientation involution: {w['unzip_orientation_involution_pass']}/{total}",
        "",
        "Negative controls:",
        f"- swap ZIP only -> roundtrip failures: {n['swap_zip_only_roundtrip_failures']}",
        f"- swap UNZIP only -> roundtrip failures: {n['swap_unzip_only_roundtrip_failures']}",
        "",
        "Coordinate/gauge:",
        f"- D6 anchor: {g['d6_parent']} (ZIP)",
        f"- family: {' '.join(g['d8_family_coordinates'])}",
        f"- selector collision: {g['selector_collision']}",
        f"- invariant 11 candidate: {r['invariant_coordinate_candidate']} = UNZIP-SWAPPED",
        f"- ZIP-SWAPPED gauge orbit: {' / '.join(r['gauge_orbit_for_zip_swapped'])}",
        "",
        "Research result: **PRODUCT-CANDIDATE-TYPED**.",
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
