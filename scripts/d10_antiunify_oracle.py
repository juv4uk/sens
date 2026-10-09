#!/usr/bin/env python3
"""Research-only Plotkin ground first-order anti-unification, NOT a D10 resident.
Ground inputs: {"atom":"a"} or {"fun":"f","args":[term,...]}.
Output introduces {"var":0}, {"var":1}, ... in first depth-first disagreement order.
Repeated structurally identical ordered disagreement pairs share variables.
"""
from __future__ import annotations
import argparse
import json

def check(t, depth=0, budget=None):
    if budget is None:
        budget = [4096]
    budget[0] -= 1
    if budget[0] < 0 or depth > 64:
        raise ValueError("finite term bound exceeded")
    if not isinstance(t, dict):
        raise ValueError("ground term must be a tagged record")
    if set(t) == {"atom"}:
        if not isinstance(t["atom"], str) or not t["atom"] or t["atom"].startswith("$"):
            raise ValueError("atom must be a nonempty ground symbol")
        return
    if set(t) == {"fun","args"}:
        if not isinstance(t["fun"], str) or not t["fun"] or t["fun"].startswith("$"):
            raise ValueError("invalid constructor")
        if not isinstance(t["args"], list) or not 1 <= len(t["args"]) <= 32:
            raise ValueError("constructor arity must be 1..32")
        for x in t["args"]:
            check(x, depth + 1, budget)
        return
    raise ValueError("variable or unrecognized record in ground input")

def key(t):
    if "atom" in t:
        return ("atom",t["atom"])
    return ("fun",t["fun"],tuple(key(x) for x in t["args"]))

def lgg(left,right):
    check(left); check(right)
    seen = {}
    sl, sr = [], []
    def visit(a,b):
        if key(a) == key(b):
            return a
        if "fun" in a and "fun" in b and a["fun"] == b["fun"] and len(a["args"]) == len(b["args"]):
            return {"fun":a["fun"],"args":[visit(x,y) for x,y in zip(a["args"],b["args"])]}
        k = (key(a),key(b))
        if k not in seen:
            seen[k] = len(sl)
            sl.append(a); sr.append(b)
        return {"var":seen[k]}
    return {"generalization":visit(left,right),"left_substitution":sl,"right_substitution":sr}

def lgg_independent(left,right):
    check(left); check(right)
    seen = {}
    sl, sr = [], []
    result = [None]
    stack = [(left,right,result,0)]
    while stack:
        a,b,holder,i = stack.pop()
        if key(a) == key(b):
            holder[i] = a
        elif "fun" in a and "fun" in b and a["fun"] == b["fun"] and len(a["args"]) == len(b["args"]):
            children = [None]*len(a["args"])
            holder[i] = {"fun":a["fun"],"args":children}
            for j in reversed(range(len(children))):
                stack.append((a["args"][j],b["args"][j],children,j))
        else:
            k = (key(a),key(b))
            if k not in seen:
                seen[k] = len(sl)
                sl.append(a);sr.append(b)
            holder[i] = {"var":seen[k]}
    return {"generalization":result[0],"left_substitution":sl,"right_substitution":sr}

def instantiate(pattern, substitution):
    if set(pattern) == {"var"}:
        index=pattern["var"]
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(substitution):
            raise ValueError("invalid generated variable")
        return substitution[index]
    if set(pattern)=={"atom"}:
        return pattern
    if set(pattern)=={"fun","args"}:
        return {"fun":pattern["fun"],"args":[instantiate(x,substitution) for x in pattern["args"]]}
    raise ValueError("invalid pattern")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--left",required=True)
    p.add_argument("--right",required=True)
    a=p.parse_args()
    try:
        print(json.dumps(lgg(json.loads(a.left),json.loads(a.right)),sort_keys=True))
    except (ValueError,TypeError) as e:
        p.exit(2,"BLOCKED: "+str(e)+"\n")
