#!/usr/bin/env python3
"""#2307: distinguish semantic bits from merely binary-encoded coordinates.

Research only. No production identity allocation.

Positive controls:
- ORDER/V4: two action bits, composition by XOR (B3 candidate).
- MOBIUS/P1(Q): exact projective coordinate, composition by matrix multiply
  (B1 coordinate algebra; no simple bitwise claim).

Negative control:
- arbitrary 2-bit labels for four unrelated functions: compact binary labels
  without a semantic operation are not B2/B3 evidence.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product

Q = tuple(sorted({
    Fraction(n, d)
    for n in range(-3, 4)
    for d in range(1, 4)
}))

I, S, N, NS = 0b00, 0b01, 0b10, 0b11


def order_action(code: int, a: Fraction, b: Fraction) -> bool:
    if code & S:
        a, b = b, a
    out = a < b
    if code & N:
        out = not out
    return out


def verify_order_b3() -> tuple[int, int]:
    relation_cases = 0
    composition_cases = 0
    for a, b in product(Q, repeat=2):
        expected = {
            I: a < b,
            S: a > b,
            N: a >= b,
            NS: a <= b,
        }
        for code, value in expected.items():
            assert order_action(code, a, b) == value
            relation_cases += 1

        for x, y in product((I, S, N, NS), repeat=2):
            # S and N are commuting involutions, so action composition is XOR.
            composed = x ^ y
            # verify through the independently stated parity of action bits
            swap = bool(x & S) ^ bool(y & S)
            neg = bool(x & N) ^ bool(y & N)
            aa, bb = (b, a) if swap else (a, b)
            semantic = aa < bb
            if neg:
                semantic = not semantic
            assert semantic == order_action(composed, a, b)
            composition_cases += 1
    return relation_cases, composition_cases


Matrix = tuple[Fraction, Fraction, Fraction, Fraction]
INF = "inf"
MI: Matrix = (Fraction(1), Fraction(0), Fraction(0), Fraction(1))


def mmul(a: Matrix, b: Matrix) -> Matrix:
    a11,a12,a21,a22 = a
    b11,b12,b21,b22 = b
    return (
        a11*b11+a12*b21,
        a11*b12+a12*b22,
        a21*b11+a22*b21,
        a21*b12+a22*b22,
    )


def mapply(m: Matrix, x: Fraction | str) -> Fraction | str:
    a,b,c,d = m
    if x == INF:
        return INF if c == 0 else a/c
    assert isinstance(x, Fraction)
    den = c*x+d
    return INF if den == 0 else (a*x+b)/den


def det(m: Matrix) -> Fraction:
    a,b,c,d = m
    return a*d-b*c


MATS: tuple[Matrix, ...] = tuple(
    m
    for m in (
        (Fraction(1),Fraction(1),Fraction(0),Fraction(1)),  # x+1
        (Fraction(2),Fraction(0),Fraction(0),Fraction(1)),  # 2x
        (Fraction(0),Fraction(1),Fraction(1),Fraction(0)),  # 1/x
        (Fraction(-1),Fraction(0),Fraction(0),Fraction(1)), # -x
        (Fraction(1),Fraction(1),Fraction(1),Fraction(2)),
    )
    if det(m) != 0
)


def verify_mobius_b1() -> int:
    cases = 0
    for a, b in product(MATS, repeat=2):
        ab = mmul(a, b)
        for x in Q + (INF,):
            assert mapply(a, mapply(b, x)) == mapply(ab, x)
            cases += 1
    return cases


def arbitrary_label_negative_control() -> int:
    # Four unrelated semantic tables can be assigned compact 2-bit labels,
    # but XOR of labels has no independently defined semantic meaning.
    funcs = {
        0b00: lambda x: x + 1,
        0b01: lambda x: x * x,
        0b10: lambda x: Fraction(0),
        0b11: lambda x: -x + 2,
    }
    mismatches = 0
    for c1, c2 in product(funcs, repeat=2):
        derived = c1 ^ c2
        for x in Q:
            semantic_composition = funcs[c1](funcs[c2](x))
            arbitrary_xor_target = funcs[derived](x)
            if semantic_composition != arbitrary_xor_target:
                mismatches += 1
    assert mismatches > 0
    return mismatches


def main() -> None:
    order_rel, order_comp = verify_order_b3()
    mobius_comp = verify_mobius_b1()
    negative = arbitrary_label_negative_control()

    print("FAMILY=ORDER-V4")
    print("CLASS=B3")
    print(f"RELATION-CASES={order_rel}")
    print(f"XOR-COMPOSITION-CASES={order_comp}")
    print("BIT0=SWAP-ARGS")
    print("BIT1=NEGATE-PREDICATE")
    print("COORDINATE-OP=XOR")
    print("SEMANTIC-OP=ACTION-COMPOSITION")

    print("FAMILY=MOBIUS-P1Q")
    print("CLASS=B1")
    print(f"MATRIX-COMPOSITION-CASES={mobius_comp}")
    print("BINARY-REPRESENTATION=EXACT-RATIONAL-MATRIX-COEFFICIENTS")
    print("COORDINATE-OP=MATRIX-MULTIPLICATION")
    print("SIMPLE-BITWISE-CLAIM=NONE")

    print("FAMILY=ARBITRARY-2BIT-LABELS")
    print("CLASS=B0")
    print(f"XOR-MISMATCHES={negative}")
    print("SEMANTIC-BIT-LAW=ABSENT")

    print("STATUS=PASS-BINARY-SEMANTIC-NATURALNESS-CONTROLS")
    print("PRINCIPLE=BINARY-ENCODED-DOES-NOT-IMPLY-BITWISE-SEMANTIC")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
