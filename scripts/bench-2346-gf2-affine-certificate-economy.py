#!/usr/bin/env python3
"""#2346: shortest generator paths vs direct GF(2)^2 affine coordinates.

Deterministic payload accounting only. This intentionally separates:
- semantic generator count;
- identity/path payload;
- full certificate metadata.
"""

from __future__ import annotations

from collections import Counter, deque
import heapq
from math import ceil, log2

Coord = tuple[int, int]
IDENTITY: Coord = (0b1001, 0b00)
COORDS: tuple[Coord, ...] = tuple(
    (matrix, offset)
    for matrix in range(16)
    for offset in range(4)
)
INDEX = {coord: i for i, coord in enumerate(COORDS)}


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


COMPOSE_INDEX = tuple(
    tuple(INDEX[compose(outer, inner)] for inner in COORDS)
    for outer in COORDS
)


def shortest_paths(
    generators: tuple[Coord, ...],
) -> tuple[dict[int, int], dict[int, tuple[int, ...]], dict[int, int]]:
    """BFS by left-appending generators.

    Generator order is a benchmark convention only, used to select one
    canonical shortest path when several exist.
    """
    generator_indices = tuple(INDEX[g] for g in generators)
    start = INDEX[IDENTITY]

    distance = {start: 0}
    canonical = {start: tuple()}
    shortest_count = {start: 1}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        next_depth = distance[current] + 1

        for symbol, generator in enumerate(generator_indices):
            nxt = COMPOSE_INDEX[generator][current]

            if nxt not in distance:
                distance[nxt] = next_depth
                canonical[nxt] = canonical[current] + (symbol,)
                shortest_count[nxt] = shortest_count[current]
                queue.append(nxt)
            elif distance[nxt] == next_depth:
                shortest_count[nxt] += shortest_count[current]

    assert len(distance) == 64
    return distance, canonical, shortest_count


def huffman_lengths(weights: dict[int, int]) -> dict[int, int]:
    """Return deterministic optimal binary prefix-code lengths."""
    if len(weights) == 1:
        only = next(iter(weights))
        return {only: 1}

    heap = []
    serial = 0
    for symbol in sorted(weights):
        heapq.heappush(heap, (weights[symbol], serial, (symbol,)))
        serial += 1

    lengths = {symbol: 0 for symbol in weights}

    while len(heap) > 1:
        w1, _, symbols1 = heapq.heappop(heap)
        w2, _, symbols2 = heapq.heappop(heap)

        for symbol in symbols1:
            lengths[symbol] += 1
        for symbol in symbols2:
            lengths[symbol] += 1

        merged = symbols1 + symbols2
        heapq.heappush(heap, (w1 + w2, serial, merged))
        serial += 1

    return lengths


def report_basis(name: str, generators: tuple[Coord, ...]) -> dict[str, float | int]:
    distance, canonical, shortest_count = shortest_paths(generators)

    symbol_frequency = Counter(
        symbol
        for path in canonical.values()
        for symbol in path
    )
    total_symbols = sum(symbol_frequency.values())

    fixed_symbol_bits = ceil(log2(len(generators)))
    fixed_payload_bits = total_symbols * fixed_symbol_bits

    lengths = huffman_lengths(dict(symbol_frequency))
    huffman_payload_bits = sum(
        symbol_frequency[symbol] * lengths[symbol]
        for symbol in symbol_frequency
    )

    ambiguous_functions = sum(
        1 for count in shortest_count.values() if count > 1
    )
    total_shortest_paths = sum(shortest_count.values())
    max_multiplicity = max(shortest_count.values())

    print(f"BASIS={name}")
    print(f"GENERATOR-COUNT={len(generators)}")
    print(f"TOTAL-SHORTEST-SYMBOLS={total_symbols}")
    print(f"AVERAGE-SHORTEST-DEPTH={total_symbols / 64.0:.6f}")
    print(f"MAX-SHORTEST-DEPTH={max(distance.values())}")
    print(
        "GENERATOR-FREQUENCY="
        + ",".join(
            f"{symbol}:{symbol_frequency[symbol]}"
            for symbol in sorted(symbol_frequency)
        )
    )
    print(
        "HUFFMAN-CODE-LENGTHS="
        + ",".join(
            f"{symbol}:{lengths[symbol]}"
            for symbol in sorted(lengths)
        )
    )
    print(f"FIXED-SYMBOL-BITS={fixed_symbol_bits}")
    print(f"FIXED-PATH-PAYLOAD-BITS={fixed_payload_bits}")
    print(f"FIXED-AVERAGE-BITS-PER-FUNCTION={fixed_payload_bits / 64.0:.6f}")
    print(f"HUFFMAN-PATH-PAYLOAD-BITS={huffman_payload_bits}")
    print(f"HUFFMAN-AVERAGE-BITS-PER-FUNCTION={huffman_payload_bits / 64.0:.6f}")
    print(f"AMBIGUOUS-SHORTEST-FUNCTIONS={ambiguous_functions}")
    print(f"TOTAL-SHORTEST-PATHS={total_shortest_paths}")
    print(f"MAX-SHORTEST-PATH-MULTIPLICITY={max_multiplicity}")

    return {
        "fixed_bits": fixed_payload_bits,
        "huffman_bits": huffman_payload_bits,
        "ambiguous": ambiguous_functions,
        "total_shortest_paths": total_shortest_paths,
        "max_multiplicity": max_multiplicity,
    }


def main() -> None:
    direct_per_function = 6
    direct_total = 64 * direct_per_function

    print(f"DIRECT-COORD-BITS-PER-FUNCTION={direct_per_function}")
    print(f"DIRECT-CORPUS-PAYLOAD-BITS={direct_total}")

    minimum3: tuple[Coord, ...] = (
        (0b0001, 0b00),
        (0b0110, 0b00),
        (0b0111, 0b10),
    )
    factorized4: tuple[Coord, ...] = (
        (0b0001, 0b00),  # projection
        (0b0110, 0b00),  # coordinate swap
        (0b1011, 0b00),  # shear
        (0b1001, 0b01),  # unit translation
    )

    min_result = report_basis("MIN-CARDINALITY-3", minimum3)
    fact_result = report_basis("FACTORIZED-4", factorized4)

    assert min_result["fixed_bits"] == 484
    assert min_result["huffman_bits"] == 368
    assert min_result["ambiguous"] == 8
    assert min_result["total_shortest_paths"] == 73
    assert min_result["max_multiplicity"] == 3

    assert fact_result["fixed_bits"] == 456
    assert fact_result["huffman_bits"] == 456
    assert fact_result["ambiguous"] == 34
    assert fact_result["total_shortest_paths"] == 127
    assert fact_result["max_multiplicity"] == 8

    print(f"MIN3-HUFFMAN-DELTA-VS-DIRECT={min_result['huffman_bits'] - direct_total}")
    print(f"MIN3-FIXED-DELTA-VS-DIRECT={min_result['fixed_bits'] - direct_total}")
    print(f"FACT4-DELTA-VS-DIRECT={fact_result['fixed_bits'] - direct_total}")

    print(
        "EXCLUDED-FULL-CERTIFICATE-OVERHEAD="
        "basis-id,carrier-types,law-ids,boundary,proof-hash,validation"
    )
    print("CANONICAL-BFS-ORDER=BENCHMARK-CONVENTION-NOT-SEMANTIC-AUTHORITY")
    print("STATUS=PASS-GF2-AFFINE-CERTIFICATE-PAYLOAD-ACCOUNTING")
    print("AUTHORITY=BENCH-ONLY")


if __name__ == "__main__":
    main()
