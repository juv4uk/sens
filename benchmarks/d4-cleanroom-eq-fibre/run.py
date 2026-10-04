#!/usr/bin/env python3
"""#3240 clean-room D4 fibre under ratified D3 EQ=101.

Family law:
  lift exact key identity over an association chain.

Local D1 suffix bit asks: update permitted?
  0 = NO  -> observe/read exact matching association
  1 = YES -> construct/update exact matching association

No historical post-D3 resident table/name is used as a premise.
"""

from __future__ import annotations
import argparse, csv, json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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

def eq_p(a:Any,b:Any)->int:
    if isinstance(a,Pair) or isinstance(b,Pair):
        return NO
    return YES if a==b else NO

def binding(key:Atom,value:Any)->Pair:
    return Pair(key,value)

def env_cons(key:Atom,value:Any,rest:Any)->Pair:
    return Pair(binding(key,value),rest)

def env_items(env:Any)->list[tuple[Atom,Any]]:
    out=[]
    cur=env
    while cur!=EMPTY:
        if not isinstance(cur,Pair) or not isinstance(cur.first,Pair):
            raise SemanticError("malformed association chain")
        k=cur.first.first
        if not isinstance(k,Atom):
            raise SemanticError("association key must be atom")
        out.append((k,cur.first.rest))
        cur=cur.rest
    return out

def make_env(rows:list[tuple[str,str]])->Any:
    out:Any=EMPTY
    for k,v in reversed(rows):
        out=env_cons(Atom(k),Atom(v),out)
    return out

@dataclass
class Stats:
    comparisons:list[dict]=field(default_factory=list)
    reentries:int=0

@dataclass(frozen=True)
class ReadResult:
    value:Any

@dataclass(frozen=True)
class WriteResult:
    env:Any

def assoc_lift(
    mode:int,
    key:Atom,
    new_value:Any,
    env:Any,
    *,
    stats:Stats,
    fuel:int,
):
    if mode not in (NO,YES):
        raise SemanticError("mode must be exact D1 predicate bit")
    if fuel<=0:
        raise SemanticError("fuel exhausted")

    if env==EMPTY:
        if mode==NO:
            return ReadResult(EMPTY)
        return WriteResult(env_cons(key,new_value,EMPTY))

    if not isinstance(env,Pair) or not isinstance(env.first,Pair):
        raise SemanticError("malformed association chain")
    cell=env.first
    cell_key=cell.first
    cell_value=cell.rest
    if not isinstance(cell_key,Atom):
        raise SemanticError("association key must be atom")

    matched=eq_p(key,cell_key)
    stats.comparisons.append({
        "query":key.name,
        "cell":cell_key.name,
        "eq":matched,
    })

    if matched==YES:
        if mode==NO:
            return ReadResult(cell_value)
        return WriteResult(Pair(binding(key,new_value),env.rest))

    stats.reentries+=1
    tail=assoc_lift(mode,key,new_value,env.rest,stats=stats,fuel=fuel-1)
    if mode==NO:
        assert isinstance(tail,ReadResult)
        return tail
    assert isinstance(tail,WriteResult)
    return WriteResult(Pair(cell,tail.env))

def prefix_eq_bad(a:Atom,b:Atom)->int:
    # Deliberate non-exact comparator for the falsifier.
    return YES if a.name[:1]==b.name[:1] else NO

def bad_read(key:Atom,env:Any)->Any:
    cur=env
    while cur!=EMPTY:
        cell=cur.first
        if prefix_eq_bad(key,cell.first)==YES:
            return cell.rest
        cur=cur.rest
    return EMPTY

