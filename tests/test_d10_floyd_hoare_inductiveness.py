#!/usr/bin/env python3
"""Finite inductive safety certificate, exact bounded research oracle."""
import copy
import itertools
import json
from collections import deque
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]/"knowledge/d10-floyd-hoare-finite-inductiveness-20261009.json"

def check(states,initial,invariant,edges):
    domain=set(states)
    if len(domain)!=len(states) or not set(initial)<=domain or not set(invariant)<=domain:
        raise ValueError("invalid state domain")
    if any(len(edge)!=2 or not set(edge)<=domain for edge in edges):
        raise ValueError("invalid transition endpoint")
    outside=sorted(set(initial)-set(invariant))
    if outside:return {"valid":False,"reason":"INITIAL-OUTSIDE","witness":outside[0]}
    bad=sorted((a,b) for a,b in edges if a in invariant and b not in invariant)
    if bad:return {"valid":False,"reason":"ESCAPING-EDGE","witness":list(bad[0])}
    return {"valid":True}

def reachable(initial,edges):
    seen=set(initial)
    pending=deque(initial)
    while pending:
        node=pending.popleft()
        for a,b in edges:
            if a==node and b not in seen:
                seen.add(b)
                pending.append(b)
    return seen

def verify(source):
    c=source["candidate"]
    assert source["schema"]=="d10-floyd-hoare-finite-inductiveness/v1"
    assert source["decision"]=="RESEARCH-PENDING-PEER-NOT-SELECTED"
    assert source["snapshot"]["selected"]==635
    assert source["snapshot"]["ratified"]==0
    assert c["semantic_name"]=="FINITE-INDUCTIVE-SAFETY-WITNESS"
    assert c["proposal_id"]=="D10P-0914" and c["width"]==10
    assert c["coordinate"] is None and c["ratified_resident"] is False
    assert c["selection_status"]=="PENDING-REVIEW"
    assert len(c["positives"])>=6 and len(c["falsifiers"])>=5
    assert len(source["histories"])>=3 and len(source["derived_or_hold"])>=4
    assert source["impact"]==dict(selected_delta=0,ratified_delta=0,coordinate_delta=0,d2_control_delta=0)
    return c

def run():
    source=json.loads(SOURCE.read_text(encoding="utf-8"))
    c=verify(source)
    for e in c["positives"]:
        assert check(e["states"],e["initial"],e["invariant"],e["edges"])==e["expected"]
    states=("A","B","C")
    sets=[frozenset(s for k,s in enumerate(states) if mask&(1<<k)) for mask in range(8)]
    candidates=list(itertools.product(states,repeat=2))
    tested=0
    for initial,inv in itertools.product(sets,repeat=2):
        for mask in range(512):
            edges=[pair for k,pair in enumerate(candidates) if mask&(1<<k)]
            ans=check(states,initial,inv,edges)
            independent=all(s in inv for s in initial) and all(a not in inv or b in inv for a,b in edges)
            assert ans["valid"]==independent
            if independent:assert reachable(initial,edges)<=inv
            tested+=1
    mutation_cases=[
        lambda d:d["candidate"].update(coordinate="0"*10),
        lambda d:d["candidate"].update(ratified_resident=True),
        lambda d:d["candidate"].update(selection_status="SELECTED"),
        lambda d:d["impact"].update(selected_delta=1),
        lambda d:d["impact"].update(d2_control_delta=1),
        lambda d:d["candidate"].update(proposal_id="D10P-9999"),
        lambda d:d["candidate"].update(width=8),
        lambda d:d["candidate"]["positives"].clear(),
        lambda d:d["candidate"]["falsifiers"].clear(),
        lambda d:d["histories"].clear(),
    ]
    for mutate in mutation_cases:
        d=copy.deepcopy(source)
        mutate(d)
        try:verify(d)
        except AssertionError:continue
        raise AssertionError("tampered dossier passed")
    for args in [(["A"],["X"],[],[]),(["A"],[],["X"],[]),(["A"],[],["A"],[["A","X"]])]:
        try:check(*args)
        except ValueError:continue
        raise AssertionError("unknown state accepted")
    print(f"FLOYD-HOARE FINITE CERTIFICATE: PASS {tested} graph cases, {len(mutation_cases)} negative controls")

if __name__=="__main__":run()
