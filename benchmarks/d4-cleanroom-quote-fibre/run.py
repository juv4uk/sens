#!/usr/bin/env python3
"""#3238 clean-room QUOTE fibre falsifier.

Parent D3:001 preserves represented semantics without entering it.

Posted pair hypothesis:
- child A: construct a late-bound executable wrapper from represented semantics;
- child B: enter/evaluate represented semantics.

#3244 requires both children to share one generator law and recover the parent
when the new factor is forgotten. This witness tests that requirement directly.
"""

from __future__ import annotations
import argparse, csv, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

YES=1

@dataclass(frozen=True)
class Atom:
    name:str

@dataclass(frozen=True)
class Form:
    op:str
    args:tuple[Any,...]=()

@dataclass(frozen=True)
class Represented:
    form:Form

@dataclass(frozen=True)
class LateBehavior:
    represented:Represented

@dataclass(frozen=True)
class EnteredWithProvenance:
    represented:Represented
    result:Any

def quote(form:Form)->Represented:
    return Represented(form)

def eval_form(form:Form,arg:Any)->Any:
    if form.op=="ARG":
        return arg
    if form.op=="CONST":
        return form.args[0]
    if form.op=="COND":
        pred,yes,no=form.args
        bit=eval_form(pred,arg)
        return eval_form(yes if bit==YES else no,arg)
    raise ValueError(form.op)

def abstract(represented:Represented)->LateBehavior:
    return LateBehavior(represented)

def invoke(behavior:LateBehavior,arg:Any)->Any:
    return eval_form(behavior.represented.form,arg)

def enter_result_only(represented:Represented,arg:Any)->Any:
    return eval_form(represented.form,arg)

def enter_with_provenance(represented:Represented,arg:Any)->EnteredWithProvenance:
    return EnteredWithProvenance(represented,eval_form(represented.form,arg))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)

    same=Atom("same")
    other=Atom("other")
    arg=Atom("future")

    f1=Form("CONST",(same,))
    f2=Form("COND",(Form("CONST",(YES,)),Form("CONST",(same,)),Form("CONST",(other,))))
    q1,q2=quote(f1),quote(f2)
    assert q1!=q2

    r1=enter_result_only(q1,arg)
    r2=enter_result_only(q2,arg)
    assert r1==r2==same

    parameterized=quote(Form("ARG"))
    behavior=abstract(parameterized)
    assert behavior.represented==parameterized
    assert invoke(behavior,Atom("a"))==Atom("a")
    assert invoke(behavior,Atom("b"))==Atom("b")

    collision={
        "parent_a":repr(q1.form),
        "parent_b":repr(q2.form),
        "child_result":repr(r1),
        "parents_distinct":q1!=q2,
        "children_equal":r1==r2,
    }
    assert collision["parents_distinct"] and collision["children_equal"]

    p1=enter_with_provenance(q1,arg)
    p2=enter_with_provenance(q2,arg)
    assert p1.represented==q1
    assert p2.represented==q2
    assert p1!=p2

    rows=[
        {
            "candidate":"late-bound-wrapper",
            "parent_recoverable":True,
            "posted_hypothesis_status":"PASS-PARENT-RECOVERY",
        },
        {
            "candidate":"result-only-stage-entry",
            "parent_recoverable":False,
            "posted_hypothesis_status":"REFUTED-PARENT-RECOVERY",
        },
        {
            "candidate":"provenance-carrying-entry-control",
            "parent_recoverable":True,
            "posted_hypothesis_status":"SEPARATE-CAPABILITY-NOT-ADMITTED",
        },
    ]
    with (args.out/"fibre.tsv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys()),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    result={
        "schema":"d4-cleanroom-quote-fibre/v1",
        "authority":"research-only",
        "parent":{"bits":"001","semantic":"preserve represented semantics without stage entry"},
        "posted_pair_hypothesis":{
            "child0":"late-bound executable wrapper",
            "child1":"result-only stage entry",
            "status":"REFUTED-AS-COMPLETE-FIBRE",
            "reason":"child1 erases parent representation; distinct represented forms can enter to the same result",
        },
        "collision_falsifier":collision,
        "child0_parent_recovery":True,
        "child1_parent_recovery":False,
        "alternate_control":{
            "capability":"provenance-carrying stage entry",
            "parent_recovery":True,
            "status":"changed-capability-requires-separate-review",
        },
        "candidate_coordinates_earned":[],
        "unresolved_coordinates":["0010","0011"],
        "historical_post_d3_seed_rows":0,
        "non_conclusions":[
            "late-bound executable construction remains independently proved",
            "result-only stage entry may be useful but fails this fibre parent-recovery law",
            "provenance-carrying entry is not silently substituted for the posted child",
        ],
    }
    (args.out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report="""# D4 clean-room QUOTE fibre falsifier — #3238

Parent D3:001 preserves represented semantics without entering it.

Posted pair result:
- late-bound wrapper: parent recovery PASS;
- result-only stage entry: parent recovery FAIL.

Decisive collision:
two distinct represented forms evaluate to the same result. Therefore a
result-only stage-entry child cannot recover which QUOTE parent representation
it came from. This is structural non-injectivity, not an implementation omission.

A provenance-carrying entry control can recover the source, but it is a changed
capability/output object and is NOT silently admitted as the posted child.

Fibre status: **REFUTED-AS-COMPLETE-FIBRE** for the posted hypothesis.
Coordinates 0010/0011 earned: **none**.
Historical post-D3 seed rows: **0**.
"""
    (args.out/"report.md").write_text(report,encoding="utf-8")
    print(report)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
