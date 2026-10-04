#!/usr/bin/env python3
"""#3099 S1 — do independent D6 semantic pairs force a shared bit axis?

This is a coordinate-theorem experiment, not a semantic-law experiment.
Semantic inputs are already proved elsewhere and are keyed only by stable IDs.

Positive control:
- D6 selector descendants: admitted PREFIX-GENERATOR family.

Candidate geometry:
- parity complement pair;
- FIRST/REST destructive pair-update pair;
- PARALLEL/SEQUENTIAL binding-order pair.

CURRENT places all three candidate pairs on one bit axis.  This script asks
whether their *independent* semantic constraints force that common axis.

Research only. No production remap.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "knowledge" / "d3-d8-stable-residents.json"

WIDTH = 6
SAMPLES = 4096
SEED = 3099

PAIR_FAMILIES = [
    {
        "family": "parity-complement",
        "relation_type": "DUALITY-COMPLEMENT",
        "authority": "#3079",
        "a": "sr-qcstbceparwp",
        "b": "sr-vnrkjfutjtyh",
    },
    {
        "family": "pair-mutation-first-rest",
        "relation_type": "PRODUCT-AXIS-CANDIDATE",
        "authority": "#3090",
        "a": "sr-tdedcubrnwcy",
        "b": "sr-gmqxwcmzqfnp",
    },
    {
        "family": "binding-order-parallel-sequential",
        "relation_type": "PRODUCT-AXIS-CANDIDATE",
        "authority": "#3091",
        "a": "sr-bdhyqsyttxzy",
        "b": "sr-npgqyeyykjdd",
    },
]

RELATION_ONLY_AUTHORITIES = [
    "#3089 set lattice",
    "#3094 macro step/full closure",
    "#3095 numeric order/extrema",
]


def load_rows() -> list[dict[str, Any]]:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if isinstance(value, dict):
            if value.get("current_domain") == "D6":
                rows.append(value)
            for item in value.values():
                walk(item)

    walk(data)
    # The corpus is structurally nested but every resident record is unique.
    dedup = {row["stable_resident_id"]: row for row in rows}
    rows = list(dedup.values())
    assert len(rows) == 64, len(rows)
    assert len({row["current_bits"] for row in rows}) == 64
    return rows


def xor_axis(a: str, b: str) -> int | None:
    """Return LSB-indexed differing axis when Hamming distance is 1."""
    assert len(a) == len(b) == WIDTH
    diffs = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(diffs) != 1:
        return None
    msb_index = diffs[0]
    return WIDTH - 1 - msb_index


def selector_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = [
        row
        for row in rows
        if row.get("semantic_class") == "selector"
        and {"#1968", "#2329"}.issubset(set(row.get("semantic_law_refs") or []))
    ]
    assert len(out) == 16, len(out)
    return sorted(out, key=lambda row: row["current_bits"])


def pair_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["stable_resident_id"]: row for row in rows}
    result = []
    for family in PAIR_FAMILIES:
        a = by_id[family["a"]]
        b = by_id[family["b"]]
        axis = xor_axis(a["current_bits"], b["current_bits"])
        result.append(
            {
                **family,
                "a_bits": a["current_bits"],
                "b_bits": b["current_bits"],
                "current_hamming1": axis is not None,
                "current_axis_lsb_index": axis,
            }
        )
    return result


def exact_axis_space() -> dict[str, Any]:
    assignments = list(itertools.product(range(WIDTH), repeat=len(PAIR_FAMILIES)))
    common = [axes for axes in assignments if len(set(axes)) == 1]
    non_common = [axes for axes in assignments if len(set(axes)) > 1]
    assert len(assignments) == WIDTH ** len(PAIR_FAMILIES) == 216
    assert len(common) == WIDTH == 6
    return {
        "axis_assignments": len(assignments),
        "common_axis_assignments": len(common),
        "non_common_axis_assignments": len(non_common),
        "common_axis_fraction": len(common) / len(assignments),
        "orientation_gauge_lower_bound": 2 ** len(PAIR_FAMILIES),
        "axis_plus_orientation_gauge_lower_bound": len(assignments)
        * (2 ** len(PAIR_FAMILIES)),
    }


def available_nonselector_coords(selectors: list[dict[str, Any]]) -> list[str]:
    reserved = {row["current_bits"] for row in selectors}
    all_coords = [format(i, f"0{WIDTH}b") for i in range(1 << WIDTH)]
    avail = [bits for bits in all_coords if bits not in reserved]
    assert len(avail) == 48
    return avail


def random_free_null(available: list[str], rng: random.Random) -> dict[str, Any]:
    hits_common_axis = 0
    hits_all_hamming1 = 0
    axis_counts = Counter()

    for _ in range(SAMPLES):
        chosen = rng.sample(available, 6)
        pairs = [(chosen[0], chosen[1]), (chosen[2], chosen[3]), (chosen[4], chosen[5])]
        axes = [xor_axis(a, b) for a, b in pairs]
        if all(axis is not None for axis in axes):
            hits_all_hamming1 += 1
            if len(set(axes)) == 1:
                hits_common_axis += 1
                axis_counts[axes[0]] += 1

    return {
        "samples": SAMPLES,
        "all_three_hamming1": hits_all_hamming1,
        "all_three_hamming1_rate": hits_all_hamming1 / SAMPLES,
        "all_three_same_axis": hits_common_axis,
        "all_three_same_axis_rate": hits_common_axis / SAMPLES,
        "same_axis_counts": dict(sorted(axis_counts.items())),
    }


def edges_by_axis(available: list[str]) -> dict[int, list[tuple[str, str]]]:
    aset = set(available)
    out: dict[int, list[tuple[str, str]]] = {axis: [] for axis in range(WIDTH)}
    for bits in sorted(aset):
        n = int(bits, 2)
        for axis in range(WIDTH):
            other = format(n ^ (1 << axis), f"0{WIDTH}b")
            if other in aset and bits < other:
                out[axis].append((bits, other))
    return out


def random_product_preserving_null(
    available: list[str],
    rng: random.Random,
) -> dict[str, Any]:
    edge_map = edges_by_axis(available)
    accepted = 0
    common_axis = 0
    retries = 0
    axis_tuples = Counter()

    while accepted < SAMPLES:
        retries += 1
        if retries > SAMPLES * 100:
            raise RuntimeError("could not sample enough disjoint product embeddings")
        axes = tuple(rng.randrange(WIDTH) for _ in PAIR_FAMILIES)
        used: set[str] = set()
        chosen: list[tuple[str, str]] = []
        ok = True
        for axis in axes:
            candidates = [
                edge for edge in edge_map[axis]
                if edge[0] not in used and edge[1] not in used
            ]
            if not candidates:
                ok = False
                break
            edge = rng.choice(candidates)
            chosen.append(edge)
            used.update(edge)
        if not ok:
            continue

        accepted += 1
        axis_tuples[axes] += 1
        if len(set(axes)) == 1:
            common_axis += 1

    return {
        "samples": accepted,
        "attempts": retries,
        "same_axis": common_axis,
        "same_axis_rate": common_axis / accepted,
        "axis_tuple_count": len(axis_tuples),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = load_rows()
    selectors = selector_rows(rows)
    pairs = pair_rows(rows)
    current_axes = [row["current_axis_lsb_index"] for row in pairs]

    assert all(row["current_hamming1"] for row in pairs)
    assert current_axes == [0, 0, 0]

    # Positive control: current D6 selector component is exactly two canonical
    # prefix blocks, independently backed by #1968/#2329.
    selector_bits = {row["current_bits"] for row in selectors}
    expected_selector_bits = {
        f"101{i:03b}" for i in range(8)
    } | {
        f"110{i:03b}" for i in range(8)
    }
    assert selector_bits == expected_selector_bits

    exact = exact_axis_space()
    available = available_nonselector_coords(selectors)

    free = random_free_null(available, random.Random(SEED))
    product = random_product_preserving_null(
        available,
        random.Random(SEED + 1),
    )

    # The semantic relation graph in this S1 slice contains three disconnected
    # two-resident components. No proved equation connects the choice made by
    # one family to the choice made by another family.
    connected_cross_family_equations = 0
    shared_axis_forced = connected_cross_family_equations > 0
    assert not shared_axis_forced

    current_common_axis = len(set(current_axes)) == 1
    assert current_common_axis

    theorem_status = (
        "CURRENT-SHARED-AXIS-OBSERVED-BUT-NOT-FORCED"
        if current_common_axis and not shared_axis_forced
        else "UNKNOWN"
    )

    # At least these residents remain unconstrained by this coordinate slice:
    # selector component constrains 16; candidate pair components touch 6.
    constrained_ids = {
        row["stable_resident_id"] for row in selectors
    } | {
        family[key]
        for family in PAIR_FAMILIES
        for key in ("a", "b")
    }
    unconstrained_count = 64 - len(constrained_ids)
    assert unconstrained_count == 42

    with (args.out / "pair-current.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(pairs[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(pairs)

    result = {
        "schema": "d6-geometry-theorem-s1/v1",
        "authority": "research-only",
        "stable_corpus_donor": "#3061",
        "selector_positive_control": {
            "authority": ["#1968", "#2329", "#2502"],
            "resident_count": len(selectors),
            "current_prefix_blocks": ["101xxx", "110xxx"],
            "rediscovered": True,
            "geometry_credit": "PREFIX-GENERATOR",
        },
        "candidate_pair_families": pairs,
        "current_geometry": {
            "all_three_hamming1": True,
            "shared_axis": True,
            "shared_axis_lsb_index": 0,
        },
        "semantic_constraint_graph": {
            "components": len(PAIR_FAMILIES),
            "cross_family_semantic_equations": connected_cross_family_equations,
            "shared_axis_forced": shared_axis_forced,
        },
        "exact_axis_assignment_null": exact,
        "free_random_nonselector_null": free,
        "product_family_preserving_null": product,
        "relation_only_laws": {
            "authorities": RELATION_ONLY_AUTHORITIES,
            "geometry_credit": 0,
        },
        "coordinate_theorem_status": theorem_status,
        "solver_credit_for_common_axis": 0,
        "minimum_gauge_freedom": {
            "independent_axis_assignments": exact["axis_assignments"],
            "common_axis_assignments": exact["common_axis_assignments"],
            "axis_orientation_assignments_lower_bound": exact[
                "axis_plus_orientation_gauge_lower_bound"
            ],
        },
        "d6_residents_unconstrained_by_this_slice": unconstrained_count,
        "interpretation": [
            "CURRENT same-LSB alignment is compatible with all three proved relations",
            "the relations are disconnected and do not force a shared coordinate axis",
            "conditional rarity is evidence worth tracking but not semantic authority",
            "a cross-family semantic equation is required before common-axis solver credit",
        ],
        "non_conclusions": [
            "the CURRENT LSB alignment is not disproved",
            "the three relations are not semantically equivalent",
            "relation-only lattice/iteration laws do not constrain placement",
            "this S1 slice does not solve full 64-resident D6 geometry",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D6 geometry theorem S1 — #3099",
        "",
        "CURRENT candidate pairs:",
        "",
        "| family | bits A | bits B | axis (LSB=0) |",
        "|---|---|---|---:|",
    ]
    for row in pairs:
        report.append(
            f"| {row['family']} | {row['a_bits']} | {row['b_bits']} | "
            f"{row['current_axis_lsb_index']} |"
        )

    report += [
        "",
        "All three CURRENT pairs use the same LSB axis.",
        "",
        "But the proved semantic relation graph has three disconnected components:",
        "there is no proved cross-family equation saying that parity choice,",
        "FIRST/REST mutation choice, and binding-order choice are one semantic axis.",
        "",
        "Exact axis-assignment space:",
        f"- independent assignments: **{exact['axis_assignments']}**;",
        f"- common-axis assignments: **{exact['common_axis_assignments']}**;",
        f"- common-axis fraction: **{exact['common_axis_fraction']:.4%}**.",
        "",
        "Matched nulls (selector D6 cells reserved):",
        f"- free random same-axis hit rate: **{free['all_three_same_axis_rate']:.4%}**;",
        f"- product-family-preserving same-axis rate: **{product['same_axis_rate']:.4%}**.",
        "",
        f"Coordinate theorem: **{theorem_status}**",
        "",
        "Solver credit for a global common D6 bit axis: **0**.",
        "",
        "Why: statistical alignment can motivate the next theorem, but only a",
        "cross-family semantic equation may force the axes to be identified.",
        "",
        "Selector PREFIX-GENERATOR remains the positive coordinate-law control.",
        "Set lattice, macro closure and numeric order/extrema remain relation-only.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
