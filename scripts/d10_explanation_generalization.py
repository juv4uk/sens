#!/usr/bin/env python3
"""Finite acyclic Horn proof-to-operational-clause projection; research, not SENS runtime."""
from __future__ import annotations
import json
from pathlib import Path

class Refusal(ValueError):
    """Explicit refusal, never inferred admission."""

def atom(x):
    if not isinstance(x, (list, tuple)) or len(x) < 2 or not all(isinstance(v, str) and v for v in x):
        raise Refusal('atom must be a nonempty predicate and at least one string argument')
    if x[0].startswith('?'):
        raise Refusal('variable predicate forbidden')
    return tuple(x)

def isvar(s):
    return s.startswith('?')

def project(goal, rules, operational):
    """Return sufficient operational leaves and rule provenance for ONE explicit Horn path.

    No guarantee of minimality/independence; never executes inferred control.
    A non-operational predicate needs exactly one source rule. Recursion refuses.
    """
    g=atom(goal)
    if not isinstance(rules, list) or not isinstance(operational, (list,set,tuple)):
        raise Refusal('invalid program shape')
    ops=set(operational)
    if not ops or any(not isinstance(s,str) or not s or s.startswith('?') for s in ops):
        raise Refusal('invalid operational predicate set')
    lookup={}
    ids=set()
    for rule in rules:
        if not isinstance(rule,dict) or not isinstance(rule.get('id'),str) or not rule['id'] or rule['id'] in ids:
            raise Refusal('rule id missing/duplicate')
        ids.add(rule['id'])
        head=atom(rule.get('head'))
        body=rule.get('body')
        if not isinstance(body,list) or not body:
            raise Refusal('nonempty conjunctive body required')
        body=[atom(x) for x in body]
        lookup.setdefault((head[0],len(head)),[]).append((rule['id'],head,body))
    counter=[0]
    provenance=[]
    leaves=[]
    def expand(target,stack):
        pred=target[0]
        if pred in ops:
            leaves.append(target)
            return
        key=(pred,len(target))
        matches=lookup.get(key,[])
        if len(matches)!=1:
            raise Refusal('missing or ambiguous rule: '+pred)
        if key in stack:
            raise Refusal('recursive proof / cycle: '+pred)
        rid,head,body=matches[0]
        binding={}
        for h,t in zip(head[1:],target[1:]):
            if isvar(h):
                if h in binding and binding[h] != t:
                    raise Refusal('repeated head variable conflicts')
                binding[h]=t
            elif h!=t:
                raise Refusal('head constant conflicts')
        scope=counter[0]
        counter[0]+=1
        def inst(v):
            if not isvar(v):
                return v
            if v not in binding:
                binding[v]='?e'+str(scope)+'_'+str(len(binding))
            return binding[v]
        provenance.append(rid)
        for b in body:
            expand((b[0],*(inst(v) for v in b[1:])),stack|{key})
    expand(g,set())
    return {'conclusion': list(g), 'operational_body': [list(t) for t in leaves],
            'proof_rule_ids': provenance, 'status': 'RESEARCH-HOLD-NOT-RATIFIED'}

def audit_d10(repository_root:Path, name='PROOF-OPERATIONAL-CLAUSE-PROJECTION'):
    """Only verify exact-name collision; cannot establish semantic independence."""
    inv=json.loads((repository_root/'knowledge/d10-v1-semantic-inventory.json').read_text())
    low=json.loads((repository_root/'knowledge/d1-d9-foundation.json').read_text())
    selected={r['semantic_name'].upper() for r in inv['rows']}
    lower={str(x).upper() for d in low['domains'].values() for x in d['residents'].values()}
    if name in selected or name in lower:
        raise Refusal('exact name already registered')
    if inv['accounting']['ratified_d10_residents'] != 0:
        raise Refusal('ratification baseline drift; owner review required')
    return {'main_selected':len(selected),'exact_name_free':True,'semantic_dedup':'NOT_PROVED'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--repository-root',type=Path)
    a=p.parse_args()
    if a.repository_root:
        print(json.dumps(audit_d10(a.repository_root),sort_keys=True))
    else:
        print(json.dumps(project(['grandparent','?x','?z'],[
            {'id':'R1','head':['grandparent','?a','?c'], 'body':[['parent','?a','?b'],['parent','?b','?c']]}],['parent']),sort_keys=True))
