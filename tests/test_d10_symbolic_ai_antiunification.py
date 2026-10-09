#!/usr/bin/env python3
"""D10 AI candidate: independent finite constructive and bounded-minimality proof."""
import itertools
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from d10_antiunify_oracle import lgg,lgg_independent,instantiate,check

def atom(a): return {"atom":a}
def fun(f,*args): return {"fun":f,"args":list(args)}
def var(i): return {"var":i}

def matches(pattern, ground):
    env={}
    stack=[(pattern,ground)]
    while stack:
        p,g=stack.pop()
        if set(p)=={"var"}:
            i=p["var"]
            if i in env and env[i]!=g: return False
            env[i]=g
        elif set(p)=={"atom"}:
            if p!=g: return False
        elif set(p)=={"fun","args"}:
            if set(g)!={"fun","args"} or p["fun"]!=g["fun"] or len(p["args"])!=len(g["args"]): return False
            stack.extend(zip(p["args"],g["args"]))
        else: return False
    return True

class TestAntiunify(unittest.TestCase):
    def test_research_not_selected_or_ratified(self):
        record=json.loads((ROOT/"knowledge/d10-symbolic-ai-antiunification-research-v1.json").read_text())
        self.assertEqual(record["schema"],"d10-symbolic-ai-antiunification-research/v1")
        self.assertEqual(record["decision"],"PENDING-OWNER-REVIEW-NOT-SELECTED")
        self.assertEqual(record["candidate"]["semantic_name"],"GROUND-TERM-LEAST-GENERAL-GENERALIZATION")
        self.assertIsNone(record["candidate"]["coordinate"])
        self.assertFalse(record["candidate"]["ratified_resident"])
        self.assertIn("D9 UNIFY",record["dedup"]["distinguishing_behavior"])

    def test_examples_and_reconstruction(self):
        cases=[
            (atom("a"),atom("a"),atom("a")),
            (atom("a"),atom("b"),var(0)),
            (fun("p",atom("a"),atom("a")),fun("p",atom("b"),atom("b")),fun("p",var(0),var(0))),
            (fun("p",atom("a"),atom("b")),fun("p",atom("b"),atom("a")),fun("p",var(0),var(1))),
            (fun("obs",atom("star"),fun("at",atom("t1"))),fun("obs",atom("star"),fun("at",atom("t2"))),fun("obs",atom("star"),fun("at",var(0)))),
            (fun("f",atom("a")),fun("g",atom("a")),var(0)),
        ]
        for a,b,p in cases:
            with self.subTest(a=a,b=b):
                out=lgg(a,b)
                self.assertEqual(out,lgg_independent(a,b))
                self.assertEqual(out["generalization"],p)
                self.assertEqual(instantiate(p,out["left_substitution"]),a)
                self.assertEqual(instantiate(p,out["right_substitution"]),b)

    def test_exhaustive_bounded_leastness(self):
        atoms=[atom("a"),atom("b")]
        ground=atoms+[fun("f",a) for a in atoms]+[fun("p",a,b) for a in atoms for b in atoms]
        pool=atoms+[var(0),var(1)]
        patterns=pool+[fun("f",a) for a in pool]+[fun("p",a,b) for a in pool for b in pool]
        for a,b in itertools.product(ground,repeat=2):
            out=lgg(a,b)
            self.assertEqual(out,lgg_independent(a,b))
            g=out["generalization"]
            self.assertEqual(instantiate(g,out["left_substitution"]),a)
            self.assertEqual(instantiate(g,out["right_substitution"]),b)
            for p in patterns:
                if matches(p,a) and matches(p,b):
                    self.assertTrue(matches(p,g),(a,b,p,g))

    def test_duplicate_disagreements_require_same_variable(self):
        a=fun("p",atom("a"),atom("a"))
        b=fun("p",atom("b"),atom("b"))
        self.assertEqual(lgg(a,b)["generalization"],fun("p",var(0),var(0)))
        self.assertFalse(matches(fun("p",var(0),var(0)),fun("p",atom("a"),atom("b"))))

    def test_invalid_input_is_explicitly_rejected(self):
        illegal=[{"var":0},{"atom":""},{"atom":"$x"},{"fun":"f","args":[]},
                 {"fun":"f","args":[atom("a")]*33},{"atom":"a","args":[]},
                 "a",{},{"fun":"f","args":["a"]}]
        for item in illegal:
            with self.subTest(item=item),self.assertRaises(ValueError):
                lgg(item,atom("a"))
        deep=atom("a")
        for _ in range(65):
            deep=fun("f",deep)
        with self.assertRaisesRegex(ValueError,"finite term bound"):
            check(deep)

if __name__=="__main__":
    unittest.main()
