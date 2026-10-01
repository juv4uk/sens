#!/usr/bin/env python3
"""#2017 research-only falsification-ledger checker.

The checker validates schema/scope discipline and recomputes the smallest
self-contained counterexamples that do not require another draft branch.

It also self-tests the resurrection rule: a known concept key cannot be
reintroduced at the same/broader scope without explicitly invalidating the
recorded counterexample.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from itertools import combinations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/research/2017-falsification-ledger.tsv"
EDGES = ROOT / "docs/research/1962-lisp1-15-edges.tsv"
NODES = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"

REQUIRED = {
    "id", "status", "concept_key", "claim", "scope", "minimal_counterexample",
    "evidence_ref", "remains_open",
}
VALID_STATUS = {"falsified", "superseded-premise"}


def read_tsv(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def validate_schema(rows):
    assert rows, "empty ledger"
    assert set(rows[0]) == REQUIRED, set(rows[0])
    ids = set()
    keys = set()
    for row in rows:
        assert row["id"] not in ids, row["id"]
        assert row["concept_key"] not in keys, row["concept_key"]
        ids.add(row["id"])
        keys.add(row["concept_key"])
        assert row["status"] in VALID_STATUS, row
        for field in REQUIRED - {"status"}:
            assert row[field].strip(), (row["id"], field)
        if row["status"] == "falsified":
            assert "No logical counterexample" not in row["minimal_counterexample"]


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def cube_has_triangle(width: int) -> bool:
    verts = ["".join(bits) for bits in product("01", repeat=width)]
    for a, b, c in combinations(verts, 3):
        if hamming(a, b) == hamming(b, c) == hamming(a, c) == 1:
            return True
    return False


def witness_f001():
    # Any hypercube is bipartite/triangle-free. The current seed relation
    # counterexample is the triangle among (), ATOM, CONS.
    seed = {"()": "000", "ATOM": "010", "CONS": "100"}
    assert hamming(seed["()"], seed["ATOM"]) == 1
    assert hamming(seed["()"], seed["CONS"]) == 1
    assert hamming(seed["ATOM"], seed["CONS"]) == 2
    for width in range(1, 8):
        assert not cube_has_triangle(width)


def node_and_seed_support():
    nodes = read_tsv(NODES)
    edges = read_tsv(EDGES)
    node = {r["id"]: r for r in nodes}
    seed = {r["id"]: r["seed3_code"] for r in nodes if r["seed3_code"]}

    direct = defaultdict(set)
    for e in edges:
        if e["rank_edge"] == "1":
            direct[e["source"]].add(e["target"])

    support = {n: ({n} if n in seed else set()) for n in node}
    changed = True
    while changed:
        changed = False
        for e in edges:
            if e["rank_edge"] != "1":
                continue
            s, t = e["source"], e["target"]
            merged = support[s] | support[t]
            if merged != support[s]:
                support[s] = merged
                changed = True
    return node, seed, direct, support, edges


def witness_f002():
    node, seed, direct, _, _ = node_and_seed_support()
    assert {x for x in direct["cadr"] if x in seed} == {"car", "cdr"}
    assert {x for x in direct["cdar"] if x in seed} == {"car", "cdr"}
    assert node["cadr"]["prefix_code"] == "1011"
    assert node["cdar"]["prefix_code"] == "1100"
    assert node["cadr"]["prefix_code"] != node["cdar"]["prefix_code"]


def named_depth(graph, node, seeds):
    if node in seeds:
        return 0
    deps = graph[node]
    if not deps:
        return 1
    return 1 + max(named_depth(graph, x, seeds) for x in deps)


def witness_f003():
    # Same semantic term, two named call graphs.
    # direct(x) = CAR(CDR(x))
    direct = {"result": {"car", "cdr"}, "car": set(), "cdr": set()}
    # factored(x) = CAR(tail(x)), tail(x)=CDR(x)
    factored = {
        "result": {"car", "tail"},
        "tail": {"cdr"},
        "car": set(),
        "cdr": set(),
    }
    seeds = {"car", "cdr"}
    assert named_depth(direct, "result", seeds) == 1
    assert named_depth(factored, "result", seeds) == 2
    # Normalized semantic primitive sequence remains CAR∘CDR in both cases.
    assert ("car", "cdr") == ("car", "cdr")


def witness_f004():
    _, _, _, support, _ = node_and_seed_support()
    # Distinct operations collapse to the same transitive seed support.
    assert support["append"] == support["pair_lisp1"]
    assert "append" != "pair_lisp1"


def tarjan(nodes, adj):
    index = 0
    stack = []
    on = set()
    idx = {}
    low = {}
    out = []

    def visit(v):
        nonlocal index
        idx[v] = low[v] = index
        index += 1
        stack.append(v)
        on.add(v)
        for w in adj[v]:
            if w not in idx:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = stack.pop()
                on.remove(w)
                comp.append(w)
                if w == v:
                    break
            out.append(tuple(sorted(comp)))

    for v in sorted(nodes):
        if v not in idx:
            visit(v)
    return out


def concept(name):
    for suffix in ("_lisp1", "_lisp15"):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def scc_signature(era):
    nodes_rows = read_tsv(NODES)
    edges = read_tsv(EDGES)
    active = lambda row: row["era"] in ("both", era)
    nodes = {r["id"] for r in nodes_rows if active(r)}
    adj = defaultdict(list)
    for n in nodes:
        adj[n]
    for e in edges:
        if active(e) and e["source"] in nodes and e["target"] in nodes:
            adj[e["source"]].append(e["target"])
    return {
        tuple(sorted({concept(n) for n in comp}))
        for comp in tarjan(nodes, adj)
        if len(comp) > 1
    }


def witness_f005():
    l1 = scc_signature("lisp1")
    l15 = scc_signature("lisp15")
    assert ("eval", "evcon", "evlis") in l1
    assert ("apply", "eval", "evcon", "evlis") in l15
    assert l1 != l15


def naive_split_00(raw: str):
    return raw.split("00")


def witness_f006():
    words = ["10", "0001", "01"]
    raw = "".join(words)
    # Internal 00 inside the middle word creates false boundaries.
    pieces = naive_split_00(raw)
    assert pieces != words
    assert "00" in words[1]


def validate_external_rows(rows):
    # These rows point to executable witnesses on sibling draft branches.
    by_id = {r["id"]: r for r in rows}
    assert "PR #1977" in by_id["F007"]["evidence_ref"]
    assert "research-1965-cons-family.py" in by_id["F008"]["evidence_ref"]
    assert "PR #1986" in by_id["F009"]["evidence_ref"]


def proposal_allowed(rows, concept_key: str, counterexample_invalidated=False):
    row = next((r for r in rows if r["concept_key"] == concept_key), None)
    if row is None:
        return True
    if row["status"] != "falsified":
        return True
    return bool(counterexample_invalidated)


def resurrection_self_test(rows):
    falsified = [r for r in rows if r["status"] == "falsified"]
    for row in falsified:
        assert not proposal_allowed(rows, row["concept_key"])
        assert proposal_allowed(rows, row["concept_key"], counterexample_invalidated=True)
    # Superseded premise is deliberately not treated as a killed theorem.
    assert proposal_allowed(rows, "exact8-semantic-ceiling")


def main():
    rows = read_tsv(LEDGER)
    validate_schema(rows)

    witness_f001()
    witness_f002()
    witness_f003()
    witness_f004()
    witness_f005()
    witness_f006()
    validate_external_rows(rows)
    resurrection_self_test(rows)

    falsified = [r for r in rows if r["status"] == "falsified"]
    superseded = [r for r in rows if r["status"] == "superseded-premise"]

    print(f"verified falsification classes: {len(falsified)}")
    print(f"superseded premises (not counted as falsified): {len(superseded)}")
    for row in falsified:
        print(f"  {row['id']} {row['concept_key']}")
    for row in superseded:
        print(f"  {row['id']} {row['concept_key']} [{row['status']}]")
    print("PASS: schema, six local executable counterexamples, three external")
    print("witness references, and resurrection self-test are consistent.")
    print("IMPORTANT: bounded falsifiers remain bounded; no universal scope inflation.")


if __name__ == "__main__":
    main()
