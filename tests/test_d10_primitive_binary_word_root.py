#!/usr/bin/env python3
"""Точні бітові слова: дві незалежні моделі, не оракул виконання SENS."""
import itertools
import unittest

def bits(word):
    if not isinstance(word, (tuple,list,str)):
        raise ValueError("expected finite sequence")
    s = tuple(int(x) for x in word) if not isinstance(word,str) else tuple(int(c) for c in word)
    if any(x not in (0,1) for x in s):
        raise ValueError("only exact D1 bits")
    return s

def brute_root(value):
    w=bits(value)
    n=len(w)
    if n==0: return ()
    for size in range(1,n+1):
        if n%size==0 and w[:size]*(n//size)==w:
            return w[:size]
    raise AssertionError("self-repetition should always work")

def kmp_root(value):
    w=bits(value)
    n=len(w)
    if n==0: return ()
    border=[0]*n
    for i in range(1,n):
        j=border[i-1]
        while j and w[i]!=w[j]:
            j=border[j-1]
        if w[i]==w[j]: j+=1
        border[i]=j
    possible=n-border[-1]
    return w[:possible] if n%possible==0 else w

def as_word(seq):
    return "".join(map(str,seq))

class WordRoot(unittest.TestCase):
    def test_source_contract_examples(self):
        examples=[
            ("01010101","01"),("000000","0"),("01010","01010"),
            ("101101101","101"),("00100","00100"),("",""),
            ("1","1"),("01","01"),("0101010","0101010"),
            ("001001","001"),("11111111","1"),("110110","110")
        ]
        for inp,out in examples:
            with self.subTest(inp=inp):
                self.assertEqual(as_word(brute_root(inp)),out)
                self.assertEqual(as_word(kmp_root(inp)),out)

    def test_all_short_binary_words(self):
        examined=0
        for n in range(0,13):
            for w in itertools.product((0,1),repeat=n):
                root=brute_root(w)
                self.assertEqual(root,kmp_root(w))
                if len(w):
                    self.assertEqual(w,root*(len(w)//len(root)))
                    self.assertEqual(len(w)%len(root),0)
                    for j in range(1,len(root)):
                        self.assertFalse(n%j==0 and w[:j]*(n//j)==w)
                examined+=1
        self.assertEqual(examined,8191)

    def test_sage_primitive_vs_minimal_overlap_period(self):
        w=bits("01010")
        # "01" is a partial overlap period, not a whole-repetition primitive.
        self.assertTrue(all(w[i]==w[i+2] for i in range(0,len(w)-2)))
        self.assertNotEqual(w, bits("01")*(len(w)//2))
        self.assertEqual(kmp_root(w),w)

    def test_idempotent_and_power(self):
        for w in ["0","1","01","001","1001","10101","00001"]:
            u=kmp_root(w)
            self.assertEqual(kmp_root(u),u)
            for k in range(1,6):
                self.assertEqual(kmp_root(bits(w)*k),u)

    def test_order_and_binary_strictness(self):
        for invalid in ("012", "a", [0,2], [2], None, 7):
            with self.subTest(invalid=invalid):
                with self.assertRaises((ValueError,TypeError)):
                    brute_root(invalid)

if __name__ == "__main__":
    unittest.main(verbosity=2)
