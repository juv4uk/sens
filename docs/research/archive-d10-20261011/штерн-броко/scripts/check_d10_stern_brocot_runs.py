#!/usr/bin/env python3
"""D10 research: compressed exact positive-rational Stern–Brocot tree path.

Formal donor: Isabelle AFP Stern_Brocot_Tree.mk_path, theorem
stern_brocot_rationals. Compression into maximal bit runs is a PROPOSAL.
Python here is a mathematical oracle, not an executable .sens program.
"""
from __future__ import annotations

import argparse
import copy
from fractions import Fraction
from itertools import groupby
import json
from math import gcd
from pathlib import Path
import random
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOSSIER=ROOT/"knowledge/d10-stern-brocot-run-path-20261009.json"
INVENTORY=ROOT/"knowledge/d10-v1-semantic-inventory.json"
FOUNDATION=ROOT/"knowledge/d1-d9-foundation.json"
NAME="STERN-BROCOT-RUN-PATH"


def exact_positive(value):
    if type(value) is int or isinstance(value,Fraction):
        result=Fraction(value)
    else:
        raise TypeError("only an exact rational or exact integer is accepted")
    if result<=0:
        raise ValueError("positive rational required; no sentinels/infinity")
    return result


def compress_path(value):
    """Batch subtraction in Euclid using only exact integer arithmetic."""
    f=exact_positive(value)
    a,b=f.numerator,f.denominator
    result=[]
    while a!=b:
        if a<b:
            k=(b-1)//a  # subtract until b >= a; never subtract past equality
            assert k>0
            result.append((0,k))
            b-=k*a
        else:
            k=(a-1)//b
            assert k>0
            result.append((1,k))
            a-=k*b
    assert a==b==1
    return tuple(result)


def validate_path(runs):
    if not isinstance(runs,(tuple,list)):
        raise TypeError("path must be finite sequence of exact bit/count pairs")
    out=[]
    previous=None
    for pair in runs:
        if not isinstance(pair,(tuple,list)) or len(pair)!=2:
            raise ValueError("run requires exactly (bit, positive_count)")
        direction,count=pair
        if type(direction) is not int or direction not in (0,1):
            raise TypeError("exact D1 0/1 bit required")
        if type(count) is not int or count<=0:
            raise ValueError("strictly positive exact run length required")
        if previous==direction:
            raise ValueError("two equal adjacent directions are not canonical")
        previous=direction
        out.append((direction,count))
    return tuple(out)


def fraction_from_runs(runs):
    """Decode compressed mediant boundaries in O(number of runs)."""
    path=validate_path(runs)
    left_n,left_d=0,1  # 0/1 boundary, never a real data value
    right_n,right_d=1,0  # 1/0 boundary, never an input rational
    for direction,count in path:
        if direction==0:  # compressed k LEFT steps
            right_n+=count*left_n
            right_d+=count*left_d
        else:  # compressed k RIGHT steps
            left_n+=count*right_n
            left_d+=count*right_d
    return Fraction(left_n+right_n,left_d+right_d)


def independent_subtractive_path(value):
    """Independent literal formal mk_path oracle; use on small inputs only."""
    fraction=exact_positive(value)
    a,b=fraction.numerator,fraction.denominator
    steps=[]
    while a!=b:
        if a<b:
            b-=a
            steps.append(0)
        else:
            a-=b
            steps.append(1)
    return tuple((bit,len(list(run))) for bit,run in groupby(steps))


def validate_dossier(d,inv,foundation):
    c=d["candidate"]
    assert d["schema"]=="d10-stern-brocot-run-path-research/v1"
    assert d["status"]=="RESEARCH-PENDING-OWNER-REVIEW"
    assert d["sources"][0]["url"].startswith("https://devel.isa-afp.org/")
    assert d["sources"][1]["url"].startswith("https://doi.org/")
    assert d["sources"][2]["owner_repo"]=="juv4uk/spanda"
    assert d["sources"][2]["blob_sha"]=="d339363e03798941280d7394fb6b24a76ff43dd3"
    assert d["attribution_limit"].startswith("Formal AFP")
    assert c["semantic_name"]==NAME and c["proposal_id"]=="D10P-4952"
    assert c["width"]==10 and c["coordinate"] is None
    assert c["selected"] is False and c["ratified"] is False
    assert c["proposal_status"]=="pending-review"
    assert c["surface_uk"] and c["surface_ukr"]
    assert len(c["positives"])>=9 and len(c["falsifiers"])>=7
    assert c["law"] and c["reverse"] and c["derivability"]
    assert all(item["status"].startswith("HOLD-") for item in d["holds"])
    assert d["accounting"]=={
      "selected_delta":0,"ratified_delta":0,
      "assigned_coordinates":0,"ledger_append_intent":1}
    assert inv["domain"]=="D10" and inv["capacity"]==1024
    assert inv["accounting"]["selected_semantic_candidates"]>=634
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert len(inv["rows"])==inv["accounting"]["selected_semantic_candidates"]
    names={row["semantic_name"] for row in inv["rows"]}
    assert "BOUNDED-RATIONAL-APPROX" in names
    assert "PRIMITIVE-BINARY-WORD-ROOT" in names
    assert NAME not in names, "candidate already selected; reconcile merge first"
    assert foundation["status"]=="owner-ratified"
    lower={str(x).upper() for v in foundation["domains"].values()
           for x in v["residents"].values()}
    assert NAME not in lower and "RATIONAL" in lower
    assert d["snapshot"]["selected"]==634
    assert d["snapshot"]["d10_inventory_sha"]=="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    for case in c["positives"]:
        p=Fraction(case["rational"])
        expected=tuple(tuple(x) for x in case["runs"])
        assert compress_path(p)==expected, (case,compress_path(p))
        assert fraction_from_runs(expected)==p, case
    print("D10 STERN-BROCOT research dossier: PASS (selected +0, ratified +0)")


