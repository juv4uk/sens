#!/usr/bin/env python3
"""Bounded exact-arithmetic reference laws, NOT a SENS oracle or Core admission."""
from __future__ import annotations

from fractions import Fraction as F
from itertools import product
from math import floor
import unittest


def finite_convolution(left, right):
    a, b = list(map(F, left)), list(map(F, right))
    if not a or not b:
        return []
    out = [F(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def polynomial_reference(left, right):
    """Independent coefficient-sum model, not indexing the output by i+j."""
    if not left or not right:
        return []
    return [
        sum((F(left[i]) * F(right[k-i])
             for i in range(len(left)) if 0 <= k-i < len(right)), F(0))
        for k in range(len(left) + len(right) - 1)
    ]


def phase_unwrap(data, period):
    p = list(map(F, data))
    period = F(period)
    if period <= 0:
        raise ValueError("period must be strictly positive")
    if not p:
        return []
    out = [p[0]]
    for old, new in zip(p, p[1:]):
        difference = new - old
        base = floor(difference / period)
        choices = (difference - base * period, difference - (base + 1) * period)
        minimum = min(abs(z) for z in choices)
        viable = [z for z in choices if abs(z) == minimum]
        delta = next((z for z in viable if z == 0 or z * difference > 0),
                     viable[0])
        out.append(out[-1] + delta)
    return out


def modulo_reference(raw, period):
    """Independent period-equivalence and local-optimality bounded proof."""
    source = list(map(F, raw))
    output = phase_unwrap(raw, period)
    P = F(period)
    assert len(source) == len(output)
    if output:
        assert output[0] == source[0]
    for i in range(1, len(source)):
        raw_delta = source[i] - source[i-1]
        delta = output[i] - output[i-1]
        quotient = (delta - raw_delta) / P
        assert quotient.denominator == 1, "phase class changed"
        assert abs(delta) <= P/2, "not minimal local delta"
        if abs(delta) == P/2 and raw_delta != 0:
            assert delta * raw_delta > 0, "half-period tie not sign-preserving"
    return output


class D10ExactSignalLawTests(unittest.TestCase):
    def test_convolution_fixtures(self):
        for a,b,out in [
            ([1,2,3],[1,1],[1,3,5,3]),
            ([0,1],[1,-1],[0,1,-1]),
            ([2],[-3],[-6]),
            ([],[1],[]),
            ([1],[],[]),
            ([F(1,2),F(1,2)],[F(1,2),-F(1,2)],[F(1,4),0,-F(1,4)])
        ]:
            with self.subTest(a=a,b=b):
                self.assertEqual(finite_convolution(a,b), list(map(F,out)))

    def test_convolution_exhaustive_three_valued_ring(self):
        values=(-1,0,1)
        inputs=[tuple(x) for n in range(0,4) for x in product(values,repeat=n)]
        for a in inputs:
            for b in inputs:
                self.assertEqual(finite_convolution(a,b),polynomial_reference(a,b))

    def test_convolution_associative_commutative_distributive(self):
        a,b,c=[1,2],[3,-1],[0,1]
        self.assertEqual(finite_convolution(a,b),finite_convolution(b,a))
        self.assertEqual(finite_convolution(finite_convolution(a,b),c),
                         finite_convolution(a,finite_convolution(b,c)))
        b_plus_c=[x+y for x,y in zip(b,c)]
        self.assertEqual(finite_convolution(a,b_plus_c),
                         [x+y for x,y in zip(finite_convolution(a,b),
                                             finite_convolution(a,c))])
        self.assertEqual(finite_convolution(a,[1]),list(map(F,a)))

    def test_phase_fixtures(self):
        for input,period,out in [
            ([0,1,2,-1,0],4,[0,1,2,3,4]),
            ([1,2,3,4,5,6,1,2],6,[1,2,3,4,5,6,7,8]),
            ([0,180,-180],360,[0,180,180]),
            ([0,2],4,[0,2]),
            ([0,-2],4,[0,-2]),
            ([0,6],4,[0,2]),
            ([0,-6],4,[0,-2]),
            ([0,12],4,[0,0]),
            ([],4,[]),
            ([F(1,3),F(5,6)],1,[F(1,3),-F(1,6)])
        ]:
            with self.subTest(data=input,period=period):
                self.assertEqual(phase_unwrap(input,period),list(map(F,out)))
                self.assertEqual(modulo_reference(input,period),list(map(F,out)))

    def test_phase_all_short_sequences_and_period_classes(self):
        inputs=[tuple(p) for n in range(0,5) for p in product(range(-3,4),repeat=n)]
        for period in (F(2),F(3),F(4),F(3,2)):
            for signal in inputs:
                result=modulo_reference(signal,period)
                self.assertEqual(result,phase_unwrap(signal,period))

    def test_phase_invalid_period_and_nonphysical_claim(self):
        for invalid in (0,-1,-F(1,2)):
            with self.assertRaises(ValueError):
                phase_unwrap([0,1],invalid)
        # This fold must NOT be interpreted as the true motion path:
        # an actual 10-revolution jump is indistinguishable from zero samples.
        self.assertEqual(phase_unwrap([0,40],4),[F(0),F(0)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
