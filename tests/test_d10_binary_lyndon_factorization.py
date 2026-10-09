#!/usr/bin/env python3
"""D10 research oracle: exact D1 binary Chen-Fox-Lyndon factorization.
Not a binary SENS runtime, not domain-coordinate authorization.
"""
from __future__ import annotations
from itertools import product
import unittest

def verify_bits(s):
    if not isinstance(s, str) or any(c not in "01" for c in s):
        raise ValueError("finite binary word with explicit alphabet order 0<1")
    return s

def is_lyndon(s):
    return bool(s) and all(s < s[i:] for i in range(1, len(s)))

def duval(s):
    s = verify_bits(s)
    result = []
    n = len(s)
    i = 0
    while i < n:
        j = i+1
        k = i
        while j < n and s[k] <= s[j]:
            k = i if s[k] < s[j] else k+1
            j += 1
        word_len = j-k
        while i <= k:
            result.append(s[i:i+word_len])
            i += word_len
    return result

def exhaustive_partitions(s):
    """Independent exponential specification, no reliance on Duval pointers."""
    verify_bits(s)
    if not s: return [[]]
    out = []
    for split_mask in range(1 << (len(s)-1)):
        last = 0
        factors = []
        for i in range(1, len(s)):
            if split_mask & (1 << (i-1)):
                factors.append(s[last:i])
                last = i
        factors.append(s[last:])
        if all(is_lyndon(w) for w in factors) and all(
            factors[i] >= factors[i+1] for i in range(len(factors)-1)
        ):
            out.append(factors)
    return out

class D10Lyndon(unittest.TestCase):
    def test_source_examples_and_counterexamples(self):
        for word, want in [
            ("", []),("0",["0"]),("1111",["1","1","1","1"]),
            ("01010",["01","01","0"]),
            ("010010010001000",["01","001","001","0001","0","0","0"]),
            ("001001",["001","001"]),("101",["1","01"])
        ]:
            with self.subTest(word=word):
                self.assertEqual(duval(word), want)

    def test_exhaustive_unique_factorization_up_to_nine(self):
        examined = 0
        for n in range(10):
            for bits in product("01", repeat=n):
                word = "".join(bits)
                candidates = exhaustive_partitions(word)
                self.assertEqual(len(candidates),1)
                self.assertEqual(duval(word), candidates[0])
                examined += 1
        self.assertEqual(examined,1023)

    def test_duval_all_bitwords_to_twelve(self):
        count=0
        for n in range(13):
            for bits in product("01", repeat=n):
                s = "".join(bits)
                factors=duval(s)
                self.assertEqual("".join(factors),s)
                self.assertTrue(all(is_lyndon(x) for x in factors))
                self.assertTrue(all(x >= y for x,y in zip(factors,factors[1:])))
                count+=1
        self.assertEqual(count,8191)

    def test_differs_from_primitive_full_repeat_root(self):
        self.assertEqual(duval("01010"),["01","01","0"])
        self.assertNotEqual(duval("01010"),["01010"])
        self.assertEqual(duval("000000"),["0"]*6)

    def test_invalid_alphabet_fails_closed(self):
        for value in ("02","010a",None,123,[0,1],(1,0)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    duval(value)

    def test_factor_order_is_explicit_data(self):
        # Reverse alphabet order 1<0 changes the canonical factorization.
        def reverse_order(s):
            return [p.translate(str.maketrans("01","10"))
                    for p in duval(s.translate(str.maketrans("01","10")))]
        self.assertNotEqual(duval("01010"),reverse_order("01010"))

if __name__=="__main__":
    unittest.main(verbosity=2)
