#!/usr/bin/env python3
import importlib.util
from fractions import Fraction as F
from itertools import product
from math import lcm
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/"scripts/check_d10_finite_bayes_update.py"
spec=importlib.util.spec_from_file_location("finite_bayes",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ExactResearch(unittest.TestCase):
 def test_witnesses(self):
  self.assertEqual(m.update(["1/2","1/2"],["3/4","1/4"]),((F(3,4),F(1,4)),F(1,2)))
  self.assertEqual(m.update(["1/3","2/3"],["1/2","1/4"]),((F(1,2),F(1,2)),F(1,3)))
  self.assertEqual(m.update(["1/4","1/4","1/2"],[1,0,"1/2"]),((F(1,2),F(0),F(1,2)),F(1,2)))
 def test_rejections(self):
  for a,b in [([],[]),([1],[]),([1],[0]),([0,0],[1,1]),([1.0],[1]),([True],[1]),(["1/2","1/2"],[0,0]),([1],[2]),(["1/2"],[1])]:
   with self.subTest(a=a,b=b),self.assertRaises(ValueError): m.update(a,b)
 def test_independent_integer_weight_oracle(self):
  checks=0
  for n in (2,3):
   for counts in product(range(5),repeat=n):
    if sum(counts)!=4: continue
    prior=[F(i,4) for i in counts]
    for bits in product(range(4),repeat=n):
     like=[F(i,3) for i in bits]
     weights=[a*b for a,b in zip(prior,like)]
     scale=lcm(*(w.denominator for w in weights))
     units=[int(w*scale) for w in weights]
     mass=sum(units)
     if not mass: continue
     expect=tuple(F(i,mass) for i in units),F(mass,scale)
     self.assertEqual(m.update(prior,like),expect)
     checks+=1
  self.assertGreater(checks,800)
