#!/usr/bin/env python3
"""Independent exact arithmetic oracles for a bounded modular lift law.

Pure research reference: does NOT execute SENS or control AS5600 hardware.
"""
import itertools
import unittest

def domain(M,r,lo,hi):
    if any(type(x) is not int for x in (M,r,lo,hi)):
        raise ValueError("integer-only contract, booleans excluded")
    if M<2 or r<0 or r>=M or lo>hi:
        raise ValueError("invalid modulus, residue, or interval")

def bounded_lift_math(M,r,lo,hi):
    domain(M,r,lo,hi)
    low_k=-((r-lo)//M)
    high_k=(hi-r)//M
    n=max(0,high_k-low_k+1)
    if n==0:return ("NONE",0)
    first=r+M*low_k
    if n==1:return ("UNIQUE",first)
    return ("AMBIGUOUS",n,first,first+M)

def bounded_lift_brute(M,r,lo,hi):
    domain(M,r,lo,hi)
    values=[z for z in range(lo,hi+1) if z%M==r]
    if not values:return ("NONE",0)
    if len(values)==1:return ("UNIQUE",values[0])
    return ("AMBIGUOUS",len(values),values[0],values[1])

class BoundedLift(unittest.TestCase):
    def test_examples(self):
        examples=[
          ((4096,2,4090,4100),("UNIQUE",4098)),
          ((4096,2,3,4097),("NONE",0)),
          ((4096,2,0,8194),("AMBIGUOUS",3,2,4098)),
          ((7,6,-10,-1),("AMBIGUOUS",2,-8,-1)),
          ((5,2,-3,-3),("UNIQUE",-3)),
          ((7,0,1,6),("NONE",0)),
          ((7,0,0,7),("AMBIGUOUS",2,0,7)),
        ]
        for inp,expected in examples:
            with self.subTest(inp=inp):
                self.assertEqual(bounded_lift_math(*inp),expected)
                self.assertEqual(bounded_lift_brute(*inp),expected)

    def test_exhaustive_against_independent_enumeration(self):
        count=0
        for M in range(2,12):
            for r in range(M):
                for lo in range(-12,13):
                    for hi in range(lo,13):
                        with self.subTest(M=M,r=r,lo=lo,hi=hi):
                            self.assertEqual(bounded_lift_math(M,r,lo,hi),
                                             bounded_lift_brute(M,r,lo,hi))
                        count+=1
        self.assertGreater(count,15000)

    def test_modular_translation(self):
        for M,r,lo,hi in [(7,0,-3,20),(9,4,-20,-3),(4096,2,0,8194)]:
            result=bounded_lift_math(M,r,lo,hi)
            for k in (-3,-1,0,1,10):
                translated=bounded_lift_math(M,r,lo+k*M,hi+k*M)
                if result[0]=="NONE":expected=result
                elif result[0]=="UNIQUE":expected=("UNIQUE",result[1]+k*M)
                else:expected=("AMBIGUOUS",result[1],result[2]+k*M,result[3]+k*M)
                self.assertEqual(translated,expected)

    def test_invalid_inputs(self):
        bad=[
          (1,0,0,1),(0,0,0,1),(7,7,0,1),(7,-1,0,1),
          (7,1,5,4),(7,True,0,10),(7,1.0,0,10),(7,1,0.5,2),
          (7,1,0,"7")
        ]
        for args in bad:
            with self.subTest(args=args),self.assertRaises(ValueError):
                bounded_lift_math(*args)
            with self.subTest(args=args),self.assertRaises(ValueError):
                bounded_lift_brute(*args)

    def test_aliasing_ambiguity_not_silently_choosable(self):
        x=bounded_lift_math(4096,2,0,8194)
        self.assertEqual(x,("AMBIGUOUS",3,2,4098))
        self.assertNotEqual(x,("UNIQUE",2))
        self.assertNotEqual(x,("UNIQUE",4098))
        # A window spanning at least two full moduli always has multiple lifts;
        for M in range(2,16):
            for r in range(M):
                for lo in range(-M,M+1):
                    self.assertEqual(bounded_lift_math(M,r,lo,lo+2*M)[0],"AMBIGUOUS")

if __name__=="__main__":
    unittest.main(verbosity=2)
