#!/usr/bin/env python3
"""Research-only finite ground congruence closure, no D10 opcode."""
import itertools
import json
import re
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-ground-congruence-closure-research-20261009.json"
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")

def validate(record):
    if not isinstance(record, dict) or set(record) != {"nodes", "equalities", "queries"}:
        raise ValueError("need exactly nodes/equalities/queries")
    nodes = record["nodes"]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 64:
        raise ValueError("need bounded nonempty finite ground DAG")
    built, arities = {}, {}
    for row in nodes:
        if not isinstance(row, dict) or set(row) != {"id", "symbol", "args"}:
            raise ValueError("node needs id/symbol/args")
        ident, symbol, args = row["id"], row["symbol"], row["args"]
        if not isinstance(ident, str) or not NAME.fullmatch(ident) or ident in built:
            raise ValueError("bad or duplicate node id")
        if not isinstance(symbol, str) or not NAME.fullmatch(symbol):
            raise ValueError("bad uninterpreted symbol")
        if not isinstance(args, list) or len(args) > 6 or any(
            not isinstance(a, str) or a not in built for a in args
        ):
            raise ValueError("args must be earlier DAG nodes")
        old = arities.setdefault(symbol, len(args))
        if old != len(args):
            raise ValueError("inconsistent symbol arity")
        built[ident] = (symbol, tuple(args))
    for category in ("equalities", "queries"):
        rows = record[category]
        if not isinstance(rows, list) or len(rows) > 256:
            raise ValueError("bounded list expected")
        for pair in rows:
            if not isinstance(pair, list) or len(pair) != 2 or any(
                not isinstance(v, str) or v not in built for v in pair
            ):
                raise ValueError("pair must name existing nodes")
    return built

def output(terms, queries, equivalent):
    ids = sorted(terms)
    pending, groups = set(ids), []
    while pending:
        seed = min(pending)
        group = sorted(v for v in ids if equivalent(seed, v))
        groups.append(group)
        pending.difference_update(group)
    return {"classes": groups,
            "entailed": [bool(equivalent(a, b)) for a, b in queries]}

def union_find_closure(record):
    """Ground term congruence: union-find signatures fixed point."""
    terms = validate(record)
    parent = {x:x for x in terms}
    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def unite(a,b):
        a,b = root(a),root(b)
        if a == b: return False
        parent[max(a,b)] = min(a,b)
        return True
    for a,b in record["equalities"]:
        unite(a,b)
    while True:
        changed, signatures = False, {}
        for node,(symbol,args) in terms.items():
            signature = (symbol,tuple(root(a) for a in args))
            if signature in signatures:
                changed = unite(node,signatures[signature]) or changed
            else:
                signatures[signature] = node
        if not changed: break
    return output(terms,record["queries"],lambda a,b:root(a)==root(b))

def relation_fixed_point(record):
    """Independent all-pairs relation closure: no union-find."""
    terms = validate(record)
    ids = sorted(terms)
    relation = {(x,x) for x in ids}
    for a,b in record["equalities"]:
        relation.update(((a,b),(b,a)))
    while True:
        before = len(relation)
        for x,y,z in itertools.product(ids,repeat=3):
            if (x,y) in relation and (y,z) in relation:
                relation.add((x,z))
        for a in ids:
            sa,aa = terms[a]
            for b in ids:
                sb,ab = terms[b]
                if sa==sb and len(aa)==len(ab) and all((i,j) in relation
                                                         for i,j in zip(aa,ab)):
                    relation.update(((a,b),(b,a)))
        if len(relation)==before: break
    return output(terms,record["queries"],lambda a,b:(a,b) in relation)

def z3_euf_oracle(record):
    """REALLY independent Microsoft Z3 uninterpreted functions."""
    terms = validate(record)
    from z3 import Const,DeclareSort,Function,Not,Solver,unsat,sat
    U = DeclareSort("U")
    functions, expr = {}, {}
    for ident,(name,args) in terms.items():
        arity = len(args)
        if arity==0:
            term = functions.setdefault((name,0),Const("c_"+name,U))
        else:
            f = functions.setdefault((name,arity),
                Function("f_"+name,*([U]*(arity+1))))
            term = f(*[expr[a] for a in args])
        expr[ident]=term
    solver=Solver()
    for a,b in record["equalities"]:
        solver.add(expr[a]==expr[b])
    def entails(a,b):
        solver.push()
        solver.add(Not(expr[a]==expr[b]))
        status=solver.check()
        solver.pop()
        if status not in (sat,unsat):
            raise RuntimeError("unknown Z3 result")
        return status==unsat
    return output(terms,record["queries"],entails)

def dossier():
    data=json.loads(DOSSIER.read_text(encoding="utf-8"))
    assert data["schema"]=="sens-d10-ground-congruence-research/v1"
    assert data["semantic_name"]=="GROUND-CONGRUENCE-CLOSURE-PARTITION"
    assert data["status"]=="HOLD-CORE-VS-LIBRARY"
    assert data["coordinate"] is None
    assert data["selected"] is False and data["ratified_resident"] is False
    assert data["current_d9_behavioral_dedup"]=="REVIEW_REQUIRED"
    assert len(data["primary_sources"])>=2
    for case in data["examples"]:
        expect=case["output"]
        assert union_find_closure(case["input"])==expect,case["name"]
        assert relation_fixed_point(case["input"])==expect,case["name"]
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--verify-z3",action="store_true")
    args=p.parse_args()
    data=dossier()
    if args.verify_z3:
        for case in data["examples"]:
            assert z3_euf_oracle(case["input"])==case["output"],case["name"]
        template=data["examples"][0]["input"]
        pairs=[list(p) for p in itertools.combinations(
            [n["id"] for n in template["nodes"]],2)]
        for mask in (0,1,2,3,5,7,11,13,17,31,63,127):
            record={**template,"equalities":[pair for i,pair in enumerate(pairs)
                                                if mask & (1<<i)]}
            expect=union_find_closure(record)
            assert relation_fixed_point(record)==expect
            assert z3_euf_oracle(record)==expect
    print(json.dumps({"status":"RESEARCH-HOLD","name":data["semantic_name"],
                      "examples":len(data["examples"]),
                      "real_z3":args.verify_z3,"selected":False,"ratified":False}))

if __name__=="__main__":
    main()
