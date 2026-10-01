#!/usr/bin/env python3
"""Graph-theoretic benchmarks for domain-graph research (#1961).

Approaches (not Cachegrind):
  1. Explicit digraph construction for bīja3 seed + CAR/CDR prefix family
  2. Tarjan SCC (cycles would break pure-prefix generator story)
  3. Prefix-tree / DAG height and branching
  4. Hamming-1 adjacency vs typed generator edges (geometry falsifier)
  5. Compression ratios: flat peer table vs root+generator edge set
  6. BFS touch counts as abstract "mechanism steps" (theory, not CPU)

Research-only. No production semantics.
"""

from __future__ import annotations

import csv
import io
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

Word = str  # bitstring, e.g. "101"


# --- corpus: bīja3 seed + selector family (from #1961 authority text) --------

BIJA3: Dict[Word, str] = {
    "000": "NIL",
    "001": "QUOTE",
    "010": "ATOM",
    "011": "EQ",
    "100": "CONS",
    "101": "CAR",
    "110": "CDR",
    "111": "COND",
}

# Typed generator edges: append bit is executable composition (CAR/CDR only).
SELECTOR_ROOTS = ("101", "110")


def selector_words(max_depth: int = 4) -> Dict[Word, str]:
    """Generate CAR/CDR family words up to max_depth suffix bits."""
    out: Dict[Word, str] = {}
    for root, name in (("101", "CAR"), ("110", "CDR")):
        out[root] = name
        frontier = [root]
        depth = 0
        while depth < max_depth:
            nxt = []
            for w in frontier:
                for bit, tag in (("0", "A"), ("1", "D")):
                    # Classical naming: caar = car of car → append toward root reading
                    # Research model: path is root + suffix bits applied inward.
                    child = w + bit
                    label = name + "/" + "".join(
                        "CAR" if b == "0" else "CDR" for b in child[len(root) :]
                    )
                    out[child] = label
                    nxt.append(child)
            frontier = nxt
            depth += 1
    return out


@dataclass(frozen=True)
class Edge:
    src: Word
    dst: Word
    kind: str  # "prefix_gen" | "hamming1" | "seed_peer"


def build_prefix_edges(words: Iterable[Word]) -> List[Edge]:
    s = set(words)
    edges = []
    for w in s:
        if len(w) >= 2:
            parent = w[:-1]
            if parent in s:
                edges.append(Edge(parent, w, "prefix_gen"))
    return edges


def build_hamming1_edges(words: Iterable[Word]) -> List[Edge]:
    """Same-width Hamming distance 1 — the 'cube geometry' candidate."""
    by_w: Dict[int, List[Word]] = defaultdict(list)
    for w in words:
        by_w[len(w)].append(w)
    edges = []
    for width, group in by_w.items():
        n = len(group)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = group[i], group[j]
                dist = sum(x != y for x, y in zip(a, b))
                if dist == 1:
                    edges.append(Edge(a, b, "hamming1"))
                    edges.append(Edge(b, a, "hamming1"))
    return edges


def tarjan_scc(nodes: Set[Word], edges: List[Edge]) -> List[List[Word]]:
    index = 0
    stack: List[Word] = []
    onstack: Set[Word] = set()
    indices: Dict[Word, int] = {}
    lowlink: Dict[Word, int] = {}
    result: List[List[Word]] = []
    adj: Dict[Word, List[Word]] = defaultdict(list)
    for e in edges:
        adj[e.src].append(e.dst)

    def strongconnect(v: Word) -> None:
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        onstack.add(v)
        for w in adj[v]:
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in onstack:
                lowlink[v] = min(lowlink[v], indices[w])
        if lowlink[v] == indices[v]:
            comp: List[Word] = []
            while True:
                w = stack.pop()
                onstack.discard(w)
                comp.append(w)
                if w == v:
                    break
            result.append(comp)

    for v in nodes:
        if v not in indices:
            strongconnect(v)
    return result


