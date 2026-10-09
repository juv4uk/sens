#!/usr/bin/env python3
"""Точні еталонні закони для D10. Це НЕ інтерпретатор SENS."""
from fractions import Fraction as F
import unittest

def mechanical_direct(n, k, rho=F(0)):
    if type(n) is not int or type(k) is not int or n <= 0 or not 0 <= k <= n:
        raise ValueError("integer period and event bounds")
    if not isinstance(rho, (int, F)) or not 0 <= rho < 1:
        raise ValueError("exact phase in [0,1)")
    rho = F(rho)
    return [((F((i+1)*k,n)+rho).numerator // (F((i+1)*k,n)+rho).denominator)
            - ((F(i*k,n)+rho).numerator // (F(i*k,n)+rho).denominator)
            for i in range(n)]

def mechanical_accumulator(n, k, rho=F(0)):
    """Інший спосіб: акумулятор залишку, без формули різниці floor."""
    if type(n) is not int or type(k) is not int or n <= 0 or not 0 <= k <= n:
        raise ValueError("integer period and event bounds")
    if not isinstance(rho,(int,F)) or not 0 <= rho < 1:
        raise ValueError("exact phase")
    acc = F(rho) * n
    result = []
    for _ in range(n):
        acc += k
        bit = acc // n
        acc -= bit * n
        result.append(bit)
    return result

def prefix_expected(n, k, phase, m):
    x = F(m*k,n) + F(phase)
    return x.numerator // x.denominator

class MechanicalWord(unittest.TestCase):
    def test_fixtures(self):
        cases = [
            (8,3,F(0),"00100101"), (8,3,F(1,2),"01010010"),
            (8,5,F(0),"01011011"), (12,4,F(0),"001001001001"),
            (5,2,F(1,3),"01001"), (3,0,F(0),"000"),(4,4,F(0),"1111")
        ]
        for n,k,p,want in cases:
            with self.subTest(n=n,k=k,p=p):
                self.assertEqual("".join(map(str,mechanical_direct(n,k,p))),want)
                self.assertEqual(mechanical_accumulator(n,k,p),mechanical_direct(n,k,p))

    def test_exhaustive_short_periods(self):
        phases=[F(0),F(1,7),F(1,3),F(1,2),F(5,7)]
        for n in range(1,25):
            for k in range(n+1):
                for phase in phases:
                    direct=mechanical_direct(n,k,phase)
                    self.assertEqual(direct,mechanical_accumulator(n,k,phase))
                    self.assertTrue(all(x in (0,1) for x in direct))
                    self.assertEqual(len(direct),n)
                    self.assertEqual(sum(direct),k)
                    self.assertEqual(sum(direct[:n//2]),prefix_expected(n,k,phase,n//2))

    def test_all_cyclic_subword_counts(self):
        # Для раціональних mechanical words кожна довжина має 0 або 1 дисбаланс.
        for n in range(1,17):
            for k in range(n+1):
                for phase in (F(0),F(1,3),F(1,2)):
                    w=mechanical_accumulator(n,k,phase)
                    for length in range(n+1):
                        values=[sum(w[(start+j)%n] for j in range(length))
                                for start in range(n)]
                        self.assertLessEqual(max(values)-min(values),1)
                        self.assertTrue(all(abs(F(count)-F(length*k,n))<1 or
                                            count == F(length*k,n) for count in values))

    def test_contract_rejects_invalid(self):
        for args in ((0,0,0),(8,-1,0),(8,9,0),(8,3,F(-1,2)),
                     (8,3,F(1)),(8,3,0.5),(8,3,2)):
            for fn in (mechanical_direct,mechanical_accumulator):
                with self.subTest(args=args,fn=fn.__name__):
                    with self.assertRaises(ValueError): fn(*args)

    def test_non_equivalent_poor_distribution(self):
        wrong=[1,1,1,0,0,0,0,0]
        self.assertEqual(sum(wrong),3)
        self.assertNotEqual(wrong,mechanical_direct(8,3))
        self.assertGreater(max(sum(wrong[(s+j)%8] for j in range(3))
                               for s in range(8)),2)

if __name__=="__main__":
    unittest.main(verbosity=2)
