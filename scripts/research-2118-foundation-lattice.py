#!/usr/bin/env python3
"""#2118 foundation-lattice anti-circularity checker."""

from __future__ import annotations
import csv
from pathlib import Path

TABLE=Path("docs/research/2118-foundation-claims.tsv")
ALLOWED_STATUS={"premise","conjecture","witness","theorem","falsified","unknown"}
AUTHORITY_CLASSES={"substrate","carrier","semantic","epistemic","proof"}
FORBIDDEN_ANCESTOR_CLASSES={"mechanism","surface"}

def load():
    with TABLE.open(encoding="utf-8", newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    return {r["claim_id"]:r for r in rows}

def deps(row):
    x=row["authority_prereqs"].strip()
    return [] if not x else [p for p in x.split(";") if p]

def topo(rows):
    state={}
    stack=[]
    order=[]
    def visit(n):
        st=state.get(n,0)
        if st==1:
            cycle=stack[stack.index(n):]+[n]
            raise AssertionError("authority cycle: "+" -> ".join(cycle))
        if st==2:return
        state[n]=1; stack.append(n)
        for d in deps(rows[n]):
            assert d in rows, f"missing dependency {d} referenced by {n}"
            visit(d)
        stack.pop(); state[n]=2; order.append(n)
    for n in rows: visit(n)
    return order

def ancestors(rows,n,memo):
    if n in memo:return memo[n]
    out=set()
    for d in deps(rows[n]):
        out.add(d); out |= ancestors(rows,d,memo)
    memo[n]=out
    return out

def validate(rows):
    assert rows, "empty lattice"
    for n,r in rows.items():
        assert r["status"] in ALLOWED_STATUS,(n,r["status"])
        assert r["layer_class"],n
        assert r["axis"],n
        assert n not in deps(r),f"self dependency {n}"
        if r["status"] in {"witness","theorem","falsified"}:
            assert r["evidence_refs"].strip(),f"{n}: evidence-bearing status without evidence refs"
    order=topo(rows)
    memo={}
    for n,r in rows.items():
        if r["layer_class"] in AUTHORITY_CLASSES:
            bad=[a for a in ancestors(rows,n,memo)
                 if rows[a]["layer_class"] in FORBIDDEN_ANCESTOR_CLASSES]
            assert not bad,f"{n}: semantic/foundation authority leaks from mechanism/surface ancestors {bad}"
    return order

def negative_controls(rows):
    # Synthetic authority cycle must fail.
    clone={k:dict(v) for k,v in rows.items()}
    clone["distinction"]["authority_prereqs"]="semantic-admission"
    try:
        validate(clone)
    except AssertionError as e:
        assert "cycle" in str(e)
    else:
        raise AssertionError("cycle negative control did not fail")

    # Synthetic mechanism->semantic authority leak must fail without a cycle.
    clone={k:dict(v) for k,v in rows.items()}
    clone["semantic-admission"]["authority_prereqs"]="exact-word-identity;constraint-status;execution-mechanism"
    try:
        validate(clone)
    except AssertionError as e:
        assert "leaks" in str(e) or "cycle" in str(e)
    else:
        raise AssertionError("mechanism authority leak negative control did not fail")

    # Synthetic surface->meaning leak must fail.
    clone={k:dict(v) for k,v in rows.items()}
    clone["predicate-polarity-d1"]["authority_prereqs"]="binary-cardinality-2;surface-projection"
    try:
        validate(clone)
    except AssertionError as e:
        assert "leaks" in str(e) or "cycle" in str(e)
    else:
        raise AssertionError("surface authority leak negative control did not fail")

def main():
    rows=load()
    order=validate(rows)
    negative_controls(rows)
    print("FOUNDATION lattice checker: PASS")
    print(f"claims={len(rows)}")
    print(f"axes={len(set(r['axis'] for r in rows.values()))}")
    print(f"authority_edges={sum(len(deps(r)) for r in rows.values())}")
    print("authority_cycles=0")
    print("mechanism->foundation authority leaks=0")
    print("surface->foundation authority leaks=0")
    print("negative controls=3 PASS")
    print("partial order:", " -> ".join(order))
    print("NON-CONCLUSION: this DAG does not impose one total foundation hierarchy")

if __name__=="__main__":
    main()
