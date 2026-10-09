#!/usr/bin/env python3
"""Deterministic donor-law oracle for D10 scientific composite candidates.

No SENS binary opcodes or runtime parity are implied; no external dependencies.
"""
import copy
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "knowledge/d10-interdisciplinary-science-proposals-20261009.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
SELECTED = ("COVARIANCE-TRANSPORT", "FRAME-STATE-TRANSFORM", "RATIONAL-RESAMPLE")

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def mul(A, B):
    assert A and B and len(A[0]) == len(B)
    assert all(len(r) == len(A[0]) for r in A)
    assert all(len(r) == len(B[0]) for r in B)
    return [[sum(a*b for a,b in zip(ar, col)) for col in zip(*B)] for ar in A]

def tr(A):
    return list(map(list, zip(*A)))

def covariance_transport(J, Sigma):
    n=len(Sigma)
    assert n>0 and all(len(row)==n for row in Sigma)
    assert J and all(len(row)==n for row in J)
    assert Sigma == tr(Sigma), "covariance must be symmetric"
    return mul(mul(J,Sigma),tr(J))

def frame_state_transform(R,Rdot,p,v):
    assert len(R)==len(Rdot)==len(p)==len(v)==3
    assert all(len(row)==3 for row in R+Rdot)
    q=mul(R,[[x] for x in p])
    rv=mul(R,[[x] for x in v])
    dp=mul(Rdot,[[x] for x in p])
    return tuple(x[0] for x in q), tuple(rv[i][0]+dp[i][0] for i in range(3))

def rational_resample(signal,L,M,taps):
    assert isinstance(L,int) and isinstance(M,int) and L>0 and M>0
    assert taps, "explicit causal FIR taps required"
    up=[0]*(len(signal)*L)
    for i,x in enumerate(signal):
        up[i*L]=x
    return [
        sum(h*up[n-k] for k,h in enumerate(taps) if n-k>=0)
        for n in range(0,len(up),M)
    ]

def historical_oracles():
    F=Fraction
    Sigma=[[F(4),F(2)],[F(2),F(9)]]
    J=[[1,1],[1,-1]]
    assert covariance_transport(J,Sigma)==[[F(17),F(-5)],[F(-5),F(9)]]
    assert covariance_transport([[1,0],[0,1]],Sigma)==Sigma
    assert covariance_transport([[1,1]],Sigma)==[[F(17)]]
    assert covariance_transport([[1,0]],[[F(1),F(0)],[F(0),F(1)]])==[[F(1)]]
    try:
        covariance_transport([[1,0,0]],Sigma)
    except AssertionError:
        pass
    else:
        raise AssertionError("bad covariance shape accepted")
    R=[[0,-1,0],[1,0,0],[0,0,1]]
    Rd=[[-2,0,0],[0,-2,0],[0,0,0]]
    pos,vel=frame_state_transform(R,Rd,(1,0,0),(0,0,0))
    assert pos==(0,1,0) and vel==(-2,0,0)
    assert vel != (0,0,0), "cannot omit rotating-frame derivative"
    assert frame_state_transform([[1,0,0],[0,1,0],[0,0,1]],[[0,0,0]]*3,(3,2,1),(1,2,3))==((3,2,1),(1,2,3))
    try:
        frame_state_transform([[1]],[[1]],(1,0,0),(0,0,0))
    except AssertionError:
        pass
    else:
        raise AssertionError("non-3D frame matrix accepted")
    taps=[F(1,4),F(1,2),F(1,4)]
    assert rational_resample([2,4,6],2,3,taps)==[F(1,2),F(2)]
    full=rational_resample([2,4,6,8,10],2,3,taps)
    for i in range(6):
        assert rational_resample([2,4,6,8,10][:i],2,3,taps)==full[:len(range(0,i*2,3))]
    assert rational_resample([],2,3,taps)==[]
    assert rational_resample([1],1,1,[F(1)])==[F(1)]
    for l,m in ((0,1),(1,0),(-1,1)):
        try: rational_resample([1],l,m,taps)
        except AssertionError: pass
        else: raise AssertionError("invalid sample rate admitted")
    print("D10 science donor exact-arithmetic oracles: PASS (covariance, frame-state, causal FIR resampling; no SENS parity)")

