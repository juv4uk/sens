#!/usr/bin/env python3
"""Exact rational squared Chamfer research oracle (HOLD, not a D10 opcode).

The real WSM-24 donor uses hypot (ordinary Euclidean distances).
This independent rational/squared-L2 variant deliberately DOES NOT claim
to reproduce that donor numerically or to execute native SENS .sens bytes.
"""
import copy
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOSSIER="knowledge/d10-wsm24-exact-chamfer-hobbies-v1.json"
INVENTORY="knowledge/d10-v1-semantic-inventory.json"
FOUNDATION="knowledge/d1-d9-foundation.json"
NAME="EXACT-SYMMETRIC-SQUARED-CHAMFER"
DONOR_BLOB="6a5b004f1fddaa763a94328ad0aa654053279faf"
TEST_BLOB="ab0765adffbb924735e567d35bb19d09bcf83eec"

class ProofFailure(Exception):
    pass

def require(ok, message):
    if not ok:
        raise ProofFailure(message)

def source(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def exact_cloud(cloud, dim=None):
    if not isinstance(cloud, (tuple,list)) or not cloud:
        raise ValueError("nonempty finite point cloud required")
    result=[]
    for point in cloud:
        if not isinstance(point,(tuple,list)) or not point:
            raise ValueError("point dimension must be positive")
        if dim is None:
            dim=len(point)
        if len(point)!=dim:
            raise ValueError("all points require exactly the same dimension")
        if any(isinstance(v,bool) or not isinstance(v,(int,Fraction)) for v in point):
            raise TypeError("coordinates must be exact integers or rationals")
        result.append(tuple(Fraction(v) for v in point))
    return tuple(result),dim

def squared(a,b):
    return sum(((x-y)*(x-y) for x,y in zip(a,b)),Fraction(0))

def directed(a,b):
    chosen=[];total=Fraction(0)
    for p in a:
        nearest,dist=0,squared(p,b[0])
        for i in range(1,len(b)):
            trial=squared(p,b[i])
            if trial<dist:  # strictly less: first-index tie
                dist,nearest=trial,i
        chosen.append(nearest)
        total+=dist
    return total/len(a),tuple(chosen)

def exact_chamfer(a,b):
    aa,d=exact_cloud(a);bb,_=exact_cloud(b,d)
    a_to_b,indices_ab=directed(aa,bb)
    b_to_a,indices_ba=directed(bb,aa)
    return (a_to_b+b_to_a)/2,indices_ab,indices_ba

def independent_matrix_oracle(a,b):
    aa,d=exact_cloud(a);bb,_=exact_cloud(b,d)
    # Independent all-pairs table, row and column minimization.
    matrix=[[sum((x-y)**2 for x,y in zip(p,q)) for q in bb] for p in aa]
    rowmin=[min(row) for row in matrix]
    colmin=[min(row[j] for row in matrix) for j in range(len(bb))]
    score=(sum(rowmin,Fraction(0))/len(aa)+sum(colmin,Fraction(0))/len(bb))/2
    ab=tuple(next(j for j,v in enumerate(row) if v==rowmin[i]) for i,row in enumerate(matrix))
    ba=tuple(next(i for i,row in enumerate(matrix) if row[j]==colmin[j]) for j in range(len(bb)))
    return score,ab,ba

def validate_metadata(dossier,inventory,foundation):
    require(dossier.get("schema")=="d10-wsm24-exact-chamfer-hobbies/v1","schema")
    require(dossier.get("status")=="PROPOSAL-HOLD-CORE-MATH-REVIEW","review status")
    origin=dossier["origin"]
    require(origin["implementation_git_blob_sha"]==DONOR_BLOB,"forged implementation source")
    require(origin["tests_git_blob_sha"]==TEST_BLOB,"forged donor tests")
    require("Euclidean hypot/sqrt" in origin["precise_donor_difference"],
            "Euclidean-to-squared variant warning erased")
    proposal=dossier["candidate"]
    require(proposal["semantic_name"]==NAME,"candidate name")
    require(proposal["selected_in_d10"] is False,"candidate illegally selected")
    require(proposal["coordinate"] is None and proposal["ratified_resident"] is False,
            "unapproved coordinate or ratification")
    require(proposal["epistemic_status"]=="RESEARCH-ONLY-HOLD","owner hold removed")
    require(len(proposal["positive_witnesses"])>=4 and len(proposal["falsifiers"])>=6,
            "witness/falsifier minimum")
    require("squared-L2" in proposal["behavior"],"squared versus Euclidean confused")
    require("likely implement" in proposal["minimality_attack"]["derivability"],
            "derivability review suppressed")
    require(dossier["outcome"]["new_d10_selected"]==0 and
            dossier["outcome"]["new_d10_coordinates"]==0 and
            dossier["outcome"]["new_d10_ratified"]==0,"false admission claim")
    selected={r["semantic_name"].upper() for r in inventory["rows"]}
    lower={str(name).upper() for d in foundation["domains"].values()
           for name in d["residents"].values()}
    require(NAME not in selected and NAME not in lower,"already selected name collision")
    require(inventory["accounting"]["ratified_d10_residents"]==0,"unexpected ratified D10")
    require(foundation["status"]=="owner-ratified","lower authority")
    return len(inventory["rows"])

def test_math():
    examples=[
       ([(0,),(2,)],[(0,)],(Fraction(1),(0,0),(0,))),
       ([(0,)], [(-1,),(1,)],(Fraction(1),(0,),(0,0))),
       ([(0,),(0,),(2,)],[(0,)],(Fraction(2,3),(0,0,0),(0,))),
       ([(0,0),(1,0)],[(0,0),(1,0)],(Fraction(0),(0,1),(0,1))),
    ]
    for a,b,wanted in examples:
        require(exact_chamfer(a,b)==wanted,"fixed point cloud witness mismatch")
    cases=[]
    for count in (1,2,3):
        for raw in itertools.product(range(-2,3),repeat=count):
            cases.append([(v,) for v in raw])
    total=0
    for a in cases:
        for b in cases:
            result=exact_chamfer(a,b)
            require(result==independent_matrix_oracle(a,b),
                    "independent matrix reference disagrees")
            require(result[0]==exact_chamfer(b,a)[0],
                    "symmetric score unequal")
            require(result[0]>=0,"negative squared nearest neighbor distance")
            total+=1
    require(total==24025,"exhaustive case census drift")
    a=[(Fraction(1,3),Fraction(1,2)),(2,0)]
    b=[(Fraction(1,3),Fraction(1,2)),(3,1)]
    require(exact_chamfer(a,b)==independent_matrix_oracle(a,b),"exact 2D fractions")
    shift=(Fraction(1,7),Fraction(-3,5))
    translated=lambda cloud:[(p[0]+shift[0],p[1]+shift[1]) for p in cloud]
    require(exact_chamfer(a,b)[0]==exact_chamfer(translated(a),translated(b))[0],
            "translation changed squared metric")
    rotation=lambda cloud:[(-p[1],p[0]) for p in cloud]
    require(exact_chamfer(a,b)[0]==exact_chamfer(rotation(a),rotation(b))[0],
            "90-degree orthogonal rotation changed score")
    require(exact_chamfer([(0,)],[(2,)])[0] >
            exact_chamfer([(0,)],[(1,)])[0] + exact_chamfer([(1,)],[(2,)])[0],
            "triangle-inequality anti-witness missing")
    for aa,bb,err in (([],[(0,)],ValueError), ([(0,)],[],ValueError),
                     ([(0,0)],[(0,)],ValueError), ([(0,),(1,2)],[(0,)],ValueError),
                     ([(0.0,)],[(0,)],TypeError), ([(True,)],[(0,)],TypeError)):
        try:
            exact_chamfer(aa,bb)
        except err:
            continue
        raise ProofFailure("invalid source input accepted")
    return total

def test_mutations(dossier,inventory,foundation):
    validate_metadata(dossier,inventory,foundation)
    experiments=[
       ("forged donor",lambda d:d["origin"].update({"implementation_git_blob_sha":"0"*40})),
       ("pretend donor matches squared",lambda d:d["origin"].update({"precise_donor_difference":"no difference"})),
       ("false selection",lambda d:d["candidate"].update({"selected_in_d10":True})),
       ("fake code",lambda d:d["candidate"].update({"coordinate":"1111111111"})),
       ("fake ratification",lambda d:d["candidate"].update({"ratified_resident":True})),
       ("erase counterexamples",lambda d:d["candidate"].update({"falsifiers":[]})),
       ("erase derivability",lambda d:d["candidate"]["minimality_attack"].update({"derivability":"OPAQUE"})),
       ("admit root",lambda d:d["outcome"].update({"new_d10_selected":1})),
    ]
    for label,change in experiments:
        mutated=copy.deepcopy(dossier)
        change(mutated)
        try:
            validate_metadata(mutated,inventory,foundation)
        except ProofFailure:
            continue
        raise ProofFailure("negative mutation accepted: "+label)
    return len(experiments)

if __name__=="__main__":
    dossier,inv,foundation=source(DOSSIER),source(INVENTORY),source(FOUNDATION)
    try:
        selected=validate_metadata(dossier,inv,foundation)
        cases=test_math()
        mutations=test_mutations(dossier,inv,foundation)
        print("D10-WSM24-CHAMFER PASS: exact differential="+str(cases)+
              " negative="+str(mutations)+"/8; current selected="+str(selected)+
              ", candidate HOLD, 0 code/ratification")
    except ProofFailure as exc:
        print("D10-WSM24-CHAMFER FAIL: "+str(exc),file=sys.stderr)
        sys.exit(1)
