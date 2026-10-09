#!/usr/bin/env python3
"""1967 Younger ambiguity counting: independent exact chart and explicit tree oracles.

This verifies a *research proposal*, not SENS binary runtime / D2 parser.
"""
from __future__ import annotations
import copy
import itertools
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-younger-1967-cnf-ambiguity-research.json"

def gram(start="S", nts=("S",), terminals=(("S", "a"),), binary=(("S", "S", "S"),)):
    return {"start": start, "nonterminals": tuple(nts),
            "terminal_rules": tuple(map(tuple, terminals)),
            "binary_rules": tuple(map(tuple, binary))}

def checked(g, tokens):
    if not isinstance(g, dict) or not isinstance(tokens, (tuple, list)) or not tokens:
        raise ValueError("finite nonempty token sequence required")
    n = g.get("nonterminals")
    if not isinstance(n, (tuple, list)) or not n or not all(type(x) is str and bool(x) for x in n):
        raise ValueError("invalid nonterminals")
    if len(n) != len(set(n)) or g.get("start") not in n:
        raise ValueError("duplicate or unknown nonterminal/start")
    if not all(type(t) is str and bool(t) for t in tokens):
        raise ValueError("empty/unknown token")
    tr, br = g.get("terminal_rules"), g.get("binary_rules")
    if not isinstance(tr, (tuple, list)) or not isinstance(br, (tuple, list)):
        raise ValueError("finite explicit rule sets required")
    if len(set(map(tuple, tr))) != len(tr) or len(set(map(tuple, br))) != len(br):
        raise ValueError("duplicate production (grammar is a set)")
    for rule in tr:
        if len(rule) != 2 or rule[0] not in n or type(rule[1]) is not str or not rule[1]:
            raise ValueError("terminal rule must be A->single token")
    for rule in br:
        if len(rule) != 3 or any(x not in n for x in rule):
            raise ValueError("strict CNF binary rule required")
    return g, tuple(tokens)

def chart_count(grammar, tokens):
    """CKY: exact natural-valued bottom-up semiring."""
    g, tokens = checked(grammar, tokens)
    n = len(tokens)
    cells = defaultdict(int)
    terminal = g["terminal_rules"]
    binary = g["binary_rules"]
    for i, token in enumerate(tokens):
        for a, word in terminal:
            if token == word:
                cells[(a, i, i+1)] += 1
    for width in range(2, n+1):
        for i in range(n-width+1):
            j = i+width
            for middle in range(i+1, j):
                for a, b, c in binary:
                    cells[(a, i, j)] += cells[(b, i, middle)]*cells[(c, middle, j)]
    return cells[(g["start"], 0, n)]

def explicit_trees(grammar, tokens):
    """Brute force, no chart, no memo, list concrete tree identities."""
    g, ts = checked(grammar, tokens)
    def enumerate_for(a, left, right):
        if right-left == 1:
            for a0, token in g["terminal_rules"]:
                if a0 == a and token == ts[left]:
                    yield (a, ("leaf", ts[left]))
        else:
            for aa, bb, cc in g["binary_rules"]:
                if aa != a:
                    continue
                for mid in range(left+1, right):
                    for l in enumerate_for(bb, left, mid):
                        for rr in enumerate_for(cc, mid, right):
                            yield (a, ("branch", mid, l, rr))
    return tuple(enumerate_for(g["start"], 0, len(ts)))

