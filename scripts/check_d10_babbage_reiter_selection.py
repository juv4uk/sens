#!/usr/bin/env python3
"""Fail-closed 635->637 D10 source research, with two independent finite exact oracles.

This checks mathematics against independent finite algorithms, NOT a real
historical mechanical computer nor a complete logical circuit diagnosis.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
from fractions import Fraction
from math import comb
from pathlib import Path
from random import Random

ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/"knowledge/d10-v1-semantic-inventory.json"
STATE=ROOT/"knowledge/d10-fill-v1-state.json"
FOUND=ROOT/"knowledge/d1-d9-foundation.json"
SOURCE=ROOT/"knowledge/d10-babbage-reiter-hobby-selected-20261009.json"
ARCH=ROOT/"docs/architecture/ARCHIPELAGO-V1.uk.md"
NAMES=("FINITE-DIFFERENCE-CERTIFICATE","MINIMAL-CONFLICT-DIAGNOSES")
SRC_CLASS=("BABBAGE-1822-EXACT-DIFFERENCES-RESEARCH","REITER-1987-MODEL-BASED-DIAGNOSIS-RESEARCH")

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def blob_hash(data):
    raw=(json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def verify(i,s,f,p,document):
    assert p["schema"]=="d10-babbage-reiter-hobby-selected/v1"
    assert p["status"]=="SELECTED-RESEARCH-CANDIDATES-UNRATIFIED"
    assert p["accounting"]=={
        "prior_selected":635,"added_selected":2,"after_selected":637,
        "after_unplaced":381,"remaining":387,
        "ratified_added":0,"coordinate_added":0}
    assert len(i["rows"])==637 and i["capacity"]==1024 and i["width"]==10
    assert i["accounting"]==dict(selected_semantic_candidates=637,law_forced_coordinates=256,unplaced_selected_candidates=381,remaining_semantic_inventory=387,ratified_d10_residents=0)
    assert s["target"]["selected_semantic_candidates"]==637
    assert s["target"]["unplaced_selected_candidates"]==381
    assert s["target"]["remaining_semantic_candidates"]==387
    assert s["target"]["ratified_residents"]==0
    assert "D10 selected              637/1024" in document
    assert "unplaced                  381" in document
    assert "remaining                 387" in document
    assert "ratified                    0" in document
    assert i["sources"][-1]=="knowledge/d10-babbage-reiter-hobby-selected-20261009.json"
    assert len({r["stable_id"] for r in i["rows"]})==637
    assert len({r["semantic_name"] for r in i["rows"]})==637
    lower={str(n).upper() for d in f["domains"].values() for n in d["residents"].values()}
    assert not (set(NAMES)&lower)
    assert len(p["rows"])==2
    assert [r["semantic_name"] for r in p["rows"]]==list(NAMES)
    assert [r["semantic_name"] for r in i["rows"][-2:]]==list(NAMES)
    assert sum(r["coordinate"] is not None for r in i["rows"])==256
    old=copy.deepcopy(i)
    old["rows"]=old["rows"][:635]
    old["sources"].pop()
    old["accounting"]["selected_semantic_candidates"]=635
    old["accounting"]["unplaced_selected_candidates"]=379
    old["accounting"]["remaining_semantic_inventory"]=389
    assert blob_hash(old)==p["snapshot"]["d10_prior_blob"],"old 635-row authority changed"
    assert p["snapshot"]["foundation_blob"]==blob_hash(f),"ratified D1-D9 changed"
    for row,current,category in zip(p["rows"],i["rows"][-2:],SRC_CLASS):
        assert row["stable_id"]==current["stable_id"]
        assert row["source_class"]==current["source_class"]==category
        assert row["semantic_name"]==current["semantic_name"]
        assert row["coordinate"] is None and current["coordinate"] is None
        assert row["ratified_resident"] is False and current["ratified_resident"] is False
        assert row["physical_t5_authorized"] is False and current["physical_t5_authorized"] is False
        assert row["status"]==current["status"]=="SELECTED-RESEARCH-CANDIDATE"
        assert row["proposal_status"]==current["proposal_status"]=="pending-owner-review"
        assert row["surface_uk"] and row["surface_ukr"]
        assert row["positive_witnesses"] and len(row["positive_witnesses"])>=3
        assert row["falsifiers"] and row["dedup_check"]
        assert row["source_scope"] and row["primary_url"].startswith("https://")
        assert row["primary_url"]==current["primary_url"]
        assert row["argument_shape"]==current["argument_shape"]
    return True

def difference_layers(samples):
    levels=[tuple(Fraction(x) for x in samples)]
    while len(levels[-1])>1:
        x=levels[-1]
        levels.append(tuple(x[j+1]-x[j] for j in range(len(x)-1)))
    return levels

def difference_certificate(samples,d):
    if d<0: return ("INVALID-DEGREE",)
    if len(samples)<d+2: return ("INSUFFICIENT-DATA",)
    levels=difference_layers(samples)
    residual=levels[d+1]
    for index,v in enumerate(residual):
        if v: return ("NOT-CERTIFIED",index,v)
    coeff=tuple(levels[j][0] for j in range(d+1))
    forecast=sum((Fraction(comb(len(samples),j))*coeff[j] for j in range(d+1)),Fraction(0))
    return ("CERTIFIED",coeff,forecast)

def difference_reference_step(samples,d):
    """Independent recurrence using last diagonal, not Newton's binomial sum."""
    levels=difference_layers(samples)
    last=[levels[j][-1] for j in range(d+1)]
    for j in range(d-1,-1,-1):
        last[j]+=last[j+1]
    return last[0]

def canonical(family):
    return tuple(sorted({tuple(sorted(s)) for s in family},key=lambda s:(len(s),s)))

