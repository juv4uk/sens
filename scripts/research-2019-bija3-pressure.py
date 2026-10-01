#!/usr/bin/env python3
"""#2019 first diagnostic: remove-one-seed pressure in the bounded corpus.

This is NOT a minimality/necessity proof.

It answers only:
- which current derived nodes transitively depend on each bīja3 seed;
- whether that pressure is stable between Lisp I and Lisp 1.5;
- whether the declared graph already derives a seed from other nodes.

Absence of a graph derivation is not logical independence.
High pressure is not proof of necessity.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"
EDGES = ROOT / "docs/research/1962-lisp1-15-edges.tsv"


def read_tsv(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="	"))


NODES_ROWS = read_tsv(NODES)
EDGE_ROWS = read_tsv(EDGES)
NODE = {r["id"]: r for r in NODES_ROWS}


def active(era: str, row: dict[str, str]) -> bool:
    return row["era"] in ("both", era)


def graph(era: str):
    nodes = {r["id"] for r in NODES_ROWS if active(era, r)}
    edges = [
        e for e in EDGE_ROWS
        if active(era, e)
        and e["rank_edge"] == "1"
        and e["source"] in nodes
        and e["target"] in nodes
    ]
    adj = defaultdict(set)
    for n in nodes:
        adj[n]
    for e in edges:
        if e["source"] == e["target"] and e["relation"] == "recursion":
            continue
        adj[e["source"]].add(e["target"])
    return nodes, edges, adj


def seeds(nodes):
    return {
        n for n in nodes
        if NODE[n].get("seed3_code")
    }


def transitive_seed_support(nodes, adj):
    base = seeds(nodes)
    memo = {}

    def walk(n, seen):
        if n in base:
            return {n}
        if n in memo:
            return memo[n]
        if n in seen:
            return set()
        out = set()
        seen = seen | {n}
        for dep in adj[n]:
            out |= walk(dep, seen)
        memo[n] = out
        return out

    return {n: walk(n, set()) for n in nodes}


def reachable(adj, source, target):
    stack = [source]
    seen = set()
    while stack:
        cur = stack.pop()
        if cur == target:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(adj[cur] - seen)
    return False


def rows_for_era(era: str):
    nodes, _, adj = graph(era)
    base = seeds(nodes)
    support = transitive_seed_support(nodes, adj)
    derived = sorted(n for n in nodes if n not in base)

    rows = []
    for seed in sorted(base, key=lambda n: NODE[n]["seed3_code"]):
        dependent = [n for n in derived if seed in support[n]]
        exclusive = [n for n in dependent if support[n] == {seed}]
        co = sorted({
            other
            for n in dependent
            for other in support[n]
            if other != seed
        })
        # This asks only what the currently declared dependency graph says.
        # It is not a proof that no alternative semantic derivation exists.
        graph_derivable = any(
            reachable(adj, seed, other)
            for other in base
            if other != seed
        )
        rows.append({
            "era": era,
            "seed": seed,
            "seed3_code": NODE[seed]["seed3_code"],
            "dependent_nodes": len(dependent),
            "exclusive_nodes": len(exclusive),
            "co_seed_count": len(co),
            "graph_has_outgoing_seed_path": "1" if graph_derivable else "0",
            "dependents": ",".join(dependent),
            "exclusive": ",".join(exclusive),
            "co_seeds": ",".join(co),
        })
    return rows


def main():
    rows = rows_for_era("lisp1") + rows_for_era("lisp15")

    by = defaultdict(dict)
    for r in rows:
        by[r["seed"]][r["era"]] = r

    print("seed	code	lisp1-dep	lisp15-dep	delta	lisp1-exclusive	lisp15-exclusive")
    for seed in sorted(by, key=lambda n: NODE[n]["seed3_code"]):
        a = by[seed]["lisp1"]
        b = by[seed]["lisp15"]
        delta = int(b["dependent_nodes"]) - int(a["dependent_nodes"])
        print(
            f"{seed}	{a['seed3_code']}	{a['dependent_nodes']}	"
            f"{b['dependent_nodes']}	{delta:+d}	"
            f"{a['exclusive_nodes']}	{b['exclusive_nodes']}"
        )

    # Sanity: eight inherited seeds are present in both eras.
    assert len(by) == 8
    assert all("lisp1" in x and "lisp15" in x for x in by.values())

    # Positive control: selector roots have exclusive descendants.
    assert int(by["car"]["lisp1"]["exclusive_nodes"]) >= 1
    assert int(by["cdr"]["lisp1"]["exclusive_nodes"]) >= 1

    # The current graph does not itself prove alternative derivations
    # of the inherited seed nodes from other seed nodes.
    assert all(
        r["graph_has_outgoing_seed_path"] == "0"
        for r in rows
    )

    out = ROOT / "docs/research/2019-bija3-pressure.tsv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="	")
        w.writeheader()
        w.writerows(rows)

    print()
    print("WROTE", out)
    print("INTERPRETATION:")
    print("- counts measure pressure in the declared corpus, not logical necessity;")
    print("- zero graph derivation means 'not derived here', not 'independent in principle';")
    print("- era deltas show representation/corpus sensitivity that #2019 must preserve.")


if __name__ == "__main__":
    main()
