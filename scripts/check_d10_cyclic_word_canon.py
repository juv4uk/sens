#!/usr/bin/env python3
"""D10 research oracle: least cyclic binary word + earliest original phase.

Booth (1980) O(n) minimum circular shift, followed by KMP O(n) to
pick the earliest shift in the original input among tied periodic minima.
Independent finite enumerator verifies the exact full-length law.
This is NOT executable binary SENS or its packed T5 representation.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"knowledge/d10-cyclic-word-canon-20261009.json"
D10=ROOT/"knowledge/d10-v1-semantic-inventory.json"
LOWER=ROOT/"knowledge/d1-d9-foundation.json"
NAME="CYCLIC-BINARY-WORD-CANON"


def bits(value):
    """A test-only textual helper. Machine candidate accepts PredicateBits."""
    if not isinstance(value,str) or not value or any(v not in "01" for v in value):
        raise ValueError("test fixture must be a nonempty bit spelling")
    return tuple(int(x) for x in value)


def check_word(value):
    if not isinstance(value,(tuple,list)) or not value:
        raise ValueError("nonempty finite PredicateBit vector is required")
    if any(type(x) is not int or x not in (0,1) for x in value):
        raise TypeError("every element must be an exact bit, not boolean/float/text")
    return tuple(value)


def booth_phase(word):
    """Find an index of lexicographically minimal full circular rotation."""
    n=len(word)
    i,j,k=0,1,0
    while i<n and j<n and k<n:
        a,b=word[(i+k)%n],word[(j+k)%n]
        if a==b:
            k+=1
            continue
        if a>b:
            i=i+k+1
            if i<=j:
                i=j+1
        else:
            j=j+k+1
            if j<=i:
                j=i+1
        k=0
    return min(i,j)%n


def kmp_first_pattern(haystack,pattern):
    """Return earliest complete pattern start using exact bit equality."""
    n=len(pattern)
    failure=[0]*n
    k=0
    for j in range(1,n):
        while k and pattern[j]!=pattern[k]:
            k=failure[k-1]
        if pattern[j]==pattern[k]:
            k+=1
        failure[j]=k
    k=0
    for i,ch in enumerate(haystack):
        while k and ch!=pattern[k]:
            k=failure[k-1]
        if ch==pattern[k]:
            k+=1
        if k==n:
            return i-n+1
    raise AssertionError("canonical rotation must occur in its doubled input")


def canonical(word):
    w=check_word(word)
    n=len(w)
    b=booth_phase(w)
    minimum=w[b:]+w[:b]
    earliest=kmp_first_pattern(w+w[:-1],minimum)
    assert 0<=earliest<n
    assert w[earliest:]+w[:earliest]==minimum
    return minimum,earliest


def independent_enumeration(word):
    """Separate direct finite-orbit specification, intentionally O(n²)."""
    w=check_word(word)
    return min((w[i:]+w[:i],i) for i in range(len(w)))


def check_dossier(doc,inventory,foundation):
    c=doc["candidate"]
    assert doc["schema"]=="d10-cyclic-binary-word-canon-research/v1"
    assert doc["status"]=="RESEARCH-PENDING-OWNER-REVIEW"
    assert doc["sources"][0]["url"].startswith("https://doc.sagemath.org/")
    assert doc["sources"][1]["url"].startswith("https://doi.org/")
    assert doc["sources"][2]["repository"]=="juv4uk/spanda"
    assert doc["sources"][2]["blob_sha"]=="d339363e03798941280d7394fb6b24a76ff43dd3"
    assert doc["historical_boundary"].startswith("Sage and Booth")
    assert c["semantic_name"]==NAME and c["proposal_id"]=="D10P-4937"
    assert c["width"]==10 and c["coordinate"] is None
    assert c["ratified"] is False and c["selected"] is False
    assert c["proposal_status"]=="pending-review"
    assert c["surface_uk"] and c["surface_ukr"] and c["law"]
    assert len(c["positives"])>=8 and len(c["falsifiers"])>=7
    assert len(c["existing_behavioral_neighbors"])>=4 and c["derivability"]
    assert all(c["no_changes"])
    assert doc["accounting"]=={
      "selected_additions":0,"ratified_additions":0,
      "coordinates_allocated":0,"ledger_append_intent":1}
    assert inventory["domain"]=="D10" and inventory["capacity"]==1024
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert inventory["accounting"]["selected_semantic_candidates"]>=632
    assert len(inventory["rows"])==inventory["accounting"]["selected_semantic_candidates"]
    names={r["semantic_name"] for r in inventory["rows"]}
    assert "PRIMITIVE-BINARY-WORD-ROOT" in names
    assert NAME not in names, "selected separately: update this research gate"
    assert foundation["status"]=="owner-ratified"
    low={str(n).upper() for d in foundation["domains"].values()
         for n in d["residents"].values()}
    assert "ROTATE" in low and NAME not in low
    assert doc["snapshot"]["selected"]==632
    assert doc["snapshot"]["d10_inventory_blob_sha"]=="7683f1e2bfcf67d3a45d412d3b1790b72ad623ad"
    for row in c["positives"]:
        got,index=canonical(bits(row["word"]))
        assert "".join(str(x) for x in got)==row["canonical"]
        assert index==row["least_left_shift"]
    print("D10 CYCLIC CANON research dossier: PASS, +0 selected, +0 ratified")


class BinaryCycleLaw(unittest.TestCase):
    def test_documented_witnesses(self):
        e=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        for row in e["candidate"]["positives"]:
            with self.subTest(word=row["word"]):
                got,shift=canonical(bits(row["word"]))
                self.assertEqual(got,bits(row["canonical"]))
                self.assertEqual(shift,row["least_left_shift"])

    def test_exhaustive_8190_binary_words(self):
        count=0
        for n in range(1,13):
            for value in range(1<<n):
                w=tuple((value>>j)&1 for j in range(n-1,-1,-1))
                self.assertEqual(canonical(w),independent_enumeration(w))
                count+=1
        self.assertEqual(count,8190)
        print("D10 CYCLIC CANON: 8190/8190 exact words agree with exhaustive orbit")

    def test_long_random_binary_words(self):
        rng=random.Random(20261009)
        for _ in range(2000):
            w=tuple(rng.randrange(2) for _ in range(rng.randrange(1,129)))
            self.assertEqual(canonical(w),independent_enumeration(w))

    def test_rotation_orbit_canonical_invariant(self):
        rng=random.Random(2229)
        for _ in range(400):
            w=tuple(rng.randrange(2) for _ in range(rng.randrange(1,101)))
            c,_=canonical(w)
            for k in {0,1,len(w)//2,len(w)-1}:
                rotated=w[k:]+w[:k]
                self.assertEqual(canonical(rotated)[0],c)

    def test_periodic_ties_choose_least_shift(self):
        self.assertEqual(canonical(bits("101010")), (bits("010101"),1))
        self.assertEqual(canonical(bits("010101")), (bits("010101"),0))
        self.assertEqual(canonical(bits("111111")), (bits("111111"),0))
        self.assertEqual(canonical(bits("100100")), (bits("001001"),1))
        self.assertEqual(canonical(bits("010010")), (bits("001001"),2))

    def test_primitive_word_distinction(self):
        c,k=canonical(bits("01010"))
        self.assertEqual((c,k),(bits("00101"),4))
        self.assertEqual(len(c),5)
        c,k=canonical(bits("1010"))
        self.assertEqual((c,k),(bits("0101"),1))
        self.assertEqual(len(c),4)

    def test_input_type_barrier(self):
        for bad in [[],(),[True,0],[False,1],[1.0,0],[2,0],
                    "1010",b"1010",[1,"0"],[None,1]]:
            with self.subTest(value=bad):
                with self.assertRaises((ValueError,TypeError)):
                    canonical(bad)

    def test_machine_dossier_negative_mutants(self):
        evidence=json.loads(EVIDENCE.read_text(encoding="utf-8"))
        inventory=json.loads(D10.read_text(encoding="utf-8"))
        lower=json.loads(LOWER.read_text(encoding="utf-8"))
        check_dossier(evidence,inventory,lower)
        mutations=[
         lambda d:d["candidate"].update(selected=True),
         lambda d:d["candidate"].update(ratified=True),
         lambda d:d["candidate"].update(coordinate="1000000000"),
         lambda d:d["candidate"].update(width=9),
         lambda d:d["candidate"].update(semantic_name="ROTATE"),
         lambda d:d["candidate"].update(positives=[]),
         lambda d:d["candidate"].update(falsifiers=[]),
         lambda d:d["sources"][0].update(url="unverified"),
         lambda d:d["sources"][2].update(blob_sha="not-a-commit"),
         lambda d:d["accounting"].update(selected_additions=1),
         lambda d:d.update(status="SELECTED"),
         lambda d:d["candidate"].update(proposal_status="ratified")
        ]
        for i,fn in enumerate(mutations):
            bad=copy.deepcopy(evidence)
            fn(bad)
            with self.subTest(adversarial=i):
                with self.assertRaises(AssertionError):
                    check_dossier(bad,inventory,lower)
        print("D10 CYCLIC CANON: 12/12 source/selection mutants blocked")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    e=json.loads(EVIDENCE.read_text(encoding="utf-8"))
    inv=json.loads(D10.read_text(encoding="utf-8"))
    low=json.loads(LOWER.read_text(encoding="utf-8"))
    check_dossier(e,inv,low)
    if args.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(BinaryCycleLaw)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
