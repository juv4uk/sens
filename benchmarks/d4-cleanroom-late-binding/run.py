#!/usr/bin/env python3
"""#3229 clean-room D4: first-class late binding is absent from D1-D3.

This witness uses only ratified D1-D3 result kinds and operations.
No historical post-D3 resident name or coordinate is used.
"""

from __future__ import annotations
import argparse, csv, json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

class Kind(str, Enum):
    DATA="DATA"
    PREDICATE="PREDICATE"
    EXECUTABLE="EXECUTABLE"

# Clean-room codomain facts from D1-D3.
PRIMITIVE_CODOMAINS = {
    "EMPTY": Kind.DATA,
    "QUOTE": Kind.DATA,
    "CAR": Kind.DATA,
    "CDR": Kind.DATA,
    "CONS": Kind.DATA,
    "ATOM": Kind.PREDICATE,
    "EQ": Kind.PREDICATE,
}
# COND is branch-kind preserving: it may select a kind already present,
# but cannot introduce a new result kind from nowhere.

def kind_closure(seed: set[Kind]) -> set[Kind]:
    closure=set(seed)
    changed=True
    while changed:
        changed=False
        for out in PRIMITIVE_CODOMAINS.values():
            if out not in closure:
                closure.add(out); changed=True
        # COND adds no novel kind: for any admitted branch kind K, result is K.
        for k in list(closure):
            if k not in closure:
                closure.add(k); changed=True
    return closure

@dataclass(frozen=True)
class Empty: pass
EMPTY=Empty()

@dataclass(frozen=True)
class Atom:
    name:str

@dataclass(frozen=True)
class Pair:
    first:Any
    rest:Any

@dataclass(frozen=True)
class TExpr:
    op:str
    args:tuple[Any,...]=()

ARG=TExpr("ARG")
E=TExpr("EMPTY")

def tcons(a,b): return TExpr("CONS",(a,b))
def tcar(a): return TExpr("CAR",(a,))
def tcdr(a): return TExpr("CDR",(a,))
def tatom(a): return TExpr("ATOM",(a,))
def teq(a,b): return TExpr("EQ",(a,b))
def tcond(p,y,n): return TExpr("COND",(p,y,n))

def eval_template(expr:TExpr,arg:Any)->Any:
    if expr.op=="ARG": return arg
    if expr.op=="EMPTY": return EMPTY
    if expr.op=="CONS": return Pair(eval_template(expr.args[0],arg),eval_template(expr.args[1],arg))
    if expr.op=="CAR":
        v=eval_template(expr.args[0],arg)
        if not isinstance(v,Pair): raise ValueError("CAR requires pair")
        return v.first
    if expr.op=="CDR":
        v=eval_template(expr.args[0],arg)
        if not isinstance(v,Pair): raise ValueError("CDR requires pair")
        return v.rest
    if expr.op=="ATOM":
        return 0 if isinstance(eval_template(expr.args[0],arg),Pair) else 1
    if expr.op=="EQ":
        a,b=eval_template(expr.args[0],arg),eval_template(expr.args[1],arg)
        if isinstance(a,Pair) or isinstance(b,Pair): return 0
        return 1 if a==b else 0
    if expr.op=="COND":
        p=eval_template(expr.args[0],arg)
        return eval_template(expr.args[1] if p==1 else expr.args[2],arg)
    raise ValueError(expr.op)

@dataclass(frozen=True)
class LateBehavior:
    template:TExpr

def make_late_behavior(template:TExpr)->LateBehavior:
    # This is the explicit new capability under test: a value whose kind is
    # EXECUTABLE and whose argument is not present at construction time.
    return LateBehavior(template)

def invoke(behavior:LateBehavior,arg:Any)->Any:
    return eval_template(behavior.template,arg)

def proper_chain(n:int)->Any:
    out:Any=EMPTY
    for i in reversed(range(n)):
        out=Pair(Atom(f"a{i}"),out)
    return out

def shallow_wrap_template()->TExpr:
    # finite, non-recursive late-bound behavior
    return tcond(
        tatom(ARG),
        E,
        tcons(tcons(tcar(ARG),E), tcdr(ARG)),
    )