def brute_diagnoses(universe,conflicts):
    universe=tuple(sorted(set(universe)))
    family=[frozenset(c) for c in conflicts]
    assert all(c.issubset(set(universe)) for c in family)
    hits=[]
    for bit in range(1<<len(universe)):
        diag=frozenset(universe[j] for j in range(len(universe)) if bit>>j&1)
        if all(diag&c for c in family):
            if all(any(not ((diag-{piece}) & c) for c in family) for piece in diag):
                hits.append(diag)
    return canonical(hits)

def incremental_diagnoses(universe,conflicts):
    universe=set(universe)
    candidates={frozenset()}
    for conflict in conflicts:
        conflict=set(conflict)
        assert conflict.issubset(universe)
        if not conflict: return ()
        grown=set()
        for chosen in candidates:
            if chosen&conflict: grown.add(chosen)
            else:
                grown.update(chosen|{part} for part in conflict)
        candidates={x for x in grown if not any(y<x for y in grown)}
    return canonical(candidates)

def finite_witnesses():
    assert difference_certificate([1,4,9,16],2)==("CERTIFIED",(Fraction(1),Fraction(3),Fraction(2)),Fraction(25))
    assert difference_certificate([7,7,7],0)==("CERTIFIED",(Fraction(7),),Fraction(7))
    assert difference_certificate([1,4,9,17],2)==("NOT-CERTIFIED",0,Fraction(1))
    assert difference_certificate([1,4,9],2)==("INSUFFICIENT-DATA",)
    assert difference_certificate([1,2],0)==("NOT-CERTIFIED",0,Fraction(1))
    assert difference_certificate([0,0],-1)==("INVALID-DEGREE",)
    assert difference_certificate([Fraction(1,2),Fraction(3,2),Fraction(5,2)],1)[-1]==Fraction(7,2)
    count=0
    for degree in range(4):
        for coeff in itertools.product(range(-2,3),repeat=degree+1):
            vals=[sum(Fraction(coeff[j])*comb(n,j) for j in range(degree+1))
                  for n in range(degree+4)]
            cert=difference_certificate(vals,degree)
            assert cert[0]=="CERTIFIED"
            assert cert[-1]==difference_reference_step(vals,degree)
            assert cert[-1]==sum(Fraction(coeff[j])*comb(len(vals),j) for j in range(degree+1))
            wrong=vals[:]
            wrong[-1]+=1
            assert difference_certificate(wrong,degree)[0]=="NOT-CERTIFIED"
            count+=1
    assert brute_diagnoses(["A","B","C"],[{"A","B"},{"B","C"}])==(("B",),("A","C"))
    assert brute_diagnoses(["A","B"],[])==((),)
    assert brute_diagnoses(["A","B"],[set()])==()
    assert brute_diagnoses(["A","B","C"],[{"A","B"},{"B","C"}])==incremental_diagnoses(["A","B","C"],[{"A","B"},{"B","C"}])
    conflict_cases=0
    for count_components in range(4):
        components=tuple(range(count_components))
        subsets=[frozenset(components[j] for j in range(count_components) if mask>>j&1)
                 for mask in range(1<<count_components)]
        for fam_mask in range(1<<len(subsets)):
            family=[subsets[j] for j in range(len(subsets)) if fam_mask>>j&1]
            assert brute_diagnoses(components,family)==incremental_diagnoses(components,family)
            conflict_cases+=1
    rng=Random(1987)
    for _ in range(250):
        components=tuple(range(4))
        family=[frozenset(x for x in components if rng.randrange(2)) for _ in range(rng.randrange(7))]
        assert brute_diagnoses(components,family)==incremental_diagnoses(components,family)
        conflict_cases+=1
    return count,conflict_cases

def adversarial(p,i,s,f,doc):
    def reject(mut):
        pp,ii,ss=copy.deepcopy(p),copy.deepcopy(i),copy.deepcopy(s)
        mut(pp,ii,ss)
        try:verify(ii,ss,f,pp,doc)
        except AssertionError:return
        raise AssertionError("invalid promotion or drift passed fail-closed guard")
    reject(lambda p,i,s:p["rows"][0].__setitem__("coordinate","0000000000"))
    reject(lambda p,i,s:p["rows"][1].__setitem__("ratified_resident",True))
    reject(lambda p,i,s:p["rows"][0].__setitem__("semantic_name","UNIFY"))
    reject(lambda p,i,s:i["rows"][0].__setitem__("behavior","tampered"))
    reject(lambda p,i,s:i["rows"][-1].__setitem__("status","RATIFIED"))
    reject(lambda p,i,s:i["rows"].pop())
    reject(lambda p,i,s:s["target"].__setitem__("selected_semantic_candidates",635))
    reject(lambda p,i,s:p["rows"][0].__setitem__("primary_url","https://wrong.example"))
    reject(lambda p,i,s:p["accounting"].__setitem__("coordinate_added",1))
    reject(lambda p,i,s:p["rows"][1].__setitem__("positive_witnesses",[]))
    return 10

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--self-test",action="store_true")
    a=arg.parse_args()
    i,s,f,p=map(load,(INV,STATE,FOUND,SOURCE))
    doc=ARCH.read_text(encoding="utf-8")
    verify(i,s,f,p,doc)
    polynomial_cases,diagnosis_cases=finite_witnesses()
    negative=adversarial(p,i,s,f,doc) if a.self_test else 0
    print(f"PASS D10 635->637, rational polynomial cases={polynomial_cases}, finite conflict families={diagnosis_cases}, rejected mutations={negative}, ratified=0, coordinates added=0")
if __name__=="__main__":
    main()
