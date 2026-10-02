#!/usr/bin/env python3
"""#2339 minimal generators for the 64 affine maps on GF(2)^2.

Research only. Exhaustively proves no 1- or 2-generator set closes to all 64,
then finds a 3-generator witness. Also compares a more factorized 4-generator
basis so cardinality-minimum is not confused with semantic/execution optimum.
"""

from __future__ import annotations

from collections import Counter, deque
from itertools import combinations

Coord = tuple[int, int]
IDENTITY: Coord = (0b1001, 0b00)
COORDS: tuple[Coord, ...] = tuple(
    (matrix, offset)
    for matrix in range(16)
    for offset in range(4)
)


def bit(matrix: int, row: int, col: int) -> int:
    return (matrix >> (row * 2 + col)) & 1


def mat_vec(matrix: int, vector: int) -> int:
    x0 = vector & 1
    x1 = (vector >> 1) & 1
    y0 = (bit(matrix, 0, 0) & x0) ^ (bit(matrix, 0, 1) & x1)
    y1 = (bit(matrix, 1, 0) & x0) ^ (bit(matrix, 1, 1) & x1)
    return y0 | (y1 << 1)


def mat_mul(left: int, right: int) -> int:
    out = 0
    for row in range(2):
        for col in range(2):
            value = 0
            for k in range(2):
                value ^= bit(left, row, k) & bit(right, k, col)
            out |= value << (row * 2 + col)
    return out


def compose(outer: Coord, inner: Coord) -> Coord:
    a, b = outer
    c, d = inner
    return mat_mul(a, c), mat_vec(a, d) ^ b


# Precompute exact 64x64 coordinate composition relation for fast search.
INDEX = {coord: i for i, coord in enumerate(COORDS)}
COMPOSE_INDEX = tuple(
    tuple(INDEX[compose(outer, inner)] for inner in COORDS)
    for outer in COORDS
)


def closure_indices(generator_indices: tuple[int, ...]) -> set[int]:
    identity_index = INDEX[IDENTITY]
    seen = {identity_index, *generator_indices}
    frontier = list(seen)

    while frontier:
        x = frontier.pop()
        current = tuple(seen)
        for y in current:
            for z in (COMPOSE_INDEX[x][y], COMPOSE_INDEX[y][x]):
                if z not in seen:
                    seen.add(z)
                    frontier.append(z)
    return seen


def exhaustive_minimum_search():
    summary = {}

    for k in (1, 2):
        tested = 0
        max_size = 0
        best = None
        for subset in combinations(range(64), k):
            tested += 1
            size = len(closure_indices(subset))
            if size > max_size:
                max_size = size
                best = subset
            assert size < 64
        summary[k] = {
            "tested": tested,
            "max_size": max_size,
            "best": best,
        }

    tested = 0
    witness = None
    max_size = 0
    for subset in combinations(range(64), 3):
        tested += 1
        size = len(closure_indices(subset))
        max_size = max(max_size, size)
        if size == 64:
            witness = subset
            break

    assert witness is not None
    summary[3] = {
        "tested_until_first_full": tested,
        "max_size": max_size,
        "witness": witness,
    }
    return summary, witness


def shortest_depths(generator_indices: tuple[int, ...]) -> dict[int, int]:
    """Shortest word length by left-appending a generator."""
    identity_index = INDEX[IDENTITY]
    distance = {identity_index: 0}
    queue = deque([identity_index])

    while queue:
        current = queue.popleft()
        depth = distance[current]
        for generator in generator_indices:
            nxt = COMPOSE_INDEX[generator][current]
            if nxt not in distance:
                distance[nxt] = depth + 1
                queue.append(nxt)

    return distance


def format_coord(coord: Coord) -> str:
    matrix, offset = coord
    return f"({matrix:04b},{offset:02b})"


def basis_report(name: str, generators: tuple[Coord, ...]) -> None:
    indices = tuple(INDEX[g] for g in generators)
    closure = closure_indices(indices)
    assert len(closure) == 64

    depths = shortest_depths(indices)
    assert len(depths) == 64

    histogram = Counter(depths.values())
    max_depth = max(depths.values())
    average_depth = sum(depths.values()) / 64.0

    print(f"BASIS={name}")
    print("GENERATORS=" + ",".join(format_coord(g) for g in generators))
    print(f"CARDINALITY={len(generators)}")
    print(f"CLOSURE={len(closure)}")
    print(f"MAX-SHORTEST-DEPTH={max_depth}")
    print(f"AVERAGE-SHORTEST-DEPTH={average_depth:.6f}")
    print(
        "DEPTH-HISTOGRAM="
        + ",".join(f"{d}:{histogram[d]}" for d in sorted(histogram))
    )

    for i in range(len(indices)):
        reduced = indices[:i] + indices[i + 1:]
        reduced_size = len(closure_indices(reduced))
        print(f"REMOVE-{i}-CLOSURE={reduced_size}")
        assert reduced_size < 64


def main() -> None:
    summary, witness_indices = exhaustive_minimum_search()

    print(
        f"K1-SUBSETS-TESTED={summary[1]['tested']} "
        f"K1-MAX-CLOSURE={summary[1]['max_size']}"
    )
    print(
        f"K2-SUBSETS-TESTED={summary[2]['tested']} "
        f"K2-MAX-CLOSURE={summary[2]['max_size']}"
    )
    print(
        f"K3-SUBSETS-UNTIL-FIRST-FULL={summary[3]['tested_until_first_full']} "
        f"K3-MAX-CLOSURE={summary[3]['max_size']}"
    )

    minimal_generators = tuple(COORDS[i] for i in witness_indices)

    # A semantically factorized control:
    # P = rank-1 projection
    # S = swap coordinates
    # H = invertible shear
    # T = unit translation
    structured_generators: tuple[Coord, ...] = (
        (0b0001, 0b00),
        (0b0110, 0b00),
        (0b1011, 0b00),
        (0b1001, 0b01),
    )

    basis_report("MIN-CARDINALITY-3", minimal_generators)
    basis_report("FACTORIZED-4", structured_generators)

    # Explicit nonlinear negative control: scalar x0 AND x1 is not affine.
    affine_scalar_tables = {
        tuple(
            ((a0 & (x & 1)) ^ (a1 & ((x >> 1) & 1)) ^ b)
            for x in range(4)
        )
        for a0 in (0, 1)
        for a1 in (0, 1)
        for b in (0, 1)
    }
    nonlinear = tuple(
        (x & 1) & ((x >> 1) & 1)
        for x in range(4)
    )
    assert nonlinear not in affine_scalar_tables
    print("NONLINEAR-AND-OUTSIDE-AFFINE=1")

    print("STATUS=PASS-EXHAUSTIVE-GF2-AFFINE-GENERATOR-SEARCH")
    print("MINIMUM-GENERATOR-CARDINALITY=3")
    print("WARNING=MIN-CARDINALITY-IS-NOT-A-SEMANTIC-OR-PERF-WINNER")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