def baseline_test():
    g = gram()
    for n, expected in enumerate((1,1,2,5,14,42,132,429,1430,4862), start=1):
        result=chart_count(g, ("a",)*n)
        assert result==expected==(math.comb(2*(n-1), n-1)//n)
        if n<=6:
            ts=explicit_trees(g, ("a",)*n)
            assert len(ts)==result
            assert len(set(ts))==result
    double=gram("S", ("S","A","B","C","D"),
                (("A","a"),("B","b"),("C","a"),("D","b")),
                (("S","A","B"),("S","C","D")))
    assert chart_count(double, ("a","b"))==len(explicit_trees(double,("a","b")))==2
    assert chart_count(double, ("a","a"))==0
    direct=gram("S",("S","A","B"),(("A","a"),("B","b")),(("S","A","B"),))
    assert chart_count(direct,("a","b"))==1
    assert chart_count(direct,("b","a"))==0
    assert chart_count(gram("S",("S",),(),()),("a",))==0

    rng=random.Random(1967)
    differential=0
    words=[t for length in range(1,5) for t in itertools.product(("a","b"),repeat=length)]
    nonterms=("S","A","B")
    candidates=[(a,b,c) for a in nonterms for b in nonterms for c in nonterms]
    lexical=[(a,t) for a in nonterms for t in ("a","b")]
    for _ in range(36):
        grammar=gram("S",nonterms,
                     rng.sample(lexical,rng.randint(1,5)),
                     rng.sample(candidates,rng.randint(1,7)))
        permuted=gram("S",nonterms,
                      tuple(reversed(grammar["terminal_rules"])),
                      tuple(reversed(grammar["binary_rules"])))
        for tokens in words:
            a=chart_count(grammar,tokens)
            trees=explicit_trees(grammar,tokens)
            assert a==len(trees), (grammar,tokens,a,len(trees))
            assert a==chart_count(permuted,tokens), "rule order cannot change trees"
            assert len(set(trees))==len(trees), "duplicate parse tree"
            differential+=1
    return differential

def dossier_guard(d):
    assert d["schema"]=="d10-historical-symbolic-ai-cnf-ambiguity/v1"
    assert d["status"]=="SOURCE-PINNED-RESEARCH-HOLD-UNRATIFIED"
    assert d["baseline"]["inventory_blob"]=="3db40a04c1094c9ea13b0c8d6099ef1d882cf203"
    assert d["baseline"]["ratified"]==0
    for field in ("current_selected_delta","ratified_delta","coordinate_delta",
                  "d2_control_delta","physical_t5_delta","syntax_delta"):
        assert d["scope"][field]==0
    assert d["sources"][0]["doi"]=="10.1016/S0019-9958(67)80007-X"
    assert d["proposed"][0]["semantic_name"]=="FINITE-CNF-PARSE-COUNT"
    assert len(d["proposed"])==1
    assert d["proposed"][0]["status"]=="HOLD-CORE-VERSUS-LIBRARY-REVIEW"
    assert d["proposed"][0]["coordinate"] is None
    assert d["proposed"][0]["ratified"] is False
    assert d["proposed"][0]["width"]==10
    assert len(d["proposed"][0]["positive_witnesses"])>=5
    assert len(d["proposed"][0]["falsifiers"])>=5
    assert len(d["derived_and_hold"])>=5
    assert all(x["decision"]!="SELECTED" for x in d["derived_and_hold"])

def negative_mutations(d):
    corrupt=[
      lambda x:x["scope"].update(current_selected_delta=1),
      lambda x:x["scope"].update(ratified_delta=1),
      lambda x:x["scope"].update(coordinate_delta=1),
      lambda x:x["scope"].update(physical_t5_delta=1),
      lambda x:x["proposed"][0].update(coordinate="0"*10),
      lambda x:x["proposed"][0].update(ratified=True),
      lambda x:x["proposed"][0].update(status="SELECTED"),
      lambda x:x["proposed"][0]["falsifiers"].clear(),
      lambda x:x["baseline"].update(inventory_blob="0"*40),
      lambda x:x["sources"][0].update(doi="fake")
    ]
    for k,fn in enumerate(corrupt):
        bad=copy.deepcopy(d)
        fn(bad)
        try: dossier_guard(bad)
        except AssertionError: continue
        raise AssertionError(f"mutation {k} bypassed research gate")
    invalid=[
      (gram(),()), # no epsilon
      (gram(nts=("S","S")),("a",)), # ambiguous symbols
      (gram(binary=(("S","S"),)),("a",)), # unit rule forbidden
      (gram(terminals=(("S","a"),("S","a"))),("a",)), # duplicate rule
      (gram(binary=(("S","S","Q"),)),("a",)), # unknown nonterminal
      (gram(),("",)), # invalid token
    ]
    for g,words in invalid:
        try: chart_count(g,words)
        except (ValueError,TypeError): continue
        raise AssertionError("invalid grammar accepted")

def main():
    d=json.loads(DOSSIER.read_text(encoding="utf-8"))
    dossier_guard(d)
    cases=baseline_test()
    negative_mutations(d)
    print(f"D10-YOUNGER-CNF: PASS exhaustive_tree_vs_chart={cases}; Catalan n=1..10; negative_mutations=10; invalid_grammars=6")
    print("Research HOLD only; exact integers, 0 selected, 0 ratified, D2/T5 unchanged.")

if __name__=="__main__":
    main()
