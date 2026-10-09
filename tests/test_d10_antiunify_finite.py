#!/usr/bin/env python3
"""Finite first-order anti-unification mathematical reference; not SENS execution."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import unittest

@dataclass(frozen=True)
class Var:
    index: int

def is_term(term):
    if isinstance(term,str):
        return bool(term)
    if isinstance(term,tuple):
        return len(term)>=1 and isinstance(term[0],str) and bool(term[0]) and all(is_term(t) for t in term[1:])
    return False

def lgg(a,b):
    """Memoize ordered disagreement pairs to preserve *shared variable* constraints."""
    if not is_term(a) or not is_term(b):
        raise ValueError("only ground finite first-order terms")
    cache={}
    left={}
    right={}
    def visit(x,y):
        if x==y:
            return x
        if isinstance(x,tuple) and isinstance(y,tuple) and x[0]==y[0] and len(x)==len(y):
            return (x[0],)+(tuple(visit(p,q) for p,q in zip(x[1:],y[1:])))
        key=(x,y)
        if key not in cache:
            v=Var(len(cache))
            cache[key]=v
            left[v]=x
            right[v]=y
        return cache[key]
    return visit(a,b),left,right

def instantiate(pattern,substitution):
    if isinstance(pattern,Var):
        return substitution[pattern]
    if isinstance(pattern,tuple):
        return (pattern[0],)+tuple(instantiate(x,substitution) for x in pattern[1:])
    return pattern

def display(term):
    if isinstance(term,Var):
        return "V"+str(term.index)
    if isinstance(term,tuple):
        return term[0]+"("+",".join(map(display,term[1:]))+")"
    return term

class FiniteAntiUnify(unittest.TestCase):
    def case(self,a,b,expected):
        g,s1,s2=lgg(a,b)
        self.assertEqual(display(g),expected)
        self.assertEqual(instantiate(g,s1),a)
        self.assertEqual(instantiate(g,s2),b)

    def test_source_witnesses(self):
        self.case(("pair","a","a"),("pair","b","b"),"pair(V0,V0)")
        self.case(("pair","a","a"),("pair","b","c"),"pair(V0,V1)")
        self.case(("parent","ann","leo"),("parent","ann","mira"),"parent(ann,V0)")
        self.case(("f",("g","a"),("g","a")),("f",("g","b"),("g","b")),"f(g(V0),g(V0))")
        self.case(("f","a"),("g","a"),"V0")
        self.case(("observation","telescope1","clear"),("observation","telescope2","clear"),"observation(V0,clear)")
        self.case("a","a","a")
        self.case(("f","a"),("f","a","b"),"V0")

    def test_reuse_and_distinctness_are_not_optional(self):
        common,_,_=lgg(("pair","a","a"),("pair","b","b"))
        self.assertEqual(common[1],common[2])
        distinct,_,_=lgg(("pair","a","a"),("pair","b","c"))
        self.assertNotEqual(distinct[1],distinct[2])
        wrong=("pair",Var(0),Var(0))
        self.assertNotEqual(instantiate(wrong,{Var(0):"b"}),("pair","b","c"))
        less_specific=("pair",Var(0),Var(1))
        self.assertNotEqual(common,less_specific)

    def test_all_ground_corpus_pairs(self):
        roots=["a","b","c",("f","a"),("f","b"),("g","a"),("g","b")]
        corpus=roots+[("pair",x,y) for x,y in product(("a","b","c"),repeat=2)]
        corpus += [("f",("pair",x,y)) for x,y in product(("a","b"),repeat=2)]
        corpus += [("pair",("f",x),("f",y)) for x,y in product(("a","b"),repeat=2)]
        n=0
        for a,b in product(corpus,repeat=2):
            g,s1,s2=lgg(a,b)
            self.assertEqual(instantiate(g,s1),a)
            self.assertEqual(instantiate(g,s2),b)
            self.assertEqual(g,lgg(a,b)[0],"determinism of canonical variable numbering")
            n+=1
        self.assertEqual(n,24*24)

    def test_shared_structure_kept_and_symmetry(self):
        examples=[
           (("f","a","a"),("f","b","b")),
           (("pair",("f","a"),("f","a")),("pair",("f","b"),("f","b"))),
           (("p","a",("q","b")) ,("p","c",("q","d"))),
           (("s","x","x","y"),("s","a","a","b"))
        ]
        for a,b in examples:
            g,sa,sb=lgg(a,b)
            h,ha,hb=lgg(b,a)
            self.assertEqual(g,h)
            self.assertEqual(instantiate(g,sa),a)
            self.assertEqual(instantiate(g,sb),b)
            self.assertEqual(instantiate(h,ha),b)
            self.assertEqual(instantiate(h,hb),a)

    def test_non_ground_rejected(self):
        for value in (0,False,None,3.14,Var(0),(),("f",Var(2)),{"f":"a"},("f","")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    lgg(value,"a")

if __name__ == "__main__":
    unittest.main(verbosity=2)
