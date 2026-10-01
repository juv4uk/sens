#!/usr/bin/env python3
"""#1969: first Model C invariance slice.

Research-only. This does not allocate binary words.

The slice tests one positive invariance requirement and one preservation
requirement:
1. harmless helper factoring/renaming must not change normalized cost;
2. a real historical SCC-topology change must remain visible, not be erased.

Two normalized cost models are compared on the same canonical selector term:
- primitive-step count;
- seed-word description bits (3 bits per bīja3 primitive operator).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"
EDGES = ROOT / "docs/research/1962-lisp1-15-edges.tsv"

PRIMITIVES = {"car", "cdr"}
SEED_WIDTH = {"car": 3, "cdr": 3}


def substitute_arg(term, arg):
    if term == "$0":
        return arg
    if isinstance(term, tuple):
        fn, child = term
        return (fn, substitute_arg(child, arg))
    return term


def normalize_term(term, helpers):
    if isinstance(term, str):
        return term
    fn, arg = term
    arg = normalize_term(arg, helpers)
    if fn in helpers:
        return normalize_term(substitute_arg(helpers[fn], arg), helpers)
    return (fn, arg)


def primitive_step_cost(term):
    if isinstance(term, str):
        return 0
    fn, child = term
    return (1 if fn in PRIMITIVES else 0) + primitive_step_cost(child)


def seed_word_bit_cost(term):
    if isinstance(term, str):
        return 0
    fn, child = term
    return SEED_WIDTH.get(fn, 0) + seed_word_bit_cost(child)


def read_tsv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def active(era, row):
    return row["era"] in ("both", era)


def tarjan(nodes, adj):
    index = 0
    stack = []
    on_stack = set()
    indices = {}
    low = {}
    out = []

    def visit(v):
        nonlocal index
        indices[v] = index
        low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in adj[v]:
            if w not in indices:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.append(w)
                if w == v:
                    break
            out.append(tuple(sorted(comp)))

    for v in sorted(nodes):
        if v not in indices:
            visit(v)
    return out


def concept(name):
    for suffix in ("_lisp1", "_lisp15"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def scc_signature(era):
    nodes_rows = read_tsv(NODES)
    edge_rows = read_tsv(EDGES)
    nodes = {r["id"] for r in nodes_rows if active(era, r)}
    adj = defaultdict(list)
    for n in nodes:
        adj[n]
    for e in edge_rows:
        if active(era, e) and e["source"] in nodes and e["target"] in nodes:
            adj[e["source"]].append(e["target"])

    multi = []
    for comp in tarjan(nodes, adj):
        if len(comp) > 1:
            multi.append(tuple(sorted({concept(n) for n in comp})))
    return tuple(sorted(multi))


def main():
    direct = ("car", ("cdr", "x"))
    factored_tail = ("car", ("tail", "x"))
    factored_q = ("car", ("q", "x"))

    canonical = normalize_term(direct, {})
    canonical_tail = normalize_term(factored_tail, {"tail": ("cdr", "$0")})
    canonical_q = normalize_term(factored_q, {"q": ("cdr", "$0")})

    assert canonical == canonical_tail == canonical_q

    fixtures = (
        ("direct", canonical),
        ("helper-tail", canonical_tail),
        ("helper-q", canonical_q),
    )

    print("normalized refactoring fixture")
    for name, term in fixtures:
        print(
            f"  {name:12s} term={term!r} "
            f"steps={primitive_step_cost(term)} "
            f"seed-bits={seed_word_bit_cost(term)}"
        )

    step_costs = {primitive_step_cost(term) for _, term in fixtures}
    bit_costs = {seed_word_bit_cost(term) for _, term in fixtures}
    assert step_costs == {2}
    assert bit_costs == {6}

    l1 = scc_signature("lisp1")
    l15 = scc_signature("lisp15")

    print("\nSCC concept signatures")
    print("  lisp1 :", l1)
    print("  lisp15:", l15)

    assert ("eval", "evcon", "evlis") in l1
    assert ("apply", "eval", "evcon", "evlis") in l15
    assert l1 != l15

    print("\nRESULT")
    print("  PASS invariance: helper insertion/renaming leaves both normalized costs unchanged")
    print("  PASS sensitivity: real Lisp I -> Lisp 1.5 evaluator SCC change remains observable")
    print("  quotient note: no path-sharing pair is merged into one semantic node here")
    print("  scope: first Model C fixture, not a production/addressing law")


if __name__ == "__main__":
    main()
