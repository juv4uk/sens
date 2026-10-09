#!/usr/bin/env python3
"""Early perceptron exact-rational one-step law, research-only (not native SENS)."""
from __future__ import annotations
import copy
import itertools
import json
from fractions import Fraction as Q
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"knowledge/d10-rosenblatt-novikoff-exact-step-20261009.json"

def exact(value):
    if type(value) is bool or isinstance(value,float):
        raise TypeError("exact rational required")
    if type(value) not in (int,str,Q):
        raise TypeError("exact rational value type required")
    return Q(value)

def step(weights,features,label,eta):
    if type(label) is not int or label not in (-1,1):
        raise ValueError("label must be -1 or +1, not D1 bool")
    if not isinstance(weights,(tuple,list)) or not isinstance(features,(tuple,list)):
        raise ValueError("vectors must be sequences")
    if len(weights)==0 or len(weights)!=len(features):
        raise ValueError("equal nonempty vector length required")
    w=tuple(map(exact,weights))
    x=tuple(map(exact,features))
    rate=exact(eta)
    if rate<=0 or not any(x):
        raise ValueError("positive rate and nonzero feature required")
    margin=label*sum((a*b for a,b in zip(w,x)),Q(0))
    if margin>0:
        return w,False
    return tuple(a+rate*label*b for a,b in zip(w,x)),True

def independently_verify(weights, features, label, eta):
    w=tuple(map(exact,weights))
    x=tuple(map(exact,features))
    rate=exact(eta)
    before=label*sum([a*b for a,b in zip(w,x)],Q(0))
    new, updated=step(w,x,label,rate)
    after=label*sum([a*b for a,b in zip(new,x)],Q(0))
    if updated:
        assert before<=0
        assert after-before==rate*sum([v*v for v in x],Q(0))
        assert after>before
    else:
        assert before>0 and new==w and after==before
    return new,updated

def guard(d):
    assert d["schema"]=="d10-historical-neural-ai-exact-perceptron/v1"
    assert d["status"]=="HOLD-SOURCE-GROUNDED-NONRATIFIED"
    assert d["baseline"]["inventory_blob"]=="3db40a04c1094c9ea13b0c8d6099ef1d882cf203"
    assert d["baseline"]["ratified"]==0
    assert d["source"][0]["doi"]=="10.1037/h0042519"
    assert d["source"][1]["year"]==1962
    assert d["scope"]["selected_delta"]==d["scope"]["ratified_delta"]==d["scope"]["coordinate_delta"]==0
    assert d["scope"]["d2_delta"]==d["scope"]["t5_delta"]==0
    c=d["candidate"]
    assert c["name"]=="EXACT-PERCEPTRON-MISTAKE-STEP"
    assert c["status"]=="HOLD-CORE-VERSUS-LIBRARY"
    assert c["coordinate"] is None and c["ratified"] is False
    assert c["width"]==10
    assert len(c["positives"])>=4 and len(c["falsifiers"])>=5
    assert len(d["holds"])>=4
    assert all(z["decision"]!="SELECTED" for z in d["holds"])

def experiment(d):
    positive=0
    for example in d["candidate"]["positives"]:
        value,flag=independently_verify(example["w"],example["x"],example["y"],example["eta"])
        assert list(map(str,value))==example["result"]
        assert flag is example["corrected"]
        positive+=1

    # Exact finite corpus, independent signed-margin identity check.
    values=(-1,Q(-1,2),0,Q(1,2),1)
    xs=(-2,-1,0,1,2)
    eta=(Q(1,2),Q(1),Q(2))
    corpus=0
    for w0,w1,x0,x1 in itertools.product(values,values,xs,xs):
        if not (x0 or x1):
            continue
        for label in (-1,1):
            for rate in eta:
                independently_verify((w0,w1),(x0,x1),label,rate)
                corpus+=1
    assert corpus==3600
    assert step((Q(0),Q(0)),(1,1),1,1)==((Q(1),Q(1)),True)
    assert step((Q(0),Q(0)),(1,1),-1,1)==((Q(-1),Q(-1)),True)
    assert step((2,2),(1,1),1,1)==((Q(2),Q(2)),False)
    return positive,corpus

def invalid_inputs():
    cases=[
       ((0,), (1,), 0, 1),
       ((0,), (1,), True, 1),
       ((0,), (0,), 1, 1),
       ((0,), (1,), 1, 0),
       ((0,), (1,), 1, -1),
       ((0,), (1,), 1, 0.1),
       ((0,), (1,2), 1, 1),
       ((), (), 1, 1),
       ((0.0,), (1,), 1, 1),
       ((0,), (True,), 1, 1)
    ]
    for example in cases:
        try:step(*example)
        except (TypeError,ValueError,ZeroDivisionError):continue
        raise AssertionError("invalid learning example accepted")
    return len(cases)

def mutations(d):
    corrupters=[
      lambda x:x["scope"].update(selected_delta=1),
      lambda x:x["scope"].update(ratified_delta=1),
      lambda x:x["scope"].update(coordinate_delta=1),
      lambda x:x["scope"].update(t5_delta=1),
      lambda x:x["candidate"].update(coordinate="0"*10),
      lambda x:x["candidate"].update(ratified=True),
      lambda x:x["candidate"].update(status="SELECTED"),
      lambda x:x["candidate"]["positives"].clear(),
      lambda x:x["baseline"].update(inventory_blob="0"*40),
      lambda x:x["source"][0].update(doi="forged")
    ]
    for i,change in enumerate(corrupters):
        altered=copy.deepcopy(d)
        change(altered)
        try:guard(altered)
        except AssertionError:continue
        raise AssertionError(f"mutation #{i} not rejected")

def main():
    data=json.loads(SOURCE.read_text(encoding="utf-8"))
    guard(data)
    positives,corpus=experiment(data)
    rejected=invalid_inputs()
    mutations(data)
    print(f"D10-PERCEPTRON: PASS examples={positives}, exact_invariant_cases={corpus}, invalid={rejected}, negative_mutations=10")
    print("One source-pinned 1958/1962 research HOLD; no selection, ratification, physical T5, or native binary claim.")

if __name__=="__main__":
    main()