def dag_height(nodes: Set[Word], edges: List[Edge]) -> int:
    """Longest path length in edges on a DAG (prefix edges only)."""
    adj: Dict[Word, List[Word]] = defaultdict(list)
    indeg: Dict[Word, int] = {n: 0 for n in nodes}
    for e in edges:
        if e.kind != "prefix_gen":
            continue
        adj[e.src].append(e.dst)
        indeg[e.dst] = indeg.get(e.dst, 0) + 1
        indeg.setdefault(e.src, 0)
    # Kahn + DP
    q = deque([n for n in nodes if indeg.get(n, 0) == 0])
    dist = {n: 0 for n in nodes}
    seen = 0
    while q:
        u = q.popleft()
        seen += 1
        for v in adj[u]:
            dist[v] = max(dist[v], dist[u] + 1)
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    if seen != len(nodes):
        return -1  # cycle
    return max(dist.values()) if dist else 0


def bfs_touch_count(roots: Iterable[Word], edges: List[Edge], targets: Set[Word]) -> int:
    """Sum of BFS edges traversed from each root until all targets reached / exhausted."""
    adj: Dict[Word, List[Word]] = defaultdict(list)
    for e in edges:
        if e.kind == "prefix_gen":
            adj[e.src].append(e.dst)
    touches = 0
    for r in roots:
        q = deque([r])
        seen = {r}
        while q:
            u = q.popleft()
            for v in adj[u]:
                touches += 1
                if v not in seen:
                    seen.add(v)
                    q.append(v)
    return touches


def metrics_for_depth(max_depth: int) -> Dict[str, object]:
    sel = selector_words(max_depth)
    nodes = set(BIJA3) | set(sel)
    # Isolate selector subgraph for generator claims
    sel_nodes = set(sel)
    prefix_e = build_prefix_edges(sel_nodes)
    ham_e = build_hamming1_edges(sel_nodes)
    # Full seed as disconnected peers (no edges) + selector component
    sccs = tarjan_scc(sel_nodes, prefix_e)
    nontrivial = [c for c in sccs if len(c) > 1]
    height = dag_height(sel_nodes, prefix_e)
    # Compression
    flat_rows = len(sel_nodes)  # one registry row each
    gen_roots = 2
    gen_actions = 2  # suffix 0/1
    gen_edges = len(prefix_e)
    # Hamming vs typed: how many Hamming edges are NOT prefix edges?
    prefix_pairs = {(e.src, e.dst) for e in prefix_e}
    ham_only = sum(1 for e in ham_e if (e.src, e.dst) not in prefix_pairs)
    # Seed triangle (uses relation is not Hamming-complete) — structural note
    seed_words = list(BIJA3.keys())
    seed_ham = build_hamming1_edges(seed_words)
    # Complete graph edge count at width 3: C(8,2)*2 directed undirected C(8,2)
    seed_ham_undirected = len(seed_ham) // 2
    max_undirected = 8 * 7 // 2
    touches = bfs_touch_count(SELECTOR_ROOTS, prefix_e, sel_nodes)
    return {
        "max_suffix_depth": max_depth,
        "selector_nodes": len(sel_nodes),
        "prefix_edges": len(prefix_e),
        "hamming1_directed_edges": len(ham_e),
        "hamming_edges_not_prefix": ham_only,
        "scc_count": len(sccs),
        "nontrivial_scc_count": len(nontrivial),
        "dag_height_edges": height,
        "flat_registry_rows": flat_rows,
        "generator_roots": gen_roots,
        "generator_actions": gen_actions,
        "compression_rows_over_actions": round(flat_rows / gen_actions, 3),
        "bfs_touch_steps": touches,
        "seed_nodes": 8,
        "seed_hamming1_undirected": seed_ham_undirected,
        "seed_max_undirected": max_undirected,
        "seed_hamming_density": round(seed_ham_undirected / max_undirected, 4),
    }


def main() -> None:
    rows = [metrics_for_depth(d) for d in (1, 2, 3, 4, 6, 8)]
    # Micro timing of pure graph construction (not CPU of SENS runtime)
    t0 = time.perf_counter()
    for _ in range(200):
        metrics_for_depth(6)
    t1 = time.perf_counter()
    host = {
        "host_metric": "metrics_for_depth_6_x200",
        "seconds": round(t1 - t0, 6),
        "note": "wall host only; not Cachegrind; not SENS runtime",
    }

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    text = buf.getvalue()
    print(text)
    print("host_timing", host)

    out_dir = Path("docs/research")
    if out_dir.is_dir():
        (out_dir / "1961-graph-metrics.tsv").write_text(text, encoding="utf-8")
        print("wrote docs/research/1961-graph-metrics.tsv")


if __name__ == "__main__":
    main()
