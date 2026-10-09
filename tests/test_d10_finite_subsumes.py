#!/usr/bin/env python3
"""Exact one-sided term instance predicate: symbolic data, no SENS runtime."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import unittest

@dataclass(frozen=True)
class V:
    namespace: str
    number: int

def valid(term, allowed):
    if isinstance(term,V):
        return term.namespace == allowed and term.number>=0
    if isinstance(term,str):
        return bool(term)
    return isinstance(term,tuple) and bool(term) and isinstance(term[0],str) and bool(term[0]) and all(valid(x,allowed) for x in term[1:])

def substitutes(generic,specific):
    """Only bind generic P-vars, never target S-vars; return (boolean, witness)."""
    if not valid(generic,"P") or not valid(specific,"S"):
        raise ValueError("finite acyclic terms with disjoint P/S metavariables")
    sigma={}
    def visit(p,s):
        if isinstance(p,V):
            if p in sigma: return sigma[p]==s
            sigma[p]=s
            return True
        if isinstance(p,str): return isinstance(s,str) and p==s
        return (isinstance(s,tuple) and p[0]==s[0] and len(p)==len(s)
                and all(visit(x,y) for x,y in zip(p[1:],s[1:])))
    if visit(generic,specific):
        return True,sigma
    return False,{}

def apply(generic,sigma):
    if isinstance(generic,V): return sigma[generic]
    if isinstance(generic,tuple): return (generic[0],)+tuple(apply(x,sigma) for x in generic[1:])
    return generic

def all_subterms(t):
    yield t
    if isinstance(t,tuple):
        for x in t[1:]:
            yield from all_subterms(x)

def all_pvars(t):
    if isinstance(t,V):
        yield t
    if isinstance(t,tuple):
        for x in t[1:]:yield from all_pvars(x)

def exhaustive_subsumes(p,s):
    """Independent witness enumeration over actual finite subtrees of target."""
    variables=list(dict.fromkeys(all_pvars(p)))
    universe=list(dict.fromkeys(all_subterms(s)))
    for values in product(universe,repeat=len(variables)):
        if apply(p,dict(zip(variables,values)))==s:return True
    return False

class OneSidedSubsumption(unittest.TestCase):
    def check(self,p,s,expect):
        accept,sigma=substitutes(p,s)
        self.assertEqual(accept,expect)
        self.assertEqual(accept,exhaustive_subsumes(p,s))
        if accept:self.assertEqual(apply(p,sigma),s)
        else:self.assertEqual(sigma,{})
    def test_source_examples_and_difference_from_unify(self):
        P0,P1,S0=V("P",0),V("P",1),V("S",0)
        self.check(("f",P0,P0),("f","a","a"),True)
        self.check(("f",P0,P0),("f","a","b"),False)
        self.check(("f",P0,P0),("f",S0,S0),True)
        self.check(("f",P0,P0),("f",S0,"b"),False)
        self.check(("f","a",P0),("f",S0,"b"),False) # UNIFY could bind S0
        self.check(("f",P0,("g",P0)),("f","a",("g","a")),True)
        self.check(("f",P0,("g",P0)),("f","a",("g","b")),False)
        self.check(("f",P0,P1),("f",S0,S0),True)
        self.check(("f","a"),("f","a","b"),False)
    def test_target_variable_identity_and_immutability(self):
        P0,S0,S1=V("P",0),V("S",0),V("S",1)
        p=("p",P0,P0)
        target=("p",S0,S1)
        before=(p,target)
        self.assertEqual(substitutes(p,target),(False,{}))
        self.assertEqual((p,target),before)
        matched,witness=substitutes(p,("p",S0,S0))
        self.assertTrue(matched)
        self.assertEqual(witness[P0],S0)
        self.assertEqual(p,before[0])
    def test_576_bounded_exhaustive_crosscheck(self):
        P0,P1,S0,S1=V("P",0),V("P",1),V("S",0),V("S",1)
        generic=["a","b",P0,P1,("f",P0),("f","a"),
                 ("g",P0),("g","b"),
                 ("pair",P0,P0),("pair",P0,P1),("pair","a",P0),
                 ("pair",P0,"b"),("pair","a","b"),("pair","b","a"),
                 ("pair",("f",P0),("f",P0)),("pair",("f",P0),("g",P1)),
                 ("h",P0,P1),("h",P0,P0),("h","a",P0),
                 ("obs","tel",P0),("obs",P0,"clear"),("obs",P0,P0),
                 ("p",("f",P0)),("p",("g",P1))]
        specific=["a","b",S0,S1,("f",S0),("f","a"),
                 ("g",S0),("g","b"),
                 ("pair",S0,S0),("pair",S0,S1),("pair","a",S0),
                 ("pair",S0,"b"),("pair","a","b"),("pair","b","a"),
                 ("pair",("f",S0),("f",S0)),("pair",("f",S0),("g",S1)),
                 ("h",S0,S1),("h",S0,S0),("h","a",S0),
                 ("obs","tel",S0),("obs",S0,"clear"),("obs",S0,S0),
                 ("p",("f",S0)),("p",("g",S1))]
        count=0
        for p,s in product(generic,specific):
            got,w=substitutes(p,s)
            self.assertEqual(got,exhaustive_subsumes(p,s))
            if got:self.assertEqual(apply(p,w),s)
            count+=1
        self.assertEqual(count,576)
    def test_rejected_invalid_and_cross_namespace(self):
        P0,S0=V("P",0),V("S",0)
        for p,s in [(("f",S0),("f","a")),(("f",P0),("f",P0)),(None,"a"),
                    (("f",0),("f","a")),([],("f","a")),(("f",P0),{"f":"a"})]:
            with self.subTest(p=p,s=s):
                with self.assertRaises(ValueError):substitutes(p,s)
    def test_constructor_and_arity(self):
        P0=V("P",0)
        self.check(("p",P0),("q","a"),False)
        self.check(("p",P0),("p","a","b"),False)
        self.check(("p",P0),("p","a"),True)
if __name__=="__main__":unittest.main(verbosity=2)