def adversarial(d,inv,foundation):
    mutants=[
      lambda x:x["candidate"].update(selected=True),
      lambda x:x["candidate"].update(ratified=True),
      lambda x:x["candidate"].update(coordinate="1000000000"),
      lambda x:x["candidate"].update(width=9),
      lambda x:x["candidate"].update(semantic_name="BOUNDED-RATIONAL-APPROX"),
      lambda x:x["candidate"].update(positives=[]),
      lambda x:x["candidate"].update(falsifiers=[]),
      lambda x:x["sources"][0].update(url="unverified"),
      lambda x:x["sources"][2].update(blob_sha="fake-sha"),
      lambda x:x["accounting"].update(selected_delta=1),
      lambda x:x.update(status="SELECTED"),
      lambda x:x["candidate"].update(proposal_status="ratified")
    ]
    for i,mutate in enumerate(mutants):
        fake=copy.deepcopy(d)
        mutate(fake)
        try: validate_dossier(fake,inv,foundation)
        except AssertionError: continue
        raise AssertionError(f"mutant {i} escaped proof gate")
    print(f"D10 STERN-BROCOT: {len(mutants)}/{len(mutants)} fail-closed mutations rejected")


class SternBrocotExact(unittest.TestCase):
    def test_documented_witnesses(self):
        d=json.loads(DOSSIER.read_text(encoding="utf-8"))
        for case in d["candidate"]["positives"]:
            f=Fraction(case["rational"])
            path=tuple(map(tuple,case["runs"]))
            with self.subTest(q=str(f)):
                self.assertEqual(compress_path(f),path)
                self.assertEqual(fraction_from_runs(path),f)

    def test_batched_vs_literal_formal_euclid(self):
        cases=0
        for p in range(1,73):
            for q in range(1,73):
                rat=Fraction(p,q)
                self.assertEqual(compress_path(rat),
                                 independent_subtractive_path(rat))
                self.assertEqual(fraction_from_runs(compress_path(rat)),rat)
                cases+=1
        print(f"D10 STERN-BROCOT: {cases} ratios matched literal AFP mk_path")

    def test_random_large_positive_exact_rationals(self):
        rand=random.Random(20261009)
        for _ in range(2800):
            p=rand.getrandbits(rand.randrange(1,256))+1
            q=rand.getrandbits(rand.randrange(1,256))+1
            rat=Fraction(p,q)
            self.assertEqual(fraction_from_runs(compress_path(rat)),rat)

    def test_arbitrary_canonical_runs_decode_encode(self):
        rand=random.Random(1900)
        for _ in range(2000):
            first=rand.randrange(2)
            runs=tuple(((first+i)%2,rand.randrange(1,10000))
                       for i in range(rand.randrange(0,10)))
            fraction=fraction_from_runs(runs)
            self.assertEqual(compress_path(fraction),runs)

    def test_billion_step_compression(self):
        self.assertEqual(compress_path(Fraction(1,1000000001)),((0,1000000000),))
        self.assertEqual(compress_path(Fraction(1000000001,1)),((1,1000000000),))
        self.assertEqual(fraction_from_runs(((0,1000000000),)),Fraction(1,1000000001))
        self.assertEqual(fraction_from_runs(((1,1000000000),)),Fraction(1000000001,1))

    def test_nonpositive_and_approximate_reject(self):
        for bad in (0,-1,Fraction(-3,4),True,False,1.0,0.1,"3/2",None):
            with self.subTest(value=str(bad)),self.assertRaises((TypeError,ValueError)):
                compress_path(bad)

    def test_noncanonical_path_reject(self):
        bad=[
          ((0,0),), ((1,-1),), ((0,2),(0,3)), ((1,2),(1,1)),
          ((False,1),), ((True,1),), ((0,1.0),), ((1,True),),
          ((2,1),), ((0,1,"extra"),), [(0,)], "0"
        ]
        for candidate in bad:
            with self.subTest(value=str(candidate)),self.assertRaises((ValueError,TypeError)):
                fraction_from_runs(candidate)

    def test_machine_research_metadata_negative_cases(self):
        dossier=json.loads(DOSSIER.read_text(encoding="utf-8"))
        inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
        foundation=json.loads(FOUNDATION.read_text(encoding="utf-8"))
        validate_dossier(dossier,inv,foundation)
        adversarial(dossier,inv,foundation)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    d=json.loads(DOSSIER.read_text(encoding="utf-8"))
    inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
    lower=json.loads(FOUNDATION.read_text(encoding="utf-8"))
    validate_dossier(d,inv,lower)
    if args.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(SternBrocotExact)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
