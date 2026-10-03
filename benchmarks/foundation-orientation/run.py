#!/usr/bin/env python3
"""#2566 D1/D2 orientation automorphism witness. Research only."""
import argparse, csv, itertools, json
from pathlib import Path

D1_ROLES=("NO","YES"); D1_CODES=("0","1")
D2_ROLES=("SEP","OPEN","CLOSE","DOT"); D2_CODES=("00","01","10","11")
CURRENT_D1={"NO":"0","YES":"1"}
CURRENT_D2={"SEP":"00","CLOSE":"01","OPEN":"10","DOT":"11"}

def inv(m): return {v:k for k,v in m.items()}

def d1_trace(m):
    dec=inv(m)
    cases=(("ATOM-empty","YES"),("ATOM-atom","YES"),("ATOM-pair","NO"),
           ("EQ-same","YES"),("EQ-distinct","NO"))
    return tuple((name, dec[m[role]], "SELECT" if dec[m[role]]=="YES" else "SKIP")
                 for name,role in cases)

def d1_frozen_flip_breaks():
    dec=inv(CURRENT_D1)
    flip={"0":"1","1":"0"}
    for _,role in (("a","YES"),("b","NO")):
        consumed=dec[flip[CURRENT_D1[role]]]
        if consumed != role: return True
    return False

def valid_roles(seq):
    depth=0; dotted=set()
    for role in seq:
        if role=="OPEN": depth+=1
        elif role=="CLOSE":
            if depth<=0: return False
            depth-=1; dotted={d for d in dotted if d<=depth}
        elif role=="SEP": pass
        elif role=="DOT":
            if depth<=0 or depth in dotted: return False
            dotted.add(depth)
        else: raise ValueError(role)
    return depth==0

FIXTURES=(
 ("empty",("OPEN","CLOSE"),True),
 ("nested",("OPEN","OPEN","CLOSE","CLOSE"),True),
 ("separated",("OPEN","CLOSE","SEP","OPEN","CLOSE"),True),
 ("improper",("OPEN","DOT","CLOSE"),True),
 ("underflow",("CLOSE","OPEN"),False),
 ("unclosed",("OPEN","OPEN","CLOSE"),False),
)

def d2_trace(m):
    dec=inv(m); out=[]
    for name,roles,expected in FIXTURES:
        encoded=tuple(m[r] for r in roles)
        actual=valid_roles(tuple(dec[c] for c in encoded))
        assert actual==expected
        out.append((name,actual))
    return tuple(out)

def comp(code): return "".join("1" if b=="0" else "0" for b in code)
def complement_hypothesis(m):
    return comp(m["OPEN"])==m["CLOSE"] and comp(m["SEP"])==m["DOT"]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)

    ref1=d1_trace(CURRENT_D1); d1=[]
    for p in itertools.permutations(D1_CODES):
        m=dict(zip(D1_ROLES,p))
        d1.append({"no":m["NO"],"yes":m["YES"],
                   "semantic_equal":d1_trace(m)==ref1,
                   "current":m==CURRENT_D1})
    assert len(d1)==2 and all(x["semantic_equal"] for x in d1)
    assert d1_frozen_flip_breaks()

    ref2=d2_trace(CURRENT_D2); d2=[]
    for p in itertools.permutations(D2_CODES):
        m=dict(zip(D2_ROLES,p))
        d2.append({"sep":m["SEP"],"open":m["OPEN"],"close":m["CLOSE"],"dot":m["DOT"],
                   "semantic_equal":d2_trace(m)==ref2,
                   "complement_geometry":complement_hypothesis(m),
                   "current":m==CURRENT_D2})
    assert len(d2)==24 and all(x["semantic_equal"] for x in d2)
    assert sum(x["complement_geometry"] for x in d2)==8

    result={
      "schema":"foundation-orientation-closeout/v1","authority":"research-only",
      "production_change":False,"consumes":["#2106","#1699","#1702","#2151"],
      "d1":{"tested":2,"surviving":2,"bits_only_flip_breaks_frozen_consumer":True,
            "independent_orienting_law_found":False,
            "classification":"EQUIVALENT-UP-TO-C2"},
      "d2":{"tested":24,"surviving_full_semantic_relations":24,
            "classification":"EQUIVALENCE-CLASS-OF-24",
            "relations":{"dual":["OPEN","CLOSE"],"separator":"SEP",
                         "improper_pair_marker":"DOT","fixtures":[x[0] for x in FIXTURES]},
            "rejected_coordinate_hypothesis":{"law":"semantic duals are bitwise complements",
                                               "survivors":8,
                                               "status":"NOT-INDEPENDENTLY-ADMITTED"}},
      "handoff":{"origin":"SENS-PREMISE","authority":"SENS-RATIFIED",
                 "refs":["#2562","#2556"]},
      "non_conclusions":["production assignments remain ratified",
                         "surviving coordinate automorphisms do not merge semantic roles",
                         "hard-coded current bits are not an independent derivation"]
    }
    (a.out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")

    for name,rows in (("d1-bijections.tsv",d1),("d2-bijections.tsv",d2)):
        with (a.out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t",lineterminator="\n")
            w.writeheader(); w.writerows(rows)

    report=f"""# D1/D2 orientation closeout — #2566

Production assignments remain unchanged.

- D1 coherent semantic relabelings surviving: **2/2**
- D1 bits-only flip with frozen consumer: **breaks**, as expected
- **D1-ORIENTATION = EQUIVALENT-UP-TO-C2**

- D2 role-to-code bijections tested: **24**
- D2 bijections surviving role-level grammar controls: **24/24**
- rejected complement-geometry hypothesis would leave **8/24**
- **D2-PLACEMENT = EQUIVALENCE-CLASS-OF-24**

No independent admitted orienting law was found in this bounded relation set.
Current orientations therefore remain ratified SENS premises, not internally
derived coordinate theorems, within this scope.
"""
    (a.out/"report.md").write_text(report)
    print(report)

if __name__=="__main__": main()
