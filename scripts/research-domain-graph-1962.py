#!/usr/bin/env python3
"""Research-only analyzer for SENS #1962. Не є semantic authority."""

from __future__ import annotations
import csv
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"
EDGES_PATH = ROOT / "docs/research/1962-lisp1-15-edges.tsv"

def read_tsv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

NODES = read_tsv(NODES_PATH)
EDGES = read_tsv(EDGES_PATH)
NODE = {row["id"]: row for row in NODES}

def active(era, row):
    return row["era"] in ("both", era)

def graph_for(era):
    nodes = {n["id"] for n in NODES if active(era, n)}
    edges = [e for e in EDGES if active(era, e)]
    adj = defaultdict(list)
    for e in edges:
        if e["source"] in nodes and e["target"] in nodes:
            adj[e["source"]].append(e["target"])
    for n in nodes:
        adj[n]
    return nodes, edges, adj

def tarjan(nodes, adj):
    index = 0
    stack = []
    on_stack = set()
    indices = {}
    lowlink = {}
    out = []

    def visit(v):
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in adj[v]:
            if w not in indices:
                visit(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])
        if lowlink[v] == indices[v]:
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

def model_a_named_depth(nodes, edges, sccs):
    """Діагностична глибина. Навмисно чутлива до helper names."""
    comp_of = {}
    for i, comp in enumerate(sccs):
        for n in comp:
            comp_of[n] = i

    deps = defaultdict(set)
    for e in edges:
        if e["rank_edge"] != "1":
            continue
        a, b = comp_of[e["source"]], comp_of[e["target"]]
        if a != b and NODE[e["target"]]["kind"] != "structure":
            deps[a].add(b)

    base_comps = {
        comp_of[n] for n in nodes
        if bool(NODE[n]["candidate_domain"])
    }

    @lru_cache(maxsize=None)
    def depth(c):
        if c in base_comps:
            return 0
        if not deps[c]:
            return 1
        return 1 + max(depth(d) for d in deps[c])

    return {n: depth(comp_of[n]) for n in nodes}

def model_b_basis_support(nodes, edges):
    """Розгортає залежності до D3/D4 candidate basis; відстань губиться."""
    basis = {n for n in nodes if bool(NODE[n]["candidate_domain"])}
    support = {n: ({n} if n in basis else set()) for n in nodes}
    changed = True
    while changed:
        changed = False
        for e in edges:
            s, t = e["source"], e["target"]
            if s not in nodes or t not in nodes:
                continue
            if NODE[t]["kind"] == "structure":
                continue
            merged = support[s] | support[t]
            if merged != support[s]:
                support[s] = merged
                changed = True
    return support

def naive_domain(depth):
    return "mūla4" if depth == 0 else f"janya{4 + depth}"

def report(era):
    nodes, edges, adj = graph_for(era)
    sccs = tarjan(nodes, adj)
    depth = model_a_named_depth(nodes, edges, sccs)
    support = model_b_basis_support(nodes, edges)

    print(f"=== {era} ===")
    d3 = sorted(n for n in nodes if NODE[n]["candidate_domain"] == "d3-candidate")
    m4 = sorted(n for n in nodes if NODE[n]["candidate_domain"] == "mūla4")
    print("candidate lower basis:")
    print("  D3 hypothesis: {" + ", ".join(d3) + "}")
    print("  mūla4:        {" + ", ".join(m4) + "}")

    print("multi-node SCC:")
    multi = [c for c in sccs if len(c) > 1]
    for comp in multi:
        print("  {" + ", ".join(comp) + "}")
    if not multi:
        print("  (none)")

    print("\nmodel A: named dependency depth (diagnostic only)")
    interesting = sorted(
        (n for n in nodes if not NODE[n]["candidate_domain"]
         and NODE[n]["kind"] != "structure"),
        key=lambda n: (depth[n], n),
    )
    for n in interesting:
        bases = ",".join(sorted(support[n])) or "-"
        print(
            f"  {n:20s} depth={depth[n]} "
            f"naive-domain={naive_domain(depth[n]):8s} "
            f"basis-support={{{bases}}}"
        )

    derived = [n for n in interesting if support[n]]
    support_sets = {tuple(sorted(support[n])) for n in derived}
    print("\nmodel B: transitive basis-support flattening")
    print(f"  derived nodes with basis support: {len(derived)}")
    print(f"  distinct basis-support sets:      {len(support_sets)}")
    print("  warning: basis expressibility alone has no distance information")

def main():
    eras = sys.argv[1:] or ["lisp1", "lisp15"]
    for era in eras:
        if era not in {"lisp1", "lisp15"}:
            raise SystemExit("unknown era: " + era)
    for i, era in enumerate(eras):
        if i:
            print()
        report(era)

if __name__ == "__main__":
    main()