def validate(inv,st,found,source):
    assert source["schema"] == "d10-interdisciplinary-scientific-laws/v1"
    assert source["selected_count"] == 3
    assert source["hold_count"] == 8
    assert len(source["selected_semantic_candidates"])==3
    assert len(source["hold_for_derivability"])==8
    assert len({x["semantic_name"] for x in source["hold_for_derivability"]})==8
    assert all(x["selected"] is False and x["coordinate"] is None for x in source["hold_for_derivability"])
    assert found["status"]=="owner-ratified"
    assert inv["accounting"]["selected_semantic_candidates"] == len(inv["rows"])
    assert inv["accounting"]["law_forced_coordinates"] == 256
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert len(inv["rows"]) <= 1024
    assert st["target"]["selected_semantic_candidates"] == len(inv["rows"])
    assert st["target"]["unplaced_selected_candidates"] == len(inv["rows"])-256
    assert st["target"]["remaining_semantic_candidates"] == 1024-len(inv["rows"])
    assert st["target"]["ratified_residents"]==0
    by_name={r["semantic_name"]:r for r in inv["rows"]}
    assert len(by_name)==len(inv["rows"])
    names_low={str(s).upper() for d in found["domains"].values() for s in d["residents"].values()}
    assert not set(SELECTED)&names_low
    assert not {x["semantic_name"] for x in source["hold_for_derivability"]}&set(SELECTED)
    assert "knowledge/d10-interdisciplinary-science-proposals-20261009.json" in inv["sources"]
    for name in SELECTED:
        row=by_name[name]
        match=next(p for p in source["selected_semantic_candidates"] if p["semantic_name"]==name)
        assert row["stable_id"]==match["stable_id"]
        assert row["behavior"]==match["law"]
        assert row["primary_url"]==match["source_url"]
        assert row["source_path"]=="knowledge/d10-interdisciplinary-science-proposals-20261009.json"
        assert row["source_class"]=="INTERDISCIPLINARY-SCIENTIFIC-LAW"
        assert row["status"]=="SELECTED-RESEARCH-CANDIDATE"
        assert row["proposal_status"]=="pending-owner-review"
        assert row["decision"]=="SELECT-D10-CANDIDATE"
        assert row["coordinate"] is None and row["coordinate_basis"]=="UNPLACED"
        assert row["ratified_resident"] is False and row["donor_coordinate_authority"]=="NONE"
        assert len(row["positive_witnesses"])>=2 and len(row["falsifiers"])>=2
        assert row["surface_uk"] and row["surface_ukr"] and row["minimality"]
    return True

def negative_controls(inv,st,found,src):
    validate(inv,st,found,src)
    for key,val in (("coordinate","1111111111"),("ratified_resident",True),
                    ("source_path","fake/source.json"),("primary_url","https://fake.invalid"),
                    ("positive_witnesses",[]),("status","RATIFIED"),
                    ("proposal_status","ratified")):
        bad=copy.deepcopy(inv)
        badrow=next(x for x in bad["rows"] if x["semantic_name"]=="FRAME-STATE-TRANSFORM")
        badrow[key]=val
        try: validate(bad,st,found,src)
        except AssertionError: continue
        raise AssertionError("invalid selection escaped: "+key)
    bad=copy.deepcopy(src)
    bad["hold_for_derivability"][0]["selected"]=True
    try: validate(inv,st,found,bad)
    except AssertionError: pass
    else: raise AssertionError("HOLD promoted silently")
    print("D10 science source/geometry negative controls: PASS 8/8")

if __name__=="__main__":
    inv,st,found,src=(load(p) for p in (INVENTORY,STATE,FOUNDATION,SOURCE))
    validate(inv,st,found,src)
    negative_controls(inv,st,found,src)
    historical_oracles()
    print("D10 science research-only selection validation: PASS",len(inv["rows"]))
