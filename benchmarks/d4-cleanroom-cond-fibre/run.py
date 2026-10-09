#!/usr/bin/env python3
"""#3241 clean-room D4 fibre under ratified D3 COND=110.

Candidate family law:
  lift_cond(parent_cond, mode_bit)

The mode bit is interpreted LOCALLY as a ratified D1 predicate:
  0 = re-entry permission NO
  1 = re-entry permission YES

Both children preserve the parent invariant: exactly one branch is selected.
No historical post-D3 resident name/table is used.
"""

from __future__ import annotations
import argparse, csv, json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

NO=0
YES=1

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

class SemanticError(RuntimeError): pass

def atom_p(v:Any)->int:
    return NO if isinstance(v,Pair) else YES

def car(v:Any)->Any:
    if not isinstance(v,Pair): raise SemanticError("first projection requires pair")
    return v.first

def cdr(v:Any)->Any:
    if not isinstance(v,Pair): raise SemanticError("rest projection requires pair")
    return v.rest

def cons(a:Any,d:Any)->Pair:
    return Pair(a,d)

def cond_select(pred:int, yes_branch:Any, no_branch:Any)->Any:
    return yes_branch if pred==YES else no_branch

@dataclass
class Stats:
    entries:int=0
    yes_selected:int=0
    no_selected:int=0
    reentries:int=0
    trace:list[str]=field(default_factory=list)

Behavior=Callable[[Any, Callable[[Any],Any] | None], Any]
Predicate=Callable[[Any],int]

def lift_cond(
    mode_bit:int,
    predicate:Predicate,
    yes_behavior:Behavior,
    no_behavior:Behavior,
    value:Any,
    *,
    fuel:int,
    stats:Stats,
)->Any:
    if mode_bit not in (NO,YES):
        raise SemanticError("mode must be exact D1 predicate bit")
    if fuel<=0:
        raise SemanticError("fuel exhausted")

    stats.entries+=1
    pred=predicate(value)
    branch=cond_select(pred,yes_behavior,no_behavior)
    if pred==YES:
        stats.yes_selected+=1
        stats.trace.append("Y")
    else:
        stats.no_selected+=1
        stats.trace.append("N")

    again=None
    if mode_bit==YES:
        def again(subvalue:Any)->Any:
            stats.reentries+=1
            return lift_cond(
                YES,predicate,yes_behavior,no_behavior,subvalue,
                fuel=fuel-1,stats=stats
            )

    return branch(value,again)

def proper_chain(n:int)->Any:
    out:Any=EMPTY
    for i in reversed(range(n)):
        out=Pair(Atom(f"a{i}"),out)
    return out

def target_wrap(v:Any)->Any:
    if v==EMPTY: return EMPTY
    if not isinstance(v,Pair): raise SemanticError("improper chain")
    return Pair(Pair(v.first,EMPTY),target_wrap(v.rest))

def base_behavior(v:Any, again)->Any:
    if v!=EMPTY: raise SemanticError("non-empty atom in proper-chain control")
    return EMPTY

def step_behavior(v:Any, again)->Any:
    if not isinstance(v,Pair): raise SemanticError("step requires pair")
    wrapped=cons(car(v),EMPTY)
    if again is None:
        # finite one-entry behavior: preserve remaining tail unchanged
        return cons(wrapped,cdr(v))
    return cons(wrapped,again(cdr(v)))

def plain_parent_trace(predicate:Predicate, values:list[Any])->list[str]:
    return ["Y" if predicate(v)==YES else "N" for v in values]

def trace_inputs_chain(v:Any)->list[Any]:
    out=[]
    cur=v
    while True:
        out.append(cur)
        if cur==EMPTY: return out
        if not isinstance(cur,Pair): raise SemanticError("improper")
        cur=cur.rest

