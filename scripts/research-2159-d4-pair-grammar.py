#!/usr/bin/env python3
"""#2159 — exhaustive D4 pair-grammar placement witness.

Research-only. This script does NOT ratify D4 codes.

It preserves the four selector descendants already backed by executable
composition evidence, enumerates the remaining bootstrap candidate placements,
and reports independent objective scores rather than one hidden weighted sum.
"""

from __future__ import annotations

from itertools import permutations, product

PREFIXES = ("000", "001", "010", "011", "100", "111")

FIXED = {
    "CAAR": "1010",
    "CADR": "1011",
    "CDAR": "1100",
    "CDDR": "1101",
}

SIBLING_PAIRS = {
    "APPLY/EVAL": ("APPLY", "EVAL"),
    "LAMBDA/DEFINE": ("LAMBDA", "DEFINE"),
    "EVCON/EVLIS": ("EVCON", "EVLIS"),
    "LOOKUP/BIND": ("LOOKUP", "BIND"),
}

# Transparent bootstrap-relation set. These are relations to test for cheap
# Hamming adjacency, not semantic authority created by the cube.
RELATION_EDGES = {
    frozenset(("APPLY", "EVAL")),
    frozenset(("APPLY", "LAMBDA")),
    frozenset(("APPLY", "BIND")),
    frozenset(("EVAL", "LAMBDA")),
    frozenset(("EVAL", "EVLIS")),
    frozenset(("EVAL", "EVCON")),
    frozenset(("EVAL", "LOOKUP")),
    frozenset(("EVAL", "BIND")),
    frozenset(("EVCON", "EVLIS")),
    frozenset(("LOOKUP", "BIND")),
    frozenset(("LOOKUP", "CAAR")),
    frozenset(("LOOKUP", "CDAR")),
    frozenset(("BIND", "CADR")),
    frozenset(("BIND", "CDDR")),
    frozenset(("LIST", "CAAR")),
    frozenset(("LIST", "CDAR")),
}

# Prefix affinity is intentionally narrower than the full dependency graph.
# It asks whether a role is placed under a D3 root with a direct current-family
# rationale. No points are assigned to APPLY/EVAL at 000 because that remains a
# bootstrap/meta placement hypothesis, not a derived ground-family theorem.
PARENT_ALLOWED = {
    "LAMBDA": {"001"},   # QUOTE / special-form neighborhood
    "DEFINE": {"001"},
    "NOT": {"010", "011"},
    "EVCON": {"011"},    # COND
    "EVLIS": {"011"},
    "LIST": {"100"},     # CONS
    "LOOKUP": {"111"},   # EQ / identity-led environment search
    "BIND": {"111", "100"},
}

CANDIDATE_A = {
    "APPLY": "0000",
    "EVAL": "0001",
    "LAMBDA": "0010",
    "DEFINE": "0011",
    "NOT": "0100",
    "RES1": "0101",
    "EVCON": "0110",
    "EVLIS": "0111",
    "LIST": "1000",
    "RES2": "1001",
    "CAAR": "1010",
    "CADR": "1011",
    "CDAR": "1100",
    "CDDR": "1101",
    "LOOKUP": "1110",
    "BIND": "1111",
}


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def score(mapping: dict[str, str]) -> tuple[int, int]:
    relation_adjacency = sum(
        hamming(mapping[a], mapping[b]) == 1
        for edge in RELATION_EDGES
        for a, b in (tuple(edge),)
    )
    parent_affinity = sum(
        mapping[name][:3] in allowed
        for name, allowed in PARENT_ALLOWED.items()
    )
    return relation_adjacency, parent_affinity


def placements():
    pair_names = tuple(SIBLING_PAIRS)
    for assigned_prefixes in permutations(PREFIXES, 4):
        used = set(assigned_prefixes)
        remaining_prefixes = [p for p in PREFIXES if p not in used]

        for orientations in product((0, 1), repeat=4):
            base = dict(FIXED)

            for pair_name, prefix, orientation in zip(
                pair_names, assigned_prefixes, orientations
            ):
                left, right = SIBLING_PAIRS[pair_name]
                if orientation == 0:
                    base[left] = prefix + "0"
                    base[right] = prefix + "1"
                else:
                    base[left] = prefix + "1"
                    base[right] = prefix + "0"

            remaining_cells = [
                prefix + bit
                for prefix in remaining_prefixes
                for bit in ("0", "1")
            ]

            for list_cell, not_cell in permutations(remaining_cells, 2):
                mapping = dict(base)
                mapping["LIST"] = list_cell
                mapping["NOT"] = not_cell

                rest = [
                    cell
                    for cell in remaining_cells
                    if cell not in {list_cell, not_cell}
                ]
                mapping["RES1"], mapping["RES2"] = rest
                yield mapping


def pareto_points(points: set[tuple[int, int]]) -> list[tuple[int, int]]:
    out = []
    for point in points:
        dominated = any(
            other != point
            and other[0] >= point[0]
            and other[1] >= point[1]
            for other in points
        )
        if not dominated:
            out.append(point)
    return sorted(out)


def main() -> None:
    rows = []
    for mapping in placements():
        rows.append((score(mapping), mapping))

    assert len(rows) == 69120

    candidate_score = score(CANDIDATE_A)
    max_relation = max(s[0] for s, _ in rows)
    max_parent = max(s[1] for s, _ in rows)
    best_relation_at_max_parent = max(
        s[0] for s, _ in rows if s[1] == max_parent
    )
    same_candidate_objectives = sum(
        1 for s, _ in rows if s == candidate_score
    )
    frontier = pareto_points({s for s, _ in rows})

    assert candidate_score == (10, 8)
    assert max_relation == 13
    assert max_parent == 8
    assert best_relation_at_max_parent == 10
    assert candidate_score in frontier

    print("D4 pair-grammar exhaustive witness: PASS")
    print(f"placements={len(rows)}")
    print(f"candidate-a relation-adjacency={candidate_score[0]}")
    print(f"candidate-a parent-affinity={candidate_score[1]}")
    print(f"max relation-adjacency={max_relation}")
    print(f"max parent-affinity={max_parent}")
    print(
        "best relation-adjacency at max parent-affinity="
        f"{best_relation_at_max_parent}"
    )
    print(f"placements sharing candidate objective pair={same_candidate_objectives}")
    print(
        "pareto="
        + ",".join(f"({relation},{parent})" for relation, parent in frontier)
    )
    print("NON-CONCLUSION: bit adjacency does not define semantics")
    print("NON-CONCLUSION: Candidate A orientation is not yet ratified")


if __name__ == "__main__":
    main()
