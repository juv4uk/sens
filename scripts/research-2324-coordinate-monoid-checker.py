#!/usr/bin/env python3
"""#2324 generic coordinate-composition checker.

Research only. One checker validates several structurally different local
function-coordinate algebras through the same laws:

  T(e) = id
  T(c1 ⊗ c2) = T(c1) ∘ T(c2)
  (c1 ⊗ c2) ⊗ c3 = c1 ⊗ (c2 ⊗ c3)

This is a shared verification interface, not a claim that every family uses
the same concrete coordinate operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Any, Callable

Coord = Any
Value = Any


@dataclass(frozen=True)
class Family:
    name: str
    carrier: str
    binary_class: str
    coords: tuple[Coord, ...]
    samples: tuple[Value, ...]
    identity: Coord
    compose: Callable[[Coord, Coord], Coord]
    apply: Callable[[Coord, Value], Value]
    coord_equal: Callable[[Coord, Coord], bool] = lambda a, b: a == b
    valid_coord: Callable[[Coord], bool] = lambda _c: True


def verify_family(f: Family) -> dict[str, int]:
    identity_cases = 0
    homomorphism_cases = 0
    associativity_cases = 0
    closure_cases = 0

    assert f.valid_coord(f.identity)

    for c in f.coords:
        left = f.compose(f.identity, c)
        right = f.compose(c, f.identity)
        assert f.valid_coord(left)
        assert f.valid_coord(right)
        assert f.coord_equal(left, c)
        assert f.coord_equal(right, c)
        identity_cases += 2

        for x in f.samples:
            assert f.apply(f.identity, x) == x

    for a, b in product(f.coords, repeat=2):
        composed = f.compose(a, b)
        assert f.valid_coord(composed)
        closure_cases += 1
        for x in f.samples:
            lhs = f.apply(composed, x)
            rhs = f.apply(a, f.apply(b, x))
            assert lhs == rhs, (f.name, a, b, x, lhs, rhs)
            homomorphism_cases += 1

    for a, b, c in product(f.coords, repeat=3):
        lhs = f.compose(f.compose(a, b), c)
        rhs = f.compose(a, f.compose(b, c))
        assert f.valid_coord(lhs)
        assert f.valid_coord(rhs)
        assert f.coord_equal(lhs, rhs), (f.name, a, b, c, lhs, rhs)
        associativity_cases += 1

    return {
        "identity_cases": identity_cases,
        "homomorphism_cases": homomorphism_cases,
        "associativity_cases": associativity_cases,
        "closure_cases": closure_cases,
    }


# ---------------------------------------------------------------------------
# Selector free-path monoid
# ---------------------------------------------------------------------------

def make_tree(depth: int, prefix: str = "") -> object:
    if depth == 0:
        return prefix or "root"
    return (
        make_tree(depth - 1, prefix + "0"),
        make_tree(depth - 1, prefix + "1"),
    )


TREE = make_tree(7)


def selector_apply(path: str, value: object) -> object:
    out = value
    for bit in reversed(path):
        assert isinstance(out, tuple) and len(out) == 2
        out = out[0] if bit == "0" else out[1]
    return out


SELECTOR = Family(
    name="selector-path",
    carrier="BinaryTree",
    binary_class="B3",
    coords=("", "0", "1", "00", "01", "10", "11"),
    samples=(TREE,),
    identity="",
    compose=lambda a, b: a + b,
    apply=selector_apply,
    valid_coord=lambda c: isinstance(c, str) and set(c) <= {"0", "1"},
)


# ---------------------------------------------------------------------------
# V4 action monoid over order-action state
# ---------------------------------------------------------------------------

I, S, N, NS = 0b00, 0b01, 0b10, 0b11

Q_SMALL = (Fraction(-1), Fraction(0), Fraction(1))
V4_STATES = tuple((a, b, p) for a, b, p in product(Q_SMALL, Q_SMALL, (0, 1)))


def v4_apply(code: int, state: tuple[Fraction, Fraction, int]):
    a, b, polarity = state
    if code & S:
        a, b = b, a
    if code & N:
        polarity ^= 1
    return a, b, polarity


V4 = Family(
    name="order-v4-action",
    carrier="QxQxPredicatePolarity",
    binary_class="B3",
    coords=(I, S, N, NS),
    samples=V4_STATES,
    identity=I,
    compose=lambda a, b: a ^ b,
    apply=v4_apply,
    valid_coord=lambda c: isinstance(c, int) and 0 <= c < 4,
)


# ---------------------------------------------------------------------------
# Unary PredicateBit affine monoid
# ---------------------------------------------------------------------------

def bit_affine_apply(code: int, x: int) -> int:
    a = (code >> 1) & 1
    b = code & 1
    return (a & x) ^ b


def bit_affine_compose(outer: int, inner: int) -> int:
    a = (outer >> 1) & 1
    b = outer & 1
    c = (inner >> 1) & 1
    d = inner & 1
    return ((a & c) << 1) | ((a & d) ^ b)


BIT_AFFINE = Family(
    name="predicatebit-affine",
    carrier="GF2",
    binary_class="B3",
    coords=(0b00, 0b01, 0b10, 0b11),
    samples=(0, 1),
    identity=0b10,
    compose=bit_affine_compose,
    apply=bit_affine_apply,
    valid_coord=lambda c: isinstance(c, int) and 0 <= c < 4,
)


# ---------------------------------------------------------------------------
# GF(2)^2 affine monoid
# ---------------------------------------------------------------------------

def mbit(matrix: int, row: int, col: int) -> int:
    return (matrix >> (row * 2 + col)) & 1


def mvec(matrix: int, vector: int) -> int:
    x0 = vector & 1
    x1 = (vector >> 1) & 1
    y0 = (mbit(matrix, 0, 0) & x0) ^ (mbit(matrix, 0, 1) & x1)
    y1 = (mbit(matrix, 1, 0) & x0) ^ (mbit(matrix, 1, 1) & x1)
    return y0 | (y1 << 1)


def mmul2(left: int, right: int) -> int:
    out = 0
    for row in range(2):
        for col in range(2):
            value = 0
            for k in range(2):
                value ^= mbit(left, row, k) & mbit(right, k, col)
            out |= value << (row * 2 + col)
    return out


def affine2_apply(coord: tuple[int, int], x: int) -> int:
    matrix, offset = coord
    return mvec(matrix, x) ^ offset


def affine2_compose(
    outer: tuple[int, int], inner: tuple[int, int]
) -> tuple[int, int]:
    a, b = outer
    c, d = inner
    return mmul2(a, c), mvec(a, d) ^ b


AFFINE2_COORDS = tuple(
    (matrix, offset)
    for matrix in range(16)
    for offset in range(4)
)

AFFINE2 = Family(
    name="gf2-affine-n2",
    carrier="GF2^2",
    binary_class="B3",
    coords=AFFINE2_COORDS,
    samples=(0, 1, 2, 3),
    identity=(0b1001, 0),
    compose=affine2_compose,
    apply=affine2_apply,
    valid_coord=lambda c: (
        isinstance(c, tuple)
        and len(c) == 2
        and 0 <= c[0] < 16
        and 0 <= c[1] < 4
    ),
)


# ---------------------------------------------------------------------------
# Möbius / P1(Q) projective matrix monoid sample
# ---------------------------------------------------------------------------

Matrix = tuple[Fraction, Fraction, Fraction, Fraction]
INF = "inf"
MID: Matrix = (
    Fraction(1), Fraction(0), Fraction(0), Fraction(1)
)


def mmulq(a: Matrix, b: Matrix) -> Matrix:
    a11,a12,a21,a22 = a
    b11,b12,b21,b22 = b
    return (
        a11*b11+a12*b21,
        a11*b12+a12*b22,
        a21*b11+a22*b21,
        a21*b12+a22*b22,
    )


def mdet(m: Matrix) -> Fraction:
    a,b,c,d = m
    return a*d-b*c


def mobius_apply(m: Matrix, x: Fraction | str) -> Fraction | str:
    a,b,c,d = m
    if x == INF:
        return INF if c == 0 else a/c
    assert isinstance(x, Fraction)
    den = c*x+d
    return INF if den == 0 else (a*x+b)/den


def canonical_projective(m: Matrix) -> tuple[Fraction, ...]:
    for value in m:
        if value != 0:
            return tuple(x / value for x in m)
    raise AssertionError("zero matrix")


MOBIUS_COORDS: tuple[Matrix, ...] = (
    MID,
    (Fraction(1),Fraction(1),Fraction(0),Fraction(1)),
    (Fraction(2),Fraction(0),Fraction(0),Fraction(1)),
    (Fraction(0),Fraction(1),Fraction(1),Fraction(0)),
    (Fraction(-1),Fraction(0),Fraction(0),Fraction(1)),
    (Fraction(1),Fraction(1),Fraction(1),Fraction(2)),
)

MOBIUS = Family(
    name="mobius-p1q",
    carrier="P1(Q)",
    binary_class="B1",
    coords=MOBIUS_COORDS,
    samples=(Fraction(-1), Fraction(0), Fraction(1), INF),
    identity=MID,
    compose=mmulq,
    apply=mobius_apply,
    coord_equal=lambda a, b: canonical_projective(a) == canonical_projective(b),
    valid_coord=lambda c: isinstance(c, tuple) and len(c) == 4 and mdet(c) != 0,
)


FAMILIES = (SELECTOR, V4, BIT_AFFINE, AFFINE2, MOBIUS)



@dataclass(frozen=True)
class Morphism:
    name: str
    source: str
    target: str
    apply: Callable[[Value], Value]


def compose_morphism(outer: Morphism, inner: Morphism, name: str) -> Morphism:
    if inner.target != outer.source:
        raise TypeError(
            f"cannot compose {outer.name}:{outer.source}->{outer.target} "
            f"after {inner.name}:{inner.source}->{inner.target}"
        )
    return Morphism(
        name=name,
        source=inner.source,
        target=outer.target,
        apply=lambda x: outer.apply(inner.apply(x)),
    )


def euclidean_divmod(a: int, b: int) -> tuple[int, int]:
    if b == 0:
        raise ZeroDivisionError("divmod by zero")
    d = abs(b)
    q_pos = a // d
    r = a - d * q_pos
    q = q_pos if b > 0 else -q_pos
    assert a == b * q + r
    assert 0 <= r < d
    return q, r


def verify_typed_composition_graph() -> dict[str, int]:
    order_cases = 0
    structural_cases = 0
    associativity_cases = 0
    type_rejections = 0

    swap = Morphism(
        "SWAP",
        "QxQ",
        "QxQ",
        lambda pair: (pair[1], pair[0]),
    )
    lt = Morphism(
        "LT",
        "QxQ",
        "PredicateBit",
        lambda pair: pair[0] < pair[1],
    )
    not_bit = Morphism(
        "NOT",
        "PredicateBit",
        "PredicateBit",
        lambda value: not value,
    )

    gt = compose_morphism(lt, swap, "GT")
    ge = compose_morphism(not_bit, lt, "GE")
    le_left = compose_morphism(
        compose_morphism(not_bit, lt, "NOT∘LT"),
        swap,
        "LE-left",
    )
    le_right = compose_morphism(
        not_bit,
        compose_morphism(lt, swap, "LT∘SWAP"),
        "LE-right",
    )

    for a, b in product(Q_SMALL, repeat=2):
        pair = (a, b)
        assert gt.apply(pair) == (a > b)
        assert ge.apply(pair) == (a >= b)
        assert le_left.apply(pair) == (a <= b)
        assert le_right.apply(pair) == (a <= b)
        assert le_left.apply(pair) == le_right.apply(pair)
        order_cases += 4
        associativity_cases += 1

    divmod_m = Morphism(
        "DIVMOD",
        "ZxZ_nonzero_divisor",
        "PairZZ",
        lambda pair: euclidean_divmod(pair[0], pair[1]),
    )
    car = Morphism("CAR", "PairZZ", "Z", lambda pair: pair[0])
    cdr = Morphism("CDR", "PairZZ", "Z", lambda pair: pair[1])
    quotient = compose_morphism(car, divmod_m, "QUOTIENT")
    remainder = compose_morphism(cdr, divmod_m, "REMAINDER")

    for a in range(-8, 9):
        for b in range(-4, 5):
            if b == 0:
                continue
            q, r = euclidean_divmod(a, b)
            assert quotient.apply((a, b)) == q
            assert remainder.apply((a, b)) == r
            assert a == b * q + r
            assert 0 <= r < abs(b)
            structural_cases += 2

    try:
        compose_morphism(swap, lt, "ILL-TYPED")
    except TypeError:
        type_rejections += 1
    else:
        raise AssertionError("ill-typed composition must be rejected")

    return {
        "order_typed_cases": order_cases,
        "structural_typed_cases": structural_cases,
        "typed_associativity_cases": associativity_cases,
        "type_rejections": type_rejections,
    }


TYPED_GRAPH_EDGES = (
    ("QxQ", "QxQ", "SWAP"),
    ("QxQ", "PredicateBit", "LT"),
    ("PredicateBit", "PredicateBit", "NOT"),
    ("ZxZ_nonzero_divisor", "PairZZ", "DIVMOD"),
    ("PairZZ", "Z", "CAR"),
    ("PairZZ", "Z", "CDR"),
)


def main() -> None:
    total_hom = 0
    total_assoc = 0

    print("COORDINATE-FAMILY-GRAPH:")
    for family in FAMILIES:
        result = verify_family(family)
        total_hom += result["homomorphism_cases"]
        total_assoc += result["associativity_cases"]
        print(
            f"family={family.name} "
            f"carrier={family.carrier} "
            f"binary_class={family.binary_class} "
            f"coords_sampled={len(family.coords)} "
            f"identity_cases={result['identity_cases']} "
            f"closure_cases={result['closure_cases']} "
            f"homomorphism_cases={result['homomorphism_cases']} "
            f"associativity_cases={result['associativity_cases']}"
        )

    typed = verify_typed_composition_graph()
    print("TYPED-CARRIER-GRAPH:")
    for source, target, name in TYPED_GRAPH_EDGES:
        print(f"  {source} --{name}--> {target}")
    for key, value in typed.items():
        print(f"{key.upper().replace('_', '-')}={value}")

    print(f"FAMILIES-CHECKED={len(FAMILIES)}")
    print(f"TOTAL-HOMOMORPHISM-CASES={total_hom}")
    print(f"TOTAL-ASSOCIATIVITY-CASES={total_assoc}")
    print("COMMON-LAW=T(c1⊗c2)=T(c1)∘T(c2)")
    print("COMMON-IDENTITY-LAW=T(e)=id")
    print("GLOBAL-MODEL=TYPED-LOCAL-COMPOSITION-STRUCTURES")
    print("CROSS-CARRIER-WITNESSES=SWAP/LT/NOT,DIVMOD/CAR/CDR")
    print("STATUS=PASS-GENERIC-COORDINATE-CHECKER")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