def mutant_both_branches(predicate,yes_behavior,no_behavior,value):
    # Deliberate falsifier: selection result is ignored and both effects run.
    pred=predicate(value)
    _selected=cond_select(pred,yes_behavior,no_behavior)
    calls=[]
    for label,branch in (("Y",yes_behavior),("N",no_behavior)):
        try:
            branch(value,None)
        except SemanticError:
            pass
        calls.append(label)
    return calls

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--deep-length",type=int,default=256)
    args=ap.parse_args()
    if args.deep_length<3: ap.error("--deep-length must be >=3")
    args.out.mkdir(parents=True,exist_ok=True)

    # Child 0: finite executable dispatch, no re-entry.
    one=proper_chain(1)
    two=proper_chain(2)
    s0=Stats()
    out0=lift_cond(NO,atom_p,base_behavior,step_behavior,two,fuel=8,stats=s0)
    assert s0.entries==1 and s0.reentries==0
    assert s0.yes_selected+s0.no_selected==s0.entries
    assert out0!=target_wrap(two)
    # On one cell, one entry is sufficient and should match.
    s0_one=Stats()
    assert lift_cond(NO,atom_p,base_behavior,step_behavior,one,fuel=8,stats=s0_one)==target_wrap(one)

    # Child 1: same branch law plus explicit re-entry permission YES.
    deep=proper_chain(args.deep_length)
    s1=Stats()
    out1=lift_cond(YES,atom_p,base_behavior,step_behavior,deep,fuel=args.deep_length+2,stats=s1)
    assert out1==target_wrap(deep)
    assert s1.reentries==args.deep_length
    assert s1.yes_selected+s1.no_selected==s1.entries

    # Parent recovery: at every entry, forget invocation/re-entry mechanics and
    # recover exactly the D3 COND branch choice.
    expected=plain_parent_trace(atom_p,trace_inputs_chain(deep))
    assert s1.trace==expected
    assert s0.trace==plain_parent_trace(atom_p,[two])

    # D1 orientation is local and explicit: mode bit answers a predicate
    # "re-entry permitted?". Reversing the bit semantics breaks the controls.
    reversed0=Stats()
    reversed0_out=lift_cond(YES,atom_p,base_behavior,step_behavior,two,fuel=8,stats=reversed0)
    assert reversed0_out==target_wrap(two)  # would violate suffix-0 finite control

    reversed1=Stats()
    reversed1_out=lift_cond(NO,atom_p,base_behavior,step_behavior,two,fuel=8,stats=reversed1)
    assert reversed1_out!=target_wrap(two)  # would violate suffix-1 re-entry control

    # Parent-invariant falsifier: a mechanism invoking both branches is not a
    # refinement of COND because one-entry one-branch selection is lost.
    both=mutant_both_branches(atom_p,base_behavior,step_behavior,two)
    assert both==["Y","N"]

    # Malformed mode and insufficient fuel fail closed.
    controls=[]
    for name,fn in [
        ("malformed-mode",lambda: lift_cond(2,atom_p,base_behavior,step_behavior,one,fuel=8,stats=Stats())),
        ("insufficient-fuel",lambda: lift_cond(YES,atom_p,base_behavior,step_behavior,deep,fuel=2,stats=Stats())),
    ]:
        try:
            fn()
        except SemanticError as exc:
            controls.append({"control":name,"status":"FAIL-CLOSED","reason":str(exc)})
        else:
            raise AssertionError(name)

    rows=[
        {
            "suffix_bit":"0",
            "local_d1_meaning":"re-entry-permitted? NO",
            "parent_invariant":"exactly one COND branch selected",
            "new_delta":"invoke selected executable once; no self re-entry",
            "deep_recursive_target":False,
            "coordinate":"1100",
            "coordinate_earned":True,
        },
        {
            "suffix_bit":"1",
            "local_d1_meaning":"re-entry-permitted? YES",
            "parent_invariant":"exactly one COND branch selected at every entry",
            "new_delta":"selected behavior may re-enter same lifted control on smaller input",
            "deep_recursive_target":True,
            "coordinate":"1101",
            "coordinate_earned":True,
        },
    ]
    with (args.out/"fibre.tsv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys()),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    result={
        "schema":"d4-cleanroom-cond-fibre/v1",
        "authority":"research-only",
        "parent":{"bits":"110","semantic":"exact one-branch conditional selection"},
        "generator":{
            "equation":"C_b(p,y,n,x)=invoke(select_COND(p(x),y,n),x,reentry=C_1 iff b=1)",
            "bit_domain":"D1 PredicateBit",
            "bit_question":"re-entry permitted?",
            "bit0":"NO",
            "bit1":"YES",
            "parent_recovery":"erase invocation/re-entry layer and retain selected branch trace",
        },
        "children":rows,
        "witness":{
            "suffix0_single_cell_pass":True,
            "suffix0_two_cell_recursive_target":False,
            "suffix1_deep_length":args.deep_length,
            "suffix1_deep_target_pass":True,
            "suffix1_parent_trace_matches":True,
        },
        "falsifiers":{
            "invoke_both_branches_rejected":True,
            "reverse_bit_orientation_breaks_controls":True,
            "malformed_and_fuel_controls":controls,
        },
        "historical_post_d3_seed_rows":0,
        "non_conclusions":[
            "this fibre law does not determine any other D4 fibre",
            "the executable behavior carrier has independent clean-room evidence but separate placement",
            "posterior historical name comparison is outside this witness",
        ],
    }
    (args.out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=f"""# D4 clean-room COND fibre — #3241

Parent: D3:110, exact one-branch conditional selection.

Local generator bit is an explicit D1 PredicateBit answering:
**re-entry permitted?**

- suffix 0 / D1 NO: one selected executable behavior is invoked once; no re-entry.
- suffix 1 / D1 YES: the same branch-selection law is preserved, and the selected behavior may re-enter on smaller input.

Controls:
- suffix 0 matches the recursive target on a one-cell chain but fails on two cells.
- suffix 1 passes the recursive target at depth {args.deep_length}.
- every entry selects exactly one branch.
- erasing execution mechanics recovers the exact parent COND branch trace.
- a mutant that invokes both branches is rejected.
- reversing the 0/1 semantic orientation breaks the required finite/re-entry controls.
- malformed mode and insufficient fuel fail closed.

Result:
the two-child generator law earns the fibre coordinates **1100** and **1101**
for these clean-room semantics, subject to review/owner ratification.

Historical post-D3 seed rows: **0**.
"""
    (args.out/"report.md").write_text(report,encoding="utf-8")
    print(report)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
