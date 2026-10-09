#!/usr/bin/env python3
"""C1P semantics: independent exact permutation and prefix-automaton oracles.

Research-only. Not a PQ-tree implementation, runtime SENS execution or proof of
Panini's historical intent. Domain n here is bounded only by test workload.
"""
from functools import lru_cache
from itertools import combinations_with_replacement, permutations
import json
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"knowledge/d10-shiva-c1p-canonical-order-research-v1.json"
NAME="FINITE-C1P-CANONICAL-ORDER"
NO_SOLUTION="NO-SOLUTION"

class Failure(Exception):
    pass

def check(condition,message):
    if not condition:
        raise Failure(message)

def validate(n,rows):
    if type(n) is not int or n<0:
        raise ValueError("n must be natural integer")
    if type(rows) not in (list,tuple):
        raise TypeError("rows must be a finite sequence")
    if any(type(m) is not int or m<0 or m.bit_length()>n for m in rows):
        raise ValueError("row mask outside declared column width")

def holds(order,rows):
    for mask in rows:
        places=[i for i,col in enumerate(order) if mask & (1<<col)]
        if places and places[-1]-places[0]+1!=len(places):
            return False
    return True

def exhaustive_order(n,rows):
    validate(n,rows)
    for perm in permutations(range(n)):
        if holds(perm,rows):
            return list(perm)
    return NO_SOLUTION

def automaton_order(n,rows):
    """Different algorithm: subset DP over partial 0->1->2 row automata.

    0=not started, 1=inside run, 2=run closed. A one after 2 is forbidden.
    Sorted search returns lexicographically first feasible permutation.
    """
    validate(n,rows)
    rows=tuple(rows)
    full=(1<<n)-1
    @lru_cache(None)
    def search(used,states):
        if used==full:
            return ()
        for col in range(n):
            if used & (1<<col):
                continue
            nxt=[]
            valid=True
            for mask,old in zip(rows,states):
                bit=(mask>>col)&1
                if old==2 and bit:
                    valid=False
                    break
                nxt.append(1 if bit else (2 if old==1 else old))
            if not valid:
                continue
            suffix=search(used | (1<<col),tuple(nxt))
            if suffix is not None:
                return (col,)+suffix
        return None
    result=search(0,(0,)*len(rows))
    return list(result) if result is not None else NO_SOLUTION

def verify_metadata(source,inv,foundation):
    check(source["schema"]=="d10-finite-c1p-research/v1","schema drift")
    check(source["status"]=="HOLD-CORE-LIBRARY-REVIEW","HOLD bypass")
    check(source["identity"]==NAME,"identity drift")
    check(source["coordinate"] is None and source["ratified"] is False,"illegal coordinate or ratification")
    check(source["selected"] is False and source["physical_t5_authorized"] is False,"premature selected/T5")
    check(source["owner_review"]=="pending","owner review bypass")
    check(len(source["positive"])>=5 and len(source["falsifiers"])>=6,"insufficient witnesses")
    check(len(source["sources"])==3,"source inventory changed")
    checks={
      "docs/hakardvitva-c1p-topological-necessity.md":"bd7c3378c44c07e09ae7dbf33a2fc91bb7212ae9",
      "prototype/verify_hakardvitva_c1p.py":"87c33e5bb6b38807e4751f413f95491f33b6a93e",
      "docs/research-index.md":"d62a09b2872a505770c440755998aaefdbc7882d",
    }
    for repo,path,sha in source["sources"]:
        check(repo=="juv4uk/shiva-sutras" and checks.get(path)==sha,"source SHA/path mismatch")
    check("10.1016/S0022-0000(76)80045-1" in source["primary"][0],"primary research lost")
    low={str(s).upper() for d in foundation["domains"].values() for s in d["residents"].values()}
    check(NAME not in low,"collides with ratified D1-D9 name")
    check(all(r["semantic_name"].upper()!=NAME for r in inv["rows"]),"selected C1P already exists")
    check(inv["accounting"]["ratified_d10_residents"]==0,"D10 unreviewed ratification")
    check("lexicographically smallest" in source["behavior"],"canonical selection law lost")

def witness_tests(source):
    for witness in source["positive"]:
        n,rows,expected=witness["n"],witness["rows"],witness["expect"]
        check(exhaustive_order(n,rows)==expected,"brute witness failed "+str(witness))
        check(automaton_order(n,rows)==expected,"DP witness failed "+str(witness))
    for n,rows in ((-1,[]),(3,[8]),(2,[-1]),(2,[True]),(2,[1.5])):
        for fn in (automaton_order,exhaustive_order):
            try:
                fn(n,rows)
            except (ValueError,TypeError):
                pass
            else:
                raise Failure("invalid input accepted "+str((n,rows)))
    cases=0
    for n in range(6):
        maxrows=2 if n==5 else 3
        for nr in range(maxrows+1):
            for rows in combinations_with_replacement(range(1<<n),nr):
                a=exhaustive_order(n,rows)
                b=automaton_order(n,rows)
                check(a==b,"differential counterexample "+str((n,rows,a,b)))
                check(a==NO_SOLUTION or holds(a,rows),"bad feasible witness")
                cases+=1
    check(cases==1744,"exhaustive corpus size drift "+str(cases))
    rng=random.Random(0xC1C11976)
    for _ in range(512):
        rows=[rng.randrange(64) for _ in range(rng.randrange(7))]
        a=exhaustive_order(6,rows)
        b=automaton_order(6,rows)
        check(a==b,"randomized 6-column discrepancy")
        check(a==NO_SOLUTION or holds(a,rows),"random witness invalid")
        cases+=1
    return cases

def metadata_mutation_tests(source,inv,foundation):
    import copy
    mutation=[
      ("selected",lambda x:x.update({"selected":True})),
      ("coordinate",lambda x:x.update({"coordinate":"0000000000"})),
      ("ratified",lambda x:x.update({"ratified":True})),
      ("T5",lambda x:x.update({"physical_t5_authorized":True})),
      ("source SHA",lambda x:x["sources"][0].__setitem__(2,"0"*40)),
      ("source path",lambda x:x["sources"][1].__setitem__(1,"README.fake")),
      ("falsifier",lambda x:x.update({"falsifiers":[]})),
      ("owner",lambda x:x.update({"owner_review":"ratified"})),
      ("name",lambda x:x.update({"identity":"FAKE-ROOT"})),
      ("canonical tie",lambda x:x.update({"behavior":"Any order accepted"})),
    ]
    for name,change in mutation:
        clone=copy.deepcopy(source)
        change(clone)
        try:
            verify_metadata(clone,inv,foundation)
        except Failure:
            continue
        raise Failure("negative mutation admitted "+name)
    return len(mutation)

def main():
    source=json.loads(PATH.read_text(encoding="utf-8"))
    inv=json.loads((ROOT/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
    foundation=json.loads((ROOT/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
    verify_metadata(source,inv,foundation)
    total=witness_tests(source)
    rejected=metadata_mutation_tests(source,inv,foundation)
    print(f"D10-SHIVA-C1P: PASS independent-oracle cases={total}; negative mutations rejected={rejected}; selected=0; ratified=0; coordinate=null; likely derived library")

if __name__=="__main__":
    try:
        main()
    except Failure as err:
        print("D10-SHIVA-C1P: FAIL "+str(err),file=sys.stderr)
        sys.exit(1)