def comparison_trace_expected(key:Atom,env:Any)->list[dict]:
    rows=[]
    for k,_ in env_items(env):
        bit=eq_p(key,k)
        rows.append({"query":key.name,"cell":k.name,"eq":bit})
        if bit==YES:
            break
    return rows

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)

    env=make_env([("aa","v0"),("ab","v1"),("b","v2")])
    original=env

    # Existing-key read/write: same exact EQ trace, different mode effect.
    query=Atom("ab")
    read_stats=Stats()
    read=assoc_lift(NO,query,Atom("unused"),env,stats=read_stats,fuel=16)
    assert isinstance(read,ReadResult) and read.value==Atom("v1")
    assert env==original

    write_stats=Stats()
    write=assoc_lift(YES,query,Atom("new"),env,stats=write_stats,fuel=16)
    assert isinstance(write,WriteResult)
    assert env==original  # persistent update: input unchanged
    assert env_items(write.env)==[
        (Atom("aa"),Atom("v0")),
        (Atom("ab"),Atom("new")),
        (Atom("b"),Atom("v2")),
    ]
    assert read_stats.comparisons==write_stats.comparisons
    assert read_stats.comparisons==comparison_trace_expected(query,env)

    # Missing-key behavior: NO observes EMPTY/no-witness, YES appends.
    missing=Atom("c")
    miss_read_stats=Stats()
    miss_read=assoc_lift(NO,missing,Atom("unused"),env,stats=miss_read_stats,fuel=16)
    assert miss_read==ReadResult(EMPTY)

    miss_write_stats=Stats()
    miss_write=assoc_lift(YES,missing,Atom("v3"),env,stats=miss_write_stats,fuel=16)
    assert env_items(miss_write.env)==env_items(env)+[(Atom("c"),Atom("v3"))]
    assert miss_read_stats.comparisons==miss_write_stats.comparisons
    assert miss_read_stats.comparisons==comparison_trace_expected(missing,env)

    # Exact-EQ falsifier: prefix comparator incorrectly claims a missing key exists.
    collision_env=make_env([("ab","x"),("ac","y")])
    collision_key=Atom("ad")
    exact_stats=Stats()
    exact=assoc_lift(NO,collision_key,Atom("unused"),collision_env,stats=exact_stats,fuel=8)
    assert exact==ReadResult(EMPTY)
    bad=bad_read(collision_key,collision_env)
    assert bad!=EMPTY

    # Suffix orientation is locally anchored by D1 question "update permitted?".
    # Reversing it violates both the read-only and update controls.
    mode0_env=env
    mode0=assoc_lift(NO,query,Atom("reversed"),mode0_env,stats=Stats(),fuel=16)
    assert isinstance(mode0,ReadResult) and mode0_env==env
    mode1=assoc_lift(YES,query,Atom("reversed"),env,stats=Stats(),fuel=16)
    assert isinstance(mode1,WriteResult) and mode1.env!=env

    # Malformed/fuel controls.
    controls=[]
    malformed=Pair(Atom("not-a-binding"),EMPTY)
    for name,fn in [
        ("malformed-mode",lambda: assoc_lift(2,query,Atom("x"),env,stats=Stats(),fuel=8)),
        ("malformed-env",lambda: assoc_lift(NO,query,Atom("x"),malformed,stats=Stats(),fuel=8)),
        ("insufficient-fuel",lambda: assoc_lift(NO,Atom("z"),Atom("x"),env,stats=Stats(),fuel=1)),
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
            "local_d1_meaning":"update-permitted? NO",
            "parent_invariant":"all key decisions use exact EQ",
            "new_delta":"observe matching value; preserve environment",
            "coordinate":"1010",
            "coordinate_earned":True,
        },
        {
            "suffix_bit":"1",
            "local_d1_meaning":"update-permitted? YES",
            "parent_invariant":"all key decisions use exact EQ",
            "new_delta":"update exact match or append missing association",
            "coordinate":"1011",
            "coordinate_earned":True,
        },
    ]
    with (args.out/"fibre.tsv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys()),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    result={
        "schema":"d4-cleanroom-eq-fibre/v1",
        "authority":"research-only",
        "parent":{"bits":"101","semantic":"exact identity predicate"},
        "generator":{
            "equation":"A_b(k,v,E): traverse E by EQ(k,key(cell)); b=0 observes; b=1 persistently updates/appends",
            "bit_domain":"D1 PredicateBit",
            "bit_question":"update permitted?",
            "bit0":"NO",
            "bit1":"YES",
            "parent_recovery":"erase traversal/action and retain the exact EQ comparison trace",
        },
        "children":rows,
        "witness":{
            "existing_key_same_comparison_trace":True,
            "read_preserves_env":True,
            "write_preserves_unrelated_bindings":True,
            "missing_read_returns_empty_no_witness":True,
            "missing_write_appends":True,
        },
        "falsifiers":{
            "non_exact_prefix_comparator_collision":True,
            "reverse_bit_orientation_breaks_controls":True,
            "fail_closed_controls":controls,
        },
        "historical_post_d3_seed_rows":0,
        "non_conclusions":[
            "this law does not determine other D4 fibres",
            "association representation is a mechanism witness, not a universal storage mandate",
            "posterior historical comparison is outside this witness",
        ],
    }
    (args.out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report="""# D4 clean-room EQ fibre — #3240

Parent: D3:101 exact identity predicate.

Local suffix bit is a D1 PredicateBit answering:
**update permitted?**

- suffix 0 / NO: traverse associations by exact EQ and observe the matched value; input environment is unchanged.
- suffix 1 / YES: traverse by the same exact EQ decisions and persistently update the match or append a missing key.

Controls:
- read and write emit identical EQ comparison traces to the same match;
- read preserves the environment;
- write changes only the requested binding and preserves unrelated bindings;
- absent read returns structural EMPTY/no-witness;
- absent write appends;
- a non-exact prefix comparator produces a false match and is rejected;
- reversing suffix meaning violates read-only/update controls;
- malformed mode/environment and insufficient fuel fail closed.

Result:
the two-child generator law earns candidate fibre coordinates **1010** and **1011**
for these clean-room semantics, subject to review/owner ratification.

Historical post-D3 seed rows: **0**.
"""
    (args.out/"report.md").write_text(report,encoding="utf-8")
    print(report)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
