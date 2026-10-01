#!/usr/bin/env python3
"""#2026 name-erased typed-graph invariant witness.

Consumes the research corpus from #1962. Node ids are used only as internal
keys / human-readable report labels. They never enter WL colors or
automorphism signatures.

Primary question:
  after deleting human names and binary slot/code information, which corpus
  nodes can the typed relation graph distinguish by structure alone?
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Node:
    ident: str
    era: str
    kind: str
    prefix_evidence: str


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str


def read_nodes(path: Path) -> dict[str, Node]:
    out: dict[str, Node] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            out[row["id"]] = Node(
                ident=row["id"],
                era=row["era"],
                kind=row["kind"],
                prefix_evidence=row.get("prefix_evidence", ""),
            )
    return out


def read_edges(path: Path) -> list[Edge]:
    out: list[Edge] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            out.append(Edge(row["source"], row["target"], row["relation"]))
    return out


def initial_label(node: Node, mode: str) -> tuple[str, ...]:
    if mode == "topology":
        return ("node",)
    if mode == "kind":
        return (node.kind,)
    if mode == "kind-era":
        return (node.kind, node.era)
    if mode == "kind-era-evidence":
        return (node.kind, node.era, node.prefix_evidence or "-")
    raise ValueError(mode)


def canon_colors(signatures: dict[str, object]) -> dict[str, int]:
    unique = sorted(set(signatures.values()), key=repr)
    index = {sig: i for i, sig in enumerate(unique)}
    return {node: index[sig] for node, sig in signatures.items()}


def same_partition(a: dict[str, int], b: dict[str, int]) -> bool:
    names = sorted(a)
    for i, x in enumerate(names):
        for y in names[i:]:
            if (a[x] == a[y]) != (b[x] == b[y]):
                return False
    return True


def wl_refine(
    nodes: dict[str, Node],
    edges: list[Edge],
    mode: str,
) -> tuple[dict[str, int], int, list[int]]:
    colors = canon_colors({n: initial_label(node, mode) for n, node in nodes.items()})
    class_counts = [len(set(colors.values()))]

    outgoing: dict[str, list[tuple[str, str]]] = defaultdict(list)
    incoming: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for e in edges:
        outgoing[e.source].append((e.relation, e.target))
        incoming[e.target].append((e.relation, e.source))

    rounds = 0
    while True:
        signatures = {}
        for n in nodes:
            out_sig = tuple(sorted((rel, colors[t]) for rel, t in outgoing[n]))
            in_sig = tuple(sorted((rel, colors[s]) for rel, s in incoming[n]))
            signatures[n] = (colors[n], out_sig, in_sig)
        new_colors = canon_colors(signatures)
        rounds += 1
        class_counts.append(len(set(new_colors.values())))
        if same_partition(new_colors, colors):
            return new_colors, rounds, class_counts
        colors = new_colors


def cells(colors: dict[str, int]) -> list[list[str]]:
    groups: dict[int, list[str]] = defaultdict(list)
    for n, c in colors.items():
        groups[c].append(n)
    return [sorted(v) for _, v in sorted(groups.items())]


def edge_counter(edges: list[Edge]) -> Counter[tuple[str, str, str]]:
    return Counter((e.source, e.target, e.relation) for e in edges)


def preserves_graph(
    mapping: dict[str, str],
    nodes: dict[str, Node],
    edges: list[Edge],
    mode: str,
) -> bool:
    # Initial non-name attributes are part of the tested structure.
    for a, b in mapping.items():
        if initial_label(nodes[a], mode) != initial_label(nodes[b], mode):
            return False
    before = edge_counter(edges)
    after = Counter((mapping[e.source], mapping[e.target], e.relation) for e in edges)
    return before == after


def bounded_automorphisms(
    nodes: dict[str, Node],
    edges: list[Edge],
    colors: dict[str, int],
    mode: str,
    max_full_search: int = 200_000,
) -> tuple[int | None, list[tuple[str, str]], int]:
    cs = cells(colors)
    variable = [c for c in cs if len(c) > 1]
    search_space = 1
    for cell in variable:
        search_space *= math.factorial(len(cell))

    swap_witnesses: list[tuple[str, str]] = []
    ident = {n: n for n in nodes}
    for cell in variable:
        for a, b in itertools.combinations(cell, 2):
            mapping = dict(ident)
            mapping[a], mapping[b] = b, a
            if preserves_graph(mapping, nodes, edges, mode):
                swap_witnesses.append((a, b))

    if search_space > max_full_search:
        return None, swap_witnesses, search_space

    count = 0
    fixed = [c[0] for c in cs if len(c) == 1]
    variable_perms = [list(itertools.permutations(c)) for c in variable]
    for chosen in itertools.product(*variable_perms):
        mapping = {n: n for n in fixed}
        for cell, perm in zip(variable, chosen):
            mapping.update(dict(zip(cell, perm)))
        if preserves_graph(mapping, nodes, edges, mode):
            count += 1
    return count, swap_witnesses, search_space


def tarjan_scc(nodes: dict[str, Node], edges: list[Edge], relations: set[str]) -> list[list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e.relation in relations:
            graph[e.source].append(e.target)

    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    result: list[list[str]] = []

    def visit(v: str) -> None:
        nonlocal index
        indices[v] = low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in graph[v]:
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
            result.append(sorted(comp))

    for n in nodes:
        if n not in indices:
            visit(n)
    return sorted(result, key=lambda c: (len(c), c))


def report_mode(nodes: dict[str, Node], edges: list[Edge], mode: str) -> dict[str, object]:
    colors, rounds, history = wl_refine(nodes, edges, mode)
    cs = cells(colors)
    collision_cells = [c for c in cs if len(c) > 1]
    unique_nodes = sum(1 for c in cs if len(c) == 1)
    auto_count, swaps, search_space = bounded_automorphisms(nodes, edges, colors, mode)

    return {
        "mode": mode,
        "rounds": rounds,
        "history": history,
        "classes": len(cs),
        "unique_nodes": unique_nodes,
        "collision_cells": collision_cells,
        "automorphism_count": auto_count,
        "automorphism_search_space": search_space,
        "swap_witnesses": swaps,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--nodes",
        default="docs/research/1962-lisp1-15-nodes.tsv",
    )
    ap.add_argument(
        "--edges",
        default="docs/research/1962-lisp1-15-edges.tsv",
    )
    args = ap.parse_args()

    nodes = read_nodes(Path(args.nodes))
    edges = read_edges(Path(args.edges))

    print(f"nodes={len(nodes)} typed_edges={len(edges)}")
    print("identity bits/codes are NOT used in primary refinement")
    print()

    results = []
    for mode in ("topology", "kind", "kind-era", "kind-era-evidence"):
        r = report_mode(nodes, edges, mode)
        results.append(r)
        print(
            f"{mode}: classes={r['classes']} unique={r['unique_nodes']} "
            f"collisions={len(r['collision_cells'])} rounds={r['rounds']} "
            f"history={r['history']}"
        )
        for cell in r["collision_cells"]:
            print("  collision:", ",".join(cell))
        if r["automorphism_count"] is None:
            print(
                f"  automorphism full-search skipped; candidate search space="
                f"{r['automorphism_search_space']}"
            )
        else:
            print(f"  exact automorphisms within WL cells={r['automorphism_count']}")
        for a, b in r["swap_witnesses"]:
            print(f"  exact swap automorphism: {a}<->{b}")
        print()

    # Historical semantic distinction used only as a falsifier after refinement.
    # It never participates in the colors.
    richest = results[-1]
    lambda_label_collision = any(
        {"lambda", "label"}.issubset(set(cell))
        for cell in richest["collision_cells"]
    )
    print(f"lambda/label structurally collide in richest name-erased mode: {lambda_label_collision}")

    sccs = tarjan_scc(nodes, edges, {"calls", "recursion"})
    nontrivial = [c for c in sccs if len(c) > 1]
    print(f"calls+recursion SCCs >1 node: {len(nontrivial)}")
    for comp in nontrivial:
        print("  SCC:", ",".join(comp))

    print()
    if lambda_label_collision:
        print("FALSIFIER: current typed graph cannot explain LAMBDA vs LABEL from structure alone")
        print("ACTION: relation kernel needs evidence that distinguishes binding vs recursive-binding semantics")
    else:
        print("RESULT: LAMBDA/LABEL are structurally distinguished under current admitted metadata")

    unresolved = sum(len(c) for c in richest["collision_cells"])
    print(f"name-erased unresolved nodes in richest mode: {unresolved}/{len(nodes)}")
    print("NON-CONCLUSION: unique WL color is not a proof of semantic identity or necessity")


if __name__ == "__main__":
    main()
