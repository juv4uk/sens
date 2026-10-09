#!/usr/bin/env python3
"""Незалежний свідок exact-rational radix decomposition."""
from fractions import Fraction
import unittest

def normalize(x, b):
    if not isinstance(x, Fraction) or type(b) is not int or b < 2:
        raise ValueError("invalid argument")
    if x == 0:
        return Fraction(0), 0
    m, e = abs(x), 0
    while m >= b:
        m /= b
        e += 1
    while m < 1:
        m *= b
        e -= 1
    return (-m if x < 0 else m), e

def reference(x, b):
    if not x:
        return Fraction(0), 0
    options = []
    for e in range(-30, 31):
        power = Fraction(b) ** e
        if power <= abs(x) < b * power:
            options.append((x / power, e))
    if len(options) != 1:
        raise AssertionError("nonunique decomposition")
    return options[0]

class TestExactRadix(unittest.TestCase):
    def test_examples(self):
        cases = [
            (Fraction(3, 4), 2, Fraction(3, 2), -1),
            (Fraction(-40, 3), 2, Fraction(-5, 3), 3),
            (Fraction(8), 2, Fraction(1), 3),
            (Fraction(1, 1000), 10, Fraction(1), -3),
            (Fraction(0), 2, Fraction(0), 0)
        ]
        for x, b, m, e in cases:
            self.assertEqual(normalize(x, b), (m, e))
            self.assertEqual(reference(x, b), (m, e))

    def test_exact_exhaustion(self):
        checked = 0
        for b in range(2, 12):
            for n in range(-31, 32):
                for d in range(1, 16):
                    x = Fraction(n, d)
                    m, e = normalize(x, b)
                    self.assertEqual((m, e), reference(x, b))
                    self.assertEqual(x, m * Fraction(b) ** e)
                    if x:
                        self.assertTrue(Fraction(1) <= abs(m) < b)
                    else:
                        self.assertEqual((m, e), (0, 0))
                    checked += 1
        self.assertEqual(checked, 9450)
        print("D10 exact radix independent rational cases: PASS 9450")

    def test_rejections(self):
        for x, b in ((Fraction(1), 1), (Fraction(1), 0),
                     (Fraction(3, 4), 2.0), (0.75, 2),
                     (Fraction(1), True), ("1/2", 2)):
            with self.assertRaises(ValueError):
                normalize(x, b)

if __name__ == "__main__":
    unittest.main(verbosity=2)
