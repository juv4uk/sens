#!/usr/bin/env python3
"""Two independent D1-bit cyclic-window coverage oracles, not SENS runtime."""
import itertools
import unittest

def validate(word,n):
    if type(n) is not int or n<1: raise ValueError("positive exact n required")
    if not isinstance(word,(str,tuple,list)): raise ValueError("finite word required")
    if isinstance(word,str):
        if any(c not in "01" for c in word): raise ValueError("D1 bits only")
        return tuple(int(c) for c in word)
    if any(type(x) is not int or x not in (0,1) for x in word):
        raise ValueError("D1 bits only")
    return tuple(word)

def explicit_set_oracle(word,n):
    w=validate(word,n)
    size=1<<n
    if len(w)!=size: return False
    windows={tuple(w[(i+j)%size] for j in range(n)) for i in range(size)}
    return len(windows)==size

def rolling_register_oracle(word,n):
    w=validate(word,n)
    size=1<<n
    if len(w)!=size: return False
    window=0
    for j in range(n):
        window=(window<<1)|w[j]
    seen=bytearray(size)
    mask=size-1
    for i in range(size):
        if seen[window]: return False
        seen[window]=1
        window=((window<<1)&mask)|w[(i+n)%size]
    return all(seen)

def fkm_binary_cycle(order):
    if type(order) is not int or order<1: raise ValueError("positive order")
    state=[0]*(2*order+1)
    result=[]
    def generate(t,p):
        if t>order:
            if order%p==0:result.extend(state[1:p+1])
        else:
            state[t]=state[t-p]
            generate(t+1,p)
            for bit in range(state[t-p]+1,2):
                state[t]=bit
                generate(t+1,t)
    generate(1,1)
    return tuple(result)

class DeBruijnWordLaw(unittest.TestCase):
    def test_sage_witness_and_wrap(self):
        cases=[("01",1,True),("10",1,True),("0011",2,True),
          ("00010111",3,True),("00101110",3,True),
          ("10001011",3,True),("00010110",3,False),
          ("00000000",3,False),("000101110",3,False),
          ("",1,False),("0101",2,False)]
        for w,n,want in cases:
            with self.subTest(w=w,n=n):
                self.assertEqual(explicit_set_oracle(w,n),want)
                self.assertEqual(rolling_register_oracle(w,n),want)

    def test_exhaustive_all_binary_cycles_up_to_order_four(self):
        # n=4 => all 2**16 binary words; two independent algorithms.
        cases=0
        for order in range(1,5):
            size=1<<order
            for bits in itertools.product((0,1),repeat=size):
                self.assertEqual(explicit_set_oracle(bits,order),
                                 rolling_register_oracle(bits,order))
                cases+=1
        self.assertEqual(cases,65556)

    def test_generated_canonical_examples_and_rotations(self):
        for n in range(1,8):
            w=fkm_binary_cycle(n)
            self.assertEqual(len(w),1<<n)
            self.assertTrue(explicit_set_oracle(w,n))
            self.assertTrue(rolling_register_oracle(w,n))
            for i in range(0,len(w), max(1,len(w)//11)):
                rotated=w[i:]+w[:i]
                self.assertTrue(explicit_set_oracle(rotated,n))
                self.assertTrue(rolling_register_oracle(rotated,n))

    def test_falsifiers_of_length_and_repeat_only(self):
        for n in range(1,7):
            w=fkm_binary_cycle(n)
            self.assertFalse(explicit_set_oracle(w+(0,),n))
            self.assertFalse(rolling_register_oracle(w[:-1],n))
            self.assertFalse(explicit_set_oracle((0,)*(1<<n),n))
            self.assertFalse(rolling_register_oracle((0,)*(1<<n),n))
            self.assertTrue(explicit_set_oracle(w,n))
        # Primitive root alone is not a proof of all n-bit windows.
        self.assertFalse(explicit_set_oracle("0010",2))
        self.assertFalse(rolling_register_oracle("0010",2))

    def test_domain_must_reject_invalid_bits_and_n(self):
        for n in (0,-1,1.0,True):
            with self.subTest(n=n):
                with self.assertRaises(ValueError):explicit_set_oracle("0011",n)
                with self.assertRaises(ValueError):rolling_register_oracle("0011",n)
        for w in (None,3,"0012", [0,2], [False,0,1,1], ["0",1,0,1]):
            with self.subTest(w=w):
                with self.assertRaises(ValueError):explicit_set_oracle(w,2)
                with self.assertRaises(ValueError):rolling_register_oracle(w,2)

if __name__=="__main__":
    unittest.main(verbosity=2)