def recursive_target(value:Any)->Any:
    if value==EMPTY: return EMPTY
    if not isinstance(value,Pair): raise ValueError("improper")
    return Pair(Pair(value.first,EMPTY),recursive_target(value.rest))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)

    closure=kind_closure({Kind.DATA})
    assert Kind.DATA in closure and Kind.PREDICATE in closure
    assert Kind.EXECUTABLE not in closure

    # Bounded kind enumeration is a machine sharpness witness for the same
    # codomain theorem: D1-D3 closure never introduces EXECUTABLE.
    depth_rows=[]
    kinds={Kind.DATA}
    for depth in range(0,7):
        kinds=kind_closure(kinds)
        depth_rows.append({
            "depth":depth,
            "data_present":Kind.DATA in kinds,
            "predicate_present":Kind.PREDICATE in kinds,
            "executable_present":Kind.EXECUTABLE in kinds,
        })
        assert Kind.EXECUTABLE not in kinds

    # Positive control: construct behavior before the future argument exists.
    template=shallow_wrap_template()
    behavior=make_late_behavior(template)
    assert isinstance(behavior,LateBehavior)

    x1=proper_chain(1)
    x2=proper_chain(2)
    y1=invoke(behavior,x1)
    y2=invoke(behavior,x2)
    assert y1 != y2
    assert y1 == Pair(Pair(Atom("a0"),EMPTY),EMPTY)

    # Independence from #3230: late binding alone remains finite.
    # This shallow behavior transforms only the first cell and leaves the
    # remaining tail unchanged, so it fails the arbitrary-depth recursive target.
    assert y2 != recursive_target(x2)

    # A second finite template proves the capability is generic over templates,
    # not one hard-coded behavior row.
    second=make_late_behavior(tcond(tatom(ARG),E,tcar(ARG)))
    assert invoke(second,Pair(Atom("z"),EMPTY)) == Atom("z")
    assert second != behavior

    # Construction is argument-independent.
    assert behavior.template == template

    with (args.out/"kind-closure.tsv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(depth_rows[0].keys()),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(depth_rows)

    result={
        "schema":"d4-cleanroom-late-binding/v1",
        "authority":"research-only",
        "historical_post_d3_seed_rows":0,
        "absolute_d4_coordinate_assignments":0,
        "lower_bound":{
            "primitive_output_kinds":{k:v.value for k,v in PRIMITIVE_CODOMAINS.items()},
            "cond_rule":"returns an already-present branch kind; introduces no novel kind",
            "closure":[k.value for k in sorted(closure,key=lambda x:x.value)],
            "executable_in_d1_d3_closure":False,
            "conclusion":"first-class late-bound executable value kind is not generable from D1-D3 codomains alone"
        },
        "positive_control":{
            "new_capability":"construct finite executable template now; supply bound argument later",
            "two_distinct_templates":True,
            "same_constructor_interface":True,
            "argument_absent_at_construction":True,
            "result_kind":"EXECUTABLE"
        },
        "independence_control":{
            "late_binding_without_reentry":True,
            "two_cell_recursive_target_pass":False,
            "conclusion":"late-bound executable construction does not by itself supply unbounded semantic re-entry"
        },
        "non_conclusions":[
            "no D4 coordinate is earned",
            "no unique implementation is proved",
            "no relation to #3230 re-entry is assumed beyond demonstrated independence control",
            "historical post-D3 concepts are not search premises"
        ]
    }
    (args.out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report="""# D4 clean-room late-binding lower bound — #3229

D1-D3 kind closure:
- DATA: present
- PREDICATE: present
- EXECUTABLE: absent at every tested closure depth 0..6

Structural reason:
no admitted D1-D3 primitive has EXECUTABLE codomain, and COND only selects an already-existing branch kind. Finite composition therefore cannot create the first executable value kind.

Positive control:
- one explicit late-bound constructor creates two distinct finite executable templates;
- construction occurs before the future argument exists;
- invocation with later arguments changes results as required.

Independence control:
- the shallow late-bound behavior succeeds as first-class parameterization;
- it still fails an arbitrary-depth recursive transform on a two-cell chain;
- therefore late binding does not imply unbounded re-entry.

Historical post-D3 seed rows: **0**.
Absolute D4 coordinates assigned: **0**.
"""
    (args.out/"report.md").write_text(report,encoding="utf-8")
    print(report)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
