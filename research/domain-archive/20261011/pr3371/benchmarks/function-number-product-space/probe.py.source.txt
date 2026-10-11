#!/usr/bin/env python3
"""#3369 — exact-width product-space algebra.

Functions are exact-width binary numbers.  This probe never uses resident names.

For n in {3,4}, prove exhaustively that W(2n) is the exact ordered-pair space
Wn × Wn under concat/split, and characterize which arithmetic operations
factor componentwise and which couple the halves.
"""

from __future__ import annotations

import json


def pair(a: int, b: int, n: int) -> int:
    return (a << n) | b


def split(x: int, n: int) -> tuple[int, int]:
    mask = (1 << n) - 1
    return x >> n, x & mask


def mask(n: int) -> int:
    return (1 << n) - 1


def popcount(x: int) -> int:
    return x.bit_count()


def analyze(n: int) -> dict:
    B = 1 << n
    W = 2 * n
    vals = range(B)
    wide_vals = range(1 << W)

    # pair/split bijection
    pair_outputs = set()
    roundtrip_pair = 0
    for a in vals:
        for b in vals:
            x = pair(a, b, n)
            pair_outputs.add(x)
            assert split(x, n) == (a, b)
            roundtrip_pair += 1

    roundtrip_split = 0
    for x in wide_vals:
        assert pair(*split(x, n), n) == x
        roundtrip_split += 1

    # Exhaustive algebra over all pairs of W(2n) elements.
    binary_cases = 0
    xor_matches = 0
    and_matches = 0
    or_matches = 0
    hamming_matches = 0
    lex_order_matches = 0

    add_exact_matches = 0
    naive_component_add_matches = 0
    naive_component_add_failures = 0
    low_carry_cases = 0

    mul_polynomial_matches = 0

    for a in vals:
        for b in vals:
            x = pair(a, b, n)
            for c in vals:
                for d in vals:
                    y = pair(c, d, n)
                    binary_cases += 1

                    if (x ^ y) == pair(a ^ c, b ^ d, n):
                        xor_matches += 1
                    if (x & y) == pair(a & c, b & d, n):
                        and_matches += 1
                    if (x | y) == pair(a | c, b | d, n):
                        or_matches += 1

                    if popcount(x ^ y) == popcount(a ^ c) + popcount(b ^ d):
                        hamming_matches += 1

                    lex = (a < c) or (a == c and b < d)
                    if (x < y) == lex:
                        lex_order_matches += 1

                    # Full addition W(2n)×W(2n) -> W(2n+1).
                    low_sum = b + d
                    low = low_sum & (B - 1)
                    carry = low_sum >> n
                    high = a + c + carry
                    reconstructed_sum = (high << n) | low
                    if x + y == reconstructed_sum:
                        add_exact_matches += 1

                    if carry:
                        low_carry_cases += 1

                    # False control: ignore low-half carry and wrap each half.
                    naive = pair((a + c) & (B - 1), low, n)
                    actual_mod = (x + y) & ((1 << W) - 1)
                    if naive == actual_mod:
                        naive_component_add_matches += 1
                    else:
                        naive_component_add_failures += 1

                    # Exact multiplication polynomial.
                    # (aB+b)(cB+d) = ac B² + (ad+bc) B + bd
                    polynomial = (a * c << (2 * n)) + ((a * d + b * c) << n) + b * d
                    if x * y == polynomial:
                        mul_polynomial_matches += 1

    unary_cases = 0
    not_matches = 0
    popcount_matches = 0
    for a in vals:
        for b in vals:
            x = pair(a, b, n)
            unary_cases += 1
            wide_not = (~x) & mask(W)
            component_not = pair((~a) & mask(n), (~b) & mask(n), n)
            if wide_not == component_not:
                not_matches += 1
            if popcount(x) == popcount(a) + popcount(b):
                popcount_matches += 1

    expected_carry_cases = B**3 * (B - 1) // 2

    report = {
        "half_width": n,
        "wide_width": W,
        "half_cardinality": B,
        "wide_cardinality": 1 << W,
        "pair_split": {
            "ordered_pairs": B * B,
            "unique_outputs": len(pair_outputs),
            "coverage": f"{len(pair_outputs)}/{1 << W}",
            "pair_then_split_matches": roundtrip_pair,
            "split_then_pair_matches": roundtrip_split,
            "bijective": len(pair_outputs) == (1 << W),
        },
        "boolean_product_algebra": {
            "binary_cases": binary_cases,
            "xor_matches": xor_matches,
            "and_matches": and_matches,
            "or_matches": or_matches,
            "not_cases": unary_cases,
            "not_matches": not_matches,
            "popcount_matches": popcount_matches,
            "hamming_distance_matches": hamming_matches,
            "lexicographic_order_matches": lex_order_matches,
        },
        "addition": {
            "full_add_width": W + 1,
            "exact_carry_equation_matches": add_exact_matches,
            "low_carry_cases": low_carry_cases,
            "expected_low_carry_cases": expected_carry_cases,
            "naive_componentwise_matches": naive_component_add_matches,
            "naive_componentwise_failures": naive_component_add_failures,
            "coupling_fraction": f"{naive_component_add_failures}/{binary_cases}",
            "equation": "pair(a,b)+pair(c,d)=((a+c+carry)<<n)|((b+d) mod 2^n)",
            "carry": "floor((b+d)/2^n)",
        },
        "multiplication": {
            "output_width": 4 * n,
            "polynomial_identity_matches": mul_polynomial_matches,
            "equation": "(a*2^n+b)(c*2^n+d)=ac*2^(2n)+(ad+bc)*2^n+bd",
        },
    }

    assert report["pair_split"]["bijective"]
    assert xor_matches == binary_cases
    assert and_matches == binary_cases
    assert or_matches == binary_cases
    assert hamming_matches == binary_cases
    assert lex_order_matches == binary_cases
    assert not_matches == unary_cases
    assert popcount_matches == unary_cases

    assert add_exact_matches == binary_cases
    assert low_carry_cases == expected_carry_cases
    assert naive_component_add_failures == expected_carry_cases

    assert mul_polynomial_matches == binary_cases

    return report


def main() -> None:
    reports = [analyze(3), analyze(4)]

    assert reports[0]["pair_split"]["coverage"] == "64/64"
    assert reports[1]["pair_split"]["coverage"] == "256/256"

    assert reports[0]["addition"]["naive_componentwise_failures"] == 1792
    assert reports[1]["addition"]["naive_componentwise_failures"] == 30720

    out = {
        "issue": "#3369",
        "classification": "EXACT PRODUCT-SPACE ALGEBRA",
        "theorems": [
            "W6 ≅ W3×W3 by concat/split",
            "W8 ≅ W4×W4 by concat/split",
            "XOR/AND/OR/NOT factor componentwise exactly",
            "popcount and Hamming distance decompose additively",
            "numeric order is lexicographic in (high,low)",
            "ADD is coupled only by the low-half carry",
            "MUL obeys the exact two-half polynomial identity",
        ],
        "domains": reports,
        "semantic_boundary": (
            "These are exact theorems about binary function numbers. "
            "They generate all W6/W8 coordinates but do not by themselves "
            "ratify semantic D6/D8 residents."
        ),
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
