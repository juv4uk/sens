#!/usr/bin/env python3
"""#2664 lane C — anti-numerology symmetry of the 44 D6 PURE-UNKNOWN coordinates.

Research-only.

The canonical #2660 frontier partitions D6 into:
- 16 generated selector residents;
- 44 PURE-UNKNOWN coordinates;
- 1 parent-duplicate proof row;
- 2 nonadmitted middle product overlays;
- 1 owner-ready/nonadmitted target.

This witness proves a deliberately weak but important negative statement:

    before a new semantic law distinguishes members of PURE-UNKNOWN,
    representation-only relabelings may permute those 44 coordinates freely
    while fixing every semantically/evidentially distinguished D6 row.

Therefore numeric order, Hamming weight, prefix aesthetics, distance to an
existing resident, or any similar raw-bit ranking cannot earn residency.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Callable, Any

HERE = Path(__file__).resolve().parent
FRONTIER_RUN = HERE / "run.py"

PURE = "PURE-UNKNOWN"


def hamming(a: str, b: str) -> int:
    assert len(a) == len(b)
    return sum(x != y for x, y in zip(a, b))


def common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def swap_map(universe: list[str], a: str, b: str) -> dict[str, str]:
    assert a != b
    mapping = {x: x for x in universe}
    mapping[a], mapping[b] = b, a
    return mapping


def inverse(mapping: dict[str, str]) -> dict[str, str]:
    result = {v: k for k, v in mapping.items()}
    assert len(result) == len(mapping)
    return result


def load() -> tuple[dict[str, Any], list[str], list[str], list[str]]:
    ns = runpy.run_path(str(FRONTIER_RUN))
    result = ns["build"]()

    frontier = result["frontier"]
    pure = sorted(
        row["coordinate"]
        for row in frontier
        if row["research_evidence_class"] == PURE
    )
    distinguished_unknown = sorted(
        row["coordinate"]
        for row in frontier
        if row["research_evidence_class"] != PURE
    )

    closure = ns["load_closure"]()
    generated = sorted(
        row["coordinate"] for row in closure if row["status"] == "generated"
    )

    assert len(generated) == 16
    assert len(pure) == 44
    assert len(distinguished_unknown) == 4
    assert len(set(generated) | set(pure) | set(distinguished_unknown)) == 64

    for row in frontier:
        if row["coordinate"] in pure:
            assert row["canonical_semantic_member"] is False
            assert row["canonical_placement_ref"] == ""
            assert row["research_refs"] == []

    return result, generated, pure, distinguished_unknown


def prove_transitive_orbit(
    generated: list[str],
    pure: list[str],
    distinguished_unknown: list[str],
) -> dict[str, Any]:
    universe = sorted(generated + pure + distinguished_unknown)
    anchor = pure[0]
    orbit = {anchor}
    witnesses = []

    protected = set(generated) | set(distinguished_unknown)

    for target in pure[1:]:
        permutation = swap_map(universe, anchor, target)

        assert all(permutation[x] == x for x in protected)
        assert set(permutation[x] for x in pure) == set(pure)

        orbit.add(permutation[anchor])
        witnesses.append(
            {
                "swap": [anchor, target],
                "fixes_protected": True,
                "pure_unknown_set_preserved": True,
            }
        )

    assert orbit == set(pure)
    return {
        "anchor": anchor,
        "orbit_size": len(orbit),
        "pure_unknown_size": len(pure),
        "transitive": True,
        "generator_transpositions": witnesses,
    }


def prove_representation_rankings_nonsemantic(
    generated: list[str],
    pure: list[str],
    distinguished_unknown: list[str],
) -> list[dict[str, Any]]:
    universe = sorted(generated + pure + distinguished_unknown)
    generated_set = set(generated)
    owner_ready = "001111"

    heuristics: dict[str, Callable[[str], tuple[Any, ...]]] = {
        "numeric-smallest": lambda x: (int(x, 2),),
        "numeric-largest": lambda x: (-int(x, 2),),
        "fewest-one-bits": lambda x: (x.count("1"), int(x, 2)),
        "most-one-bits": lambda x: (-x.count("1"), int(x, 2)),
        "closest-to-any-generated": lambda x: (
            min(hamming(x, g) for g in generated_set),
            int(x, 2),
        ),
        "closest-to-owner-ready-001111": lambda x: (
            hamming(x, owner_ready),
            int(x, 2),
        ),
        "longest-prefix-with-D4-DEFINE-0011": lambda x: (
            -common_prefix(x, "0011"),
            int(x, 2),
        ),
    }

    rows = []
    fallback = pure[-1]

    for name, key in heuristics.items():
        winner_coordinate = min(pure, key=key)
        other = fallback if fallback != winner_coordinate else pure[0]

        permutation = swap_map(universe, winner_coordinate, other)
        inv = inverse(permutation)

        # The raw-bit heuristic sees exactly the same coordinate strings after
        # a semantics-preserving relabeling and therefore picks the same
        # printed coordinate. But that printed coordinate now denotes a
        # different abstract PURE-UNKNOWN token.
        selected_token_before = winner_coordinate
        selected_token_after = inv[winner_coordinate]

        assert selected_token_after != selected_token_before
        assert all(permutation[x] == x for x in generated)
        assert all(permutation[x] == x for x in distinguished_unknown)

        rows.append(
            {
                "heuristic": name,
                "winner_coordinate": winner_coordinate,
                "swapped_with": other,
                "selected_abstract_token_before": selected_token_before,
                "selected_abstract_token_after": selected_token_after,
                "semantics_preserved": True,
                "ranking_invariant": False,
                "verdict": "ACCIDENTAL-REPRESENTATION",
            }
        )

    return rows


def build() -> dict[str, Any]:
    frontier, generated, pure, distinguished = load()

    orbit = prove_transitive_orbit(generated, pure, distinguished)
    rankings = prove_representation_rankings_nonsemantic(
        generated, pure, distinguished
    )

    assert orbit["orbit_size"] == 44
    assert all(not row["ranking_invariant"] for row in rankings)
    assert frontier["canonical"]["occupancy_mutations"] == 0

    return {
        "schema": "d6-pure-unknown-anti-numerology/v1",
        "domain": "Core D6",
        "input_frontier_schema": frontier["schema"],
        "canonical_generated": len(generated),
        "pure_unknown": len(pure),
        "distinguished_nonadmitted_unknown": len(distinguished),
        "symmetry": orbit,
        "representation_rankings": rankings,
        "semantic_conclusion": {
            "pure_unknown_is_one_unbroken_orbit": True,
            "coordinate_only_candidate_selection": "REJECT",
            "required_symmetry_breaker": (
                "independent semantic law/theorem with parent, deltas, witness, "
                "falsifier and domain authority"
            ),
            "new_candidates": 0,
            "occupancy_mutations": 0,
        },
        "non_conclusions": [
            "does not prove that PURE-UNKNOWN coordinates can never gain residents",
            "does not choose among future semantic laws",
            "does not affect 001111 owner readiness",
            "does not assign a coordinate to non-local-exit or any historical row",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = build()

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("D6-PURE-UNKNOWN-ANTI-NUMEROLOGY=PASS")
    print("PURE-UNKNOWN=44")
    print("SYMMETRY-ORBIT=44")
    print("TRANSITIVE=YES")
    print("PROTECTED-D6-ROWS-FIXED=YES")
    print("COORDINATE-ONLY-CANDIDATE=REJECT")
    print("NEW-CANDIDATES=0")
    print("OCCUPANCY-MUTATIONS=0")
    for row in result["representation_rankings"]:
        print(
            f"REJECTED-HEURISTIC={row['heuristic']}:"
            f"{row['winner_coordinate']}->{row['selected_abstract_token_after']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
