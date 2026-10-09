#!/usr/bin/env python3
"""Exact independent direct-language vs Brzozowski regular derivative proofs.
Research donor, NOT a SENS source file, ISA opcode or executable SENS oracle.
"""
from functools import lru_cache
from itertools import product
import unittest

ZERO=("zero",)
EPS=("eps",)
BIT0=("bit",0)
BIT1=("bit",1)

def alt(*exprs):
    flat=[]
    for x in exprs:
        if x==ZERO: continue
        if x[0]=="alt": flat.extend(x[1:])
        else: flat.append(x)
    unique=tuple(dict.fromkeys(flat))
    if not unique: return ZERO
    if len(unique)==1: return unique[0]
    return ("alt",)+unique

def cat(*exprs):
    flat=[]
    for x in exprs:
        if x==ZERO: return ZERO
        if x==EPS: continue
        if x[0]=="cat": flat.extend(x[1:])
        else: flat.append(x)
    if not flat: return EPS
    if len(flat)==1: return flat[0]
    return ("cat",)+tuple(flat)

def star(x):
    return EPS if x in (ZERO, EPS) else x if x[0]=="star" else ("star",x)

@lru_cache(maxsize=None)
def nullable(x):
    op=x[0]
    if op=="eps" or op=="star": return True
    if op=="zero" or op=="bit": return False
    if op=="alt": return any(map(nullable,x[1:]))
    if op=="cat": return all(map(nullable,x[1:]))
    raise ValueError(x)

@lru_cache(maxsize=None)
def derivative(x,bit):
    if bit not in (0,1): raise ValueError("D1 bit required")
    op=x[0]
    if op in ("zero","eps"): return ZERO
    if op=="bit": return EPS if x[1]==bit else ZERO
    if op=="alt": return alt(*(derivative(y,bit) for y in x[1:]))
    if op=="star": return cat(derivative(x[1],bit),x)
    if op=="cat":
        first=x[1]
        rest=cat(*x[2:])
        d=cat(derivative(first,bit),rest)
        return alt(d,derivative(rest,bit)) if nullable(first) else d
    raise ValueError(x)

def accepts_direct(regex,word):
    """Independent direct language relation, no derivative call.
    Computes reachable input positions for each regex, with a finite
    closure for star and no zero-progress re-entry."""
    seq=tuple(word)
    @lru_cache(maxsize=None)
    def endings(x,i):
        op=x[0]
        if op=="zero": return frozenset()
        if op=="eps": return frozenset({i})
        if op=="bit": return frozenset({i+1}) if i<len(seq) and seq[i]==x[1] else frozenset()
        if op=="alt": return frozenset(j for sub in x[1:] for j in endings(sub,i))
        if op=="cat":
            positions={i}
            for sub in x[1:]:
                positions={j for p in positions for j in endings(sub,p)}
            return frozenset(positions)
        if op=="star":
            seen={i}
            stack=[i]
            while stack:
                for p in endings(x[1],stack.pop()):
                    if p not in seen:
                        seen.add(p)
                        stack.append(p)
            return frozenset(seen)
        raise ValueError(x)
    return len(seq) in endings(regex,0)

def accepts_derivative(regex,word):
    residual=regex
    for bit in word:
        residual=derivative(residual,bit)
    return nullable(residual)

class Brzozowski1964(unittest.TestCase):
    def test_source_witnesses(self):
        ab=cat(BIT0,BIT1)
        zero_then_one=cat(star(BIT0),BIT1)
        union=alt(BIT0,BIT1)
        cases=[
          (ab,0,[("1",True),("",False),("0",False)]),
          (ab,1,[("",False),("1",False)]),
          (zero_then_one,0,[("1",True),("01",True),("",False)]),
          (zero_then_one,1,[("",True),("1",False),("0",False)]),
          (union,0,[("",True),("0",False)]),
          (EPS,0,[("",False),("0",False)])
        ]
        for r,a,samples in cases:
            for suffix,expect in samples:
                self.assertEqual(accepts_derivative(derivative(r,a),tuple(map(int,suffix))),expect)

    def test_derivative_vs_independent_language_membership(self):
        atoms=(ZERO,EPS,BIT0,BIT1)
        samples=list(atoms)
        samples += [star(BIT0),star(BIT1),star(alt(BIT0,BIT1)),star(EPS)]
        for a in atoms:
            for b in atoms:
                samples += [alt(a,b),cat(a,b)]
        samples += [cat(star(BIT0),BIT1),cat(alt(EPS,BIT0),BIT1),
                    star(cat(BIT0,BIT1)),cat(BIT0,star(BIT1)),
                    cat(star(alt(BIT0,BIT1)),BIT1)]
        words=[tuple(w) for n in range(5) for w in product((0,1),repeat=n)]
        for r in samples:
            for bit in (0,1):
                residual=derivative(r,bit)
                for suffix in words:
                    self.assertEqual(accepts_derivative(residual,suffix),
                                     accepts_direct(r,(bit,)+suffix),
                                     (r,bit,suffix))
        self.assertGreater(len(samples)*2*len(words),3000)

    def test_derivative_composition(self):
        expressions=[cat(BIT0,BIT1),cat(star(BIT0),BIT1),
                     alt(cat(BIT0,BIT1),cat(BIT1,BIT0)),
                     star(cat(BIT0,BIT1)),star(alt(BIT0,BIT1))]
        words=[tuple(w) for n in range(5) for w in product((0,1),repeat=n)]
        for r in expressions:
            for word in words:
                self.assertEqual(accepts_derivative(r,word),accepts_direct(r,word))

    def test_nullable_left_arm_is_necessary(self):
        r=cat(star(BIT0),BIT1)
        self.assertTrue(nullable(derivative(r,1)))
        self.assertFalse(nullable(cat(derivative(star(BIT0),1),BIT1)))

    def test_ast_inequality_not_semantic_inequality(self):
        a=cat(EPS,BIT0)
        b=alt(BIT0,ZERO)
        self.assertEqual(a,b)
        for bit in (0,1):
            for n in range(4):
                for suffix in product((0,1),repeat=n):
                    self.assertEqual(accepts_derivative(derivative(a,bit),suffix),
                                     accepts_derivative(derivative(b,bit),suffix))

    def test_invalid_bit_rejected(self):
        for bad in (-1,2,"0",None):
            with self.assertRaises(ValueError):
                derivative(BIT0,bad)

if __name__=="__main__":
    unittest.main(verbosity=2)
