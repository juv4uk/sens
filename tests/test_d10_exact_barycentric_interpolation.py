#!/usr/bin/env python3
"""Exact D10 donor reference: NIST DLMF Lagrange-vs-barycentric, not SENS runtime."""
from fractions import Fraction as F
from itertools import combinations, product
from unittest import TestCase, main


def require(points, x):
    assert points, "at least one interpolation node required"
    assert isinstance(x, F), "exact rational evaluation required"
    assert all(len(p) == 2 and isinstance(p[0], F) and isinstance(p[1], F)
               for p in points), "only exact rational nodes permitted"
    assert len(set(p[0] for p in points)) == len(points), "distinct abscissas required"


def lagrange(points, x):
    require(points, x)
    total = F(0)
    for i, (xi, yi) in enumerate(points):
        basis = F(1)
        for j, (xj, _) in enumerate(points):
            if i != j:
                basis *= (x - xj) / (xi - xj)
        total += yi * basis
    return total


def barycentric(points, x):
    require(points, x)
    for xi, yi in points:
        if x == xi:
            return yi
    weights = []
    for i, (xi, _) in enumerate(points):
        denominator = F(1)
        for j, (xj, _) in enumerate(points):
            if i != j:
                denominator *= xi - xj
        weights.append(F(1) / denominator)
    terms = [w / (x - xi) for w, (xi, _) in zip(weights, points)]
    denominator = sum(terms, F(0))
    assert denominator != 0, "invalid barycentric denominator"
    return sum((t * yi for t, (_, yi) in zip(terms, points)), F(0)) / denominator


class ExactBarycentricDonor(TestCase):
    def test_source_examples(self):
        cases = [
            ([(0, 0), (1, 1), (2, 4)], F(1, 2), F(1, 4)),
            ([(0, 0), (1, 1), (2, 4)], F(3), F(9)),
            ([(-1, 1), (1, 5)], F(0), F(3)),
            ([(1, 7)], F(5, 2), F(7)),
            ([(0, 5), (1, 5), (2, 5)], F(3, 2), F(5)),
        ]
        for plain, query, expected in cases:
            nodes = [(F(a), F(b)) for a, b in plain]
            with self.subTest(nodes=plain, query=query):
                self.assertEqual(barycentric(nodes, query), expected)
                self.assertEqual(lagrange(nodes, query), expected)

    def test_bounded_exhaustive_independent_models(self):
        node_values = list(map(F, (-2, -1, 0, 1, 2)))
        y_values = list(map(F, (-1, 0, 1)))
        queries = (F(-3, 2), F(-1, 2), F(0), F(1, 2), F(3, 2), F(3))
        samples = 0
        for size in range(1, 5):
            for xs in combinations(node_values, size):
                for ys in product(y_values, repeat=size):
                    nodes = list(zip(xs, ys))
                    for q in queries:
                        a = lagrange(nodes, q)
                        self.assertEqual(barycentric(nodes, q), a)
                        self.assertEqual(barycentric(list(reversed(nodes)), q), a)
                        samples += 1
                    for xx, yy in nodes:
                        self.assertEqual(barycentric(nodes, xx), yy)
        self.assertEqual(samples, 4680)

    def test_exact_affine_value_law(self):
        pts = [(F(0), F(-1)), (F(1), F(2)), (F(3), F(-2))]
        for q in (F(0), F(1, 3), F(5, 2), F(4)):
            p = barycentric(pts, q)
            shifted = [(x, y + F(7)) for x, y in pts]
            scaled = [(x, -F(2) * y) for x, y in pts]
            self.assertEqual(barycentric(shifted, q), p + 7)
            self.assertEqual(barycentric(scaled, q), -2 * p)

    def test_falsifiers(self):
        good = [(F(0), F(0)), (F(1), F(1))]
        bad = (
            ([], F(0)),
            ([(F(0), F(0)), (F(0), F(2))], F(0)),
            ([(F(0), F(0)), (F(1), F(1))], 0.5),
            ([(0.0, F(0)), (F(1), F(1))], F(0)),
        )
        for points, query in bad:
            with self.subTest(points=points, query=query):
                with self.assertRaises(AssertionError):
                    barycentric(points, query)
        self.assertEqual(barycentric(good, F(1, 2)), F(1, 2))
        self.assertIsInstance(barycentric(good, F(1, 2)), F)


if __name__ == "__main__":
    main(verbosity=2)
