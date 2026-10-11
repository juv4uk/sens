#!/usr/bin/env python3
"""#2325 deterministic mechanism accounting for GF(2)^n affine composition.

Research/benchmark only. No production identity allocation and no wall-clock
superiority claim.

Compare:
  flat function-composition relation
vs
  direct affine coordinate composition.

Flat control receives the ideal packed-result lower bound.
"""

from __future__ import annotations

from itertools import product


def bit(matrix: int, n: int, row: int, col: int) -> int:
    return (matrix >> (row * n + col)) & 1


def mat_vec(matrix: int, vector: int, n: int) -> int:
    out = 0
    for row in range(n):
        value = 0
        for col in range(n):
            value ^= bit(matrix, n, row, col) & ((vector >> col) & 1)
        out |= value << row
    return out


def mat_mul(left: int, right: int, n: int) -> int:
    out = 0
    for row in range(n):
        for col in range(n):
            value = 0
            for k in range(n):
                value ^= bit(left, n, row, k) & bit(right, n, k, col)
            out |= value << (row * n + col)
    return out


def affine_apply(coord: tuple[int, int], x: int, n: int) -> int:
    matrix, offset = coord
    return mat_vec(matrix, x, n) ^ offset


def affine_compose(
    outer: tuple[int, int],
    inner: tuple[int, int],
    n: int,
) -> tuple[int, int]:
    a, b = outer
    c, d = inner
    return mat_mul(a, c, n), mat_vec(a, d, n) ^ b


def coords(n: int):
    for matrix in range(1 << (n * n)):
        for offset in range(1 << n):
            yield matrix, offset


def coord_to_index(coord: tuple[int, int], n: int) -> int:
    matrix, offset = coord
    return (matrix << n) | offset


def index_to_coord(index: int, n: int) -> tuple[int, int]:
    mask = (1 << n) - 1
    return index >> n, index & mask


def verify_exhaustive(n: int) -> dict[str, int]:
    cs = tuple(coords(n))
    width = n * n + n
    count = 1 << width
    assert len(cs) == count

    # Coordinate/index representation is exact and bijective.
    for i, c in enumerate(cs):
        assert coord_to_index(c, n) == i
        assert index_to_coord(i, n) == c

    semantic_cases = 0
    table_results: list[int] = []

    for outer, inner in product(cs, repeat=2):
        direct = affine_compose(outer, inner, n)
        direct_index = coord_to_index(direct, n)
        table_results.append(direct_index)

        for x in range(1 << n):
            lhs = affine_apply(direct, x, n)
            rhs = affine_apply(outer, affine_apply(inner, x, n), n)
            assert lhs == rhs
            semantic_cases += 1

    # Packed table lower bound is exact here because each result uses width bits.
    packed_bits = len(table_results) * width
    packed_bytes_ceil = (packed_bits + 7) // 8

    return {
        "coordinate_bits": width,
        "function_count": count,
        "table_entries": len(table_results),
        "semantic_cases": semantic_cases,
        "packed_bits": packed_bits,
        "packed_bytes_ceil": packed_bytes_ceil,
    }


def human_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    amount = float(value)
    unit = units[0]
    for candidate in units:
        unit = candidate
        if amount < 1024.0 or candidate == units[-1]:
            break
        amount /= 1024.0
    return f"{amount:.6g}{unit}"


def scaling_row(n: int) -> dict[str, int]:
    width = n * n + n
    function_count = 1 << width
    table_entries = function_count * function_count
    flat_bits = table_entries * width
    flat_bytes = (flat_bits + 7) // 8

    direct_ands = n**3 + n**2
    direct_xors = n**3

    return {
        "n": n,
        "coordinate_bits": width,
        "function_count": function_count,
        "flat_table_entries": table_entries,
        "flat_payload_bits": flat_bits,
        "flat_payload_bytes": flat_bytes,
        "direct_ands": direct_ands,
        "direct_xors": direct_xors,
    }


def main() -> None:
    for n in (1, 2):
        result = verify_exhaustive(n)
        print(
            f"EXHAUSTIVE n={n} "
            f"coord_bits={result['coordinate_bits']} "
            f"functions={result['function_count']} "
            f"entries={result['table_entries']} "
            f"semantic_cases={result['semantic_cases']} "
            f"packed_bits={result['packed_bits']} "
            f"packed_bytes_ceil={result['packed_bytes_ceil']}"
        )

    print("SCALING:")
    for n in range(1, 9):
        row = scaling_row(n)
        print(
            f"n={row['n']} "
            f"coord_bits={row['coordinate_bits']} "
            f"functions={row['function_count']} "
            f"flat_entries={row['flat_table_entries']} "
            f"flat_bits={row['flat_payload_bits']} "
            f"flat_bytes={row['flat_payload_bytes']} "
            f"flat_human={human_bytes(row['flat_payload_bytes'])} "
            f"direct_AND={row['direct_ands']} "
            f"direct_XOR={row['direct_xors']}"
        )

    # Known exact checkpoints, useful as CI assertions.
    n2 = scaling_row(2)
    assert n2["coordinate_bits"] == 6
    assert n2["function_count"] == 64
    assert n2["flat_table_entries"] == 4096
    assert n2["flat_payload_bits"] == 24576
    assert n2["flat_payload_bytes"] == 3072
    assert n2["direct_ands"] == 12
    assert n2["direct_xors"] == 8

    n3 = scaling_row(3)
    assert n3["coordinate_bits"] == 12
    assert n3["function_count"] == 4096
    assert n3["flat_table_entries"] == 16_777_216
    assert n3["flat_payload_bits"] == 201_326_592
    assert n3["flat_payload_bytes"] == 25_165_824
    assert n3["direct_ands"] == 36
    assert n3["direct_xors"] == 27

    print("STATUS=PASS-DETERMINISTIC-GF2-AFFINE-COMPOSITION-ACCOUNTING")
    print("FLAT-CONTROL=IDEAL-PACKED-RESULT-LOWER-BOUND")
    print("DIRECT-CONTROL=NAIVE-GF2-BOOLEAN-OP-COUNT")
    print("CLAIM=MECHANISM-STORAGE-SCALING-NOT-WALL-CLOCK-SUPERIORITY")
    print("AUTHORITY=BENCH-ONLY")


if __name__ == "__main__":
    main()
