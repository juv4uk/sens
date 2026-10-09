"""Independent finite Allen/ATMS mathematical and D10 admission witnesses."""
import copy
import importlib.util
import itertools
import json
import unittest
from pathlib import Path
from fractions import Fraction

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("d10_hist",root/"scripts/check_d10_allen_atms_research.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def reference(a,b):
 x,y=a;u,v=b
 cases={
 "BEFORE":y<u, "MEETS":y==u, "OVERLAPS":x<u<y<v,
 "STARTS":x==u and y<v, "DURING":u<x and y<v,
 "FINISHES":u<x and y==v, "EQUALS":x==u and y==v,
 "AFTER":x>v, "MET-BY":x==v, "OVERLAPPED-BY":u<x<v<y,
 "STARTED-BY":x==u and y>v, "CONTAINS":x<u and y>v,
 "FINISHED-BY":x<u and y==v}
 hits=[name for name,ok in cases.items() if ok]
 assert len(hits)==1,(a,b,hits)
 return hits[0]

def oracle(left,right,bad):
 atoms=sorted({a for group in left+right+bad for a in group})
 valid=[]
 for k in range(len(atoms)+1):
  for tup in itertools.combinations(atoms,k):
   s=set(tup)
   if any(set(a)<=s for a in left) and any(set(b)<=s for b in right) and not any(set(n)<=s for n in bad):
    valid.append(frozenset(s))
 out=[x for x in valid if not any(y<x for y in valid)]
 return tuple(sorted((tuple(sorted(x)) for x in out), key=lambda z:(len(z),z)))

class HistoricalExactOracles(unittest.TestCase):
 def test_allen_13_relations_441_pairs_and_inverse(self):
  intervals=list(itertools.combinations(range(-3,4),2))
  seen=set()
  for a in intervals:
   for b in intervals:
    r=m.allen_interval_relation(a,b)
    self.assertEqual(r,reference(a,b))
    self.assertEqual(m.allen_interval_relation(b,a),m.ALLEN_INVERSE[r])
    seen.add(r)
  self.assertEqual(seen,m.ALLEN_RELATIONS)
 def test_allen_fraction_ties_and_invalid(self):
  F=Fraction
  self.assertEqual(m.allen_interval_relation((0,F(1,3)),(F(1,3),1)),"MEETS")
  self.assertEqual(m.allen_interval_relation((0,F(1,2)),(F(1,3),1)),"OVERLAPS")
  for bad in ((0,0),(3,2)):
   with self.assertRaises(ValueError):m.allen_interval_relation(bad,(2,3))
  for bad in (0.0,True,"0"):
   with self.assertRaises(TypeError):m.allen_interval_relation((bad,1),(2,3))
 def test_atms_405_exhaustive_powerset_differential(self):
  fs=[[],[[]],[[0]],[[1]],[[2]],[[0],[1]],[[0,1]],[[0],[0,1]],[[0,2],[1,2]]]
  ng=[[],[[]],[[0]],[[0,1]],[[0],[2]]]
  for a,b,n in itertools.product(fs,fs,ng):
   self.assertEqual(m.atms_consistent_label_join(a,b,n),oracle(a,b,n))
 def test_atms_empty_support_distinct_from_no_support(self):
  self.assertEqual(m.atms_consistent_label_join([[]],[[]],[]),((),))
  self.assertEqual(m.atms_consistent_label_join([], [[]],[]),())
  self.assertEqual(m.atms_consistent_label_join([[]],[[]],[[]]),())
 def test_atms_invalid_identity(self):
  for invalid in (-1,True,1.5,"x"):
   with self.assertRaises(TypeError):m.atms_consistent_label_join([[invalid]],[[]],[])

class NeverRatifyFromResearch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  load=lambda p:json.loads(p.read_text(encoding="utf8"))
  cls.doc=load(m.DOSSIER);cls.fd=load(m.FOUNDATION);cls.inv=load(m.INVENTORY)
 def check(self,d):return m.verify_dossier(d,self.fd,self.inv)
 def test_live_research_only(self):
  self.assertEqual(self.check(self.doc)["selected_from_dossier"],0)
 def test_forged_coordinates_and_residents_rejected(self):
  for patch in ({"coordinate":"0000000000"},{"ratified_resident":True},
                {"selected_in_canonical_inventory":True},
                {"physical_t5_authorized":True},
                {"triage_status":"SELECT"},{"owner_review_required":False},
                {"semantic_name":"CAR"},{"semantic_name":"SEARCH"},
                {"source":{"primary_url":"http://invalid"}},
                {"falsifiers":[]}):
   d=copy.deepcopy(self.doc);d["rows"][0].update(patch)
   with self.assertRaises((AssertionError,KeyError)):self.check(d)

if __name__=="__main__":unittest.main()
