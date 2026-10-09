#!/usr/bin/env python3
"""#4991 exact finite directed arc-consistency; no SENS coordinate or ratification."""
from __future__ import annotations
from collections import deque
from copy import deepcopy
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'knowledge/d10-ai-interest-proposal-v1.json'
NAME = 'FINITE-BINARY-ARC-CONSISTENCY-FIXPOINT'

def normalize(domains, arcs):
    if not isinstance(domains, dict) or len(domains) != len(set(domains)):
        raise ValueError('domain mapping required')
    names = tuple(sorted(domains))
    if any(not isinstance(n,str) or not n for n in names):
        raise ValueError('variable name must be non-empty string')
    D = {n: frozenset(domains[n]) for n in names}
    A=[]
    for src,dst,pairs in arcs:
        if src not in D or dst not in D:
            raise ValueError('undeclared variable on directed arc')
        relation=frozenset(tuple(pair) for pair in pairs)
        if any(len(pair)!=2 for pair in relation):
            raise ValueError('each allowed tuple must be binary')
        A.append((src,dst,relation))
    return D, tuple(A)

def queue_ac(domains, arcs):
    D,A=normalize(domains,arcs)
    D={k:set(v) for k,v in D.items()}
    pending=deque(range(len(A)))
    pending_set=set(pending)
    while pending:
        i=pending.popleft();pending_set.remove(i)
        src,dst,relation=A[i]
        removable={x for x in D[src] if not any((x,y) in relation for y in D[dst])}
        if removable:
            D[src].difference_update(removable)
            for j,(_,target,_) in enumerate(A):
                if target==src and j not in pending_set:
                    pending.append(j);pending_set.add(j)
    return tuple((k,tuple(sorted(D[k]))) for k in sorted(D))

def round_ac(domains, arcs):
    D,A=normalize(domains,arcs)
    while True:
        nxt={n:frozenset(x for x in D[n] if all(
            src!=n or any((x,y) in rel for y in D[dst])
            for src,dst,rel in A)) for n in D}
        if nxt==D:
            return tuple((k,tuple(sorted(nxt[k]))) for k in sorted(nxt))
        D=nxt

def ac_status(result):
    return 'EMPTY-DOMAIN-CONTRADICTION' if any(not values for _,values in result) else 'ARC-CONSISTENT'

def check_doc(doc):
    assert doc['schema']=='d10-ai-interest-proposal/v1'
    f=doc['owner_directive_4991']
    assert f['semantic_name']==NAME
    assert f['status']=='SELECTED-RESEARCH-CANDIDATE'
    assert f['coordinate'] is None and f['ratified_resident'] is False
    assert f['physical_t5_authorized'] is False
    assert f['primary_url']=='https://doi.org/10.1016/0004-3702(77)90007-8'
    assert f['surface_uk'] and f['surface_ukr']
    assert len(f['positive_witnesses'])>=5 and len(f['falsifiers'])>=5
    assert f['core_vs_library']=='PENDING-OWNER-REVIEW'
    assert len(doc['families'])==6 and doc['total_candidates']==38

def self_test():
    doc=json.loads(DOC.read_text())
    check_doc(doc)
    checks=0
    pairsets=[frozenset(p for j,p in enumerate(product((0,1),repeat=2)) if (mask>>j)&1)
              for mask in range(16)]
    subsets=[set(x for x in (0,1) if mask & (1<<x)) for mask in range(4)]
    for a,b,p,q in product(subsets,subsets,pairsets,pairsets):
        d={'A':a,'B':b}
        r=[('A','B',p),('B','A',q)]
        assert queue_ac(d,r)==round_ac(d,r), (d,r)
        checks+=1
    for a,b,c,p,q in product(subsets,subsets,subsets,pairsets,pairsets):
        d={'A':a,'B':b,'C':c}
        r=[('A','B',p),('B','C',q)]
        assert queue_ac(d,r)==round_ac(d,r), (d,r)
        checks+=1
    d={'A':{0,1},'B':{0,1}}
    forward=[('A','B',{(0,1)})]
    assert queue_ac(d,forward)==(('A',(0,)),('B',(0,1)))
    assert queue_ac(d,[('B','A',{(0,1)})])==(('A',(0,1)),('B',(0,)))
    assert queue_ac(d,forward+forward)==queue_ac(d,forward)
    assert queue_ac({'A':{0,1},'B':{0,1},'C':{1}},
        [('A','B',{(0,0),(1,1)}),('B','C',{(0,0),(1,1)})]) == (
        ('A',(1,)),('B',(1,)),('C',(1,)))
    ne={(0,1),(1,0)}
    odd=[('A','B',ne),('B','A',ne),('B','C',ne),('C','B',ne),('C','A',ne),('A','C',ne)]
    three={x:{0,1} for x in 'ABC'}
    assert queue_ac(three,odd)==tuple((x,(0,1)) for x in 'ABC')
    assert not any(all((assignment[s],assignment[t]) in rel for s,t,rel in odd)
                   for values in product((0,1),repeat=3)
                   for assignment in [dict(zip('ABC',values))])
    assert ac_status(queue_ac(three,odd))=='ARC-CONSISTENT'
    assert ac_status(queue_ac({'A':{0},'B':{1}},[('A','B',{(0,0)})]))=='EMPTY-DOMAIN-CONTRADICTION'
    assert ac_status(queue_ac({'A':set()},[]))=='EMPTY-DOMAIN-CONTRADICTION'
    source=deepcopy(three),deepcopy(odd)
    queue_ac(three,odd)
    assert three==source[0] and odd==source[1]
    for case in [lambda:queue_ac({'A':{0}},[('A','B',{(0,0)})]),
                 lambda:queue_ac({'A':{0}},[('A','A',{(1,)})])]:
        try:case()
        except ValueError:pass
        else:raise AssertionError('bad CSP admitted')
    mutants=[
        lambda x:x['owner_directive_4991'].update(coordinate='0'*10),
        lambda x:x['owner_directive_4991'].update(ratified_resident=True),
        lambda x:x['owner_directive_4991'].update(physical_t5_authorized=True),
        lambda x:x['owner_directive_4991'].update(status='RATIFIED'),
        lambda x:x['owner_directive_4991'].update(semantic_name='UNIFY'),
        lambda x:x['owner_directive_4991'].update(core_vs_library='APPROVED'),
        lambda x:x['owner_directive_4991'].update(primary_url='https://example.invalid/'),
        lambda x:x['owner_directive_4991'].update(positive_witnesses=[]),
        lambda x:x['owner_directive_4991'].update(falsifiers=[]),
        lambda x:x.update(total_candidates=39),
    ]
    for i, mutate in enumerate(mutants):
        shadow=deepcopy(doc);mutate(shadow)
        try:check_doc(shadow)
        except AssertionError:continue
        raise AssertionError(f'negative mutation {i} survived')
    print(f'D10 #4991 PASS Python queue-vs-round cases={checks}, 10 mutants rejected, 0 coords, 0 ratified')

if __name__=='__main__':
    self_test()
