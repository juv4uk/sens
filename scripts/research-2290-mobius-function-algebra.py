#!/usr/bin/env python3
"""#2290: exact-Q Möbius/function-matrix algebra witness.

Research only. No production semantic identities are allocated.

For M = [[a,b],[c,d]], define T_M(x) = (a*x+b)/(c*x+d).
The witness checks:
- T_A(T_B(x)) = T_(A*B)(x) with exact undefined-domain parity;
- projective equivalence M ~ kM;
- inverse via adjugate for det(M) != 0;
- decomposition through translation, reciprocal and scaling.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import gcd, lcm
from functools import reduce

Matrix = tuple[Fraction, Fraction, Fraction, Fraction]

Q = tuple(sorted({
    Fraction(n, d)
    for n in range(-3, 4)
    for d in range(1, 4)
}))
INF = "∞"
COEFFS = tuple(Fraction(n) for n in range(-2, 3))


def det(m: Matrix) -> Fraction:
    a, b, c, d = m
    return a*d - b*c


def mul(a: Matrix, b: Matrix) -> Matrix:
    a11,a12,a21,a22 = a
    b11,b12,b21,b22 = b
    return (
        a11*b11 + a12*b21,
        a11*b12 + a12*b22,
        a21*b11 + a22*b21,
        a21*b12 + a22*b22,
    )


def apply(m: Matrix, x: Fraction) -> Fraction | None:
    """Finite-Q partial semantics."""
    a,b,c,d = m
    den = c*x + d
    if den == 0:
        return None
    return (a*x + b) / den


def apply_p1(m: Matrix, x: Fraction | str) -> Fraction | str:
    """Projective-line semantics Q ∪ {∞} for invertible matrices."""
    a,b,c,d = m
    if x == INF:
        if c == 0:
            return INF
        return a / c
    assert isinstance(x, Fraction)
    den = c*x + d
    if den == 0:
        return INF
    return (a*x + b) / den


def canonical(m: Matrix) -> tuple[int, int, int, int]:
    """Canonical primitive-integer representative of a projective class."""
    den_lcm = 1
    for value in m:
        den_lcm = lcm(den_lcm, value.denominator)
    ints = [int(value * den_lcm) for value in m]
    g = reduce(gcd, (abs(v) for v in ints if v != 0), 0)
    if g:
        ints = [v // g for v in ints]
    for v in ints:
        if v != 0:
            if v < 0:
                ints = [-x for x in ints]
            break
    return tuple(ints)  # type: ignore[return-value]


I: Matrix = (Fraction(1),Fraction(0),Fraction(0),Fraction(1))
R: Matrix = (Fraction(0),Fraction(1),Fraction(1),Fraction(0))


def translation(t: Fraction) -> Matrix:
    return (Fraction(1), t, Fraction(0), Fraction(1))


def scaling(s: Fraction) -> Matrix:
    return (s, Fraction(0), Fraction(0), Fraction(1))


def compose_chain(*matrices: Matrix) -> Matrix:
    out = I
    for m in matrices:
        out = mul(m, out)
    return out


def decompose(m: Matrix) -> Matrix:
    """Rebuild projectively from translation/scaling/reciprocal generators."""
    a,b,c,d = m
    if det(m) == 0:
        raise ValueError("singular")
    if c == 0:
        # (a*x+b)/d = (a/d)*x + b/d
        return compose_chain(scaling(a/d), translation(b/d))

    # T_M(x) = a/c + ((b*c-a*d)/c^2) * 1/(x + d/c)
    t1 = translation(d/c)
    r = R
    s = scaling((b*c - a*d)/(c*c))
    t2 = translation(a/c)
    return compose_chain(t1, r, s, t2)


def matrices() -> tuple[Matrix, ...]:
    out = []
    for values in product(COEFFS, repeat=4):
        m = tuple(values)  # type: ignore[assignment]
        if any(v != 0 for v in m) and det(m) != 0:
            out.append(m)  # type: ignore[arg-type]
    # canonical de-dup so projective duplicates do not dominate the corpus
    uniq = {}
    for m in out:
        uniq.setdefault(canonical(m), m)
    return tuple(uniq.values())


MS = matrices()


def verify_projective() -> int:
    cases = 0
    for m in MS:
        for k in (Fraction(-3), Fraction(-1), Fraction(2), Fraction(3,2)):
            km = tuple(k*x for x in m)  # type: ignore[assignment]
            assert canonical(km) == canonical(m)
            for x in Q:
                assert apply(km, x) == apply(m, x)
                cases += 1
    return cases


def verify_composition() -> tuple[int,int,int,int]:
    finite_common = 0
    finite_pole = 0
    pole_recovered_via_infinity = 0
    projective_cases = 0
    sample = MS[:80]
    p1_inputs = Q + (INF,)

    for a,b in product(sample, repeat=2):
        ab = mul(a,b)

        for x in Q:
            bx = apply(b,x)
            lhs = None if bx is None else apply(a,bx)
            rhs = apply(ab,x)
            if lhs is None:
                finite_pole += 1
                if rhs is not None:
                    pole_recovered_via_infinity += 1
            else:
                assert lhs == rhs, (a,b,x,lhs,rhs)
                finite_common += 1

        for x in p1_inputs:
            lhs_p1 = apply_p1(a, apply_p1(b,x))
            rhs_p1 = apply_p1(ab,x)
            assert lhs_p1 == rhs_p1, (a,b,x,lhs_p1,rhs_p1)
            projective_cases += 1

    assert pole_recovered_via_infinity > 0
    return (
        finite_common,
        finite_pole,
        pole_recovered_via_infinity,
        projective_cases,
    )


def verify_inverse() -> tuple[int,int]:
    exact = 0
    undefined = 0
    for m in MS[:200]:
        a,b,c,d = m
        inv = (d,-b,-c,a)
        assert canonical(mul(m,inv)) == canonical(I)
        assert canonical(mul(inv,m)) == canonical(I)
        for x in Q:
            y = apply(m,x)
            if y is None:
                undefined += 1
                continue
            back = apply(inv,y)
            assert back == x
            exact += 1
    return exact, undefined


def verify_decomposition() -> tuple[int,int]:
    matrix_cases = 0
    value_cases = 0
    for m in MS:
        rebuilt = decompose(m)
        assert canonical(rebuilt) == canonical(m), (m, rebuilt)
        matrix_cases += 1
        for x in Q:
            assert apply(rebuilt,x) == apply(m,x)
            value_cases += 1
    return matrix_cases, value_cases


def main() -> None:
    projective = verify_projective()
    (
        comp_finite_common,
        comp_finite_poles,
        comp_pole_recovered,
        comp_projective,
    ) = verify_composition()
    inv_exact, inv_undefined = verify_inverse()
    dec_m, dec_v = verify_decomposition()

    print(f"Q-CORPUS={len(Q)}")
    print(f"PROJECTIVE-CLASSES={len(MS)}")
    print(f"PROJECTIVE-EQUIVALENCE-CASES={projective}")
    print(f"FINITE-Q-COMPOSITION-COMMON-DOMAIN-CASES={comp_finite_common}")
    print(f"FINITE-Q-INTERMEDIATE-POLE-CASES={comp_finite_poles}")
    print(f"FINITE-Q-POLE-RECOVERED-VIA-INFINITY={comp_pole_recovered}")
    print(f"P1-COMPOSITION-CASES={comp_projective}")
    print(f"INVERSE-EXACT-CASES={inv_exact}")
    print(f"INVERSE-UNDEFINED-INPUTS={inv_undefined}")
    print(f"DECOMPOSITION-MATRIX-CASES={dec_m}")
    print(f"DECOMPOSITION-VALUE-CASES={dec_v}")
    print("LAW-P1=T_A∘T_B=T_(A*B)")
    print("FINITE-Q-BOUNDARY=NOT-CLOSED-UNDER-MOBIUS-COMPOSITION")
    print("NATURAL-CARRIER=P1(Q)=Q∪{∞}")
    print("GENERATORS=TRANSLATION,SCALING,RECIPROCAL")
    print("COORDINATE=PROJECTIVE-2X2-EXACT-Q-MATRIX")
    print("STATUS=PASS-BOUNDED-MOBIUS-FUNCTION-ALGEBRA")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
