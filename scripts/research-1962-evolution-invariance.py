#!/usr/bin/env python3
"""#1962: Lisp I -> Lisp 1.5 evolution-invariance falsifier.

Research-only. This script checks that evolution of evaluator topology does not
silently relocate already-established bīja3 / selector-path identities.
It allocates nothing and changes no production authority.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"
EDGES_PATH = ROOT / "docs/research/1962-lisp1-15-edges.tsv"

ERAS = ("lisp1", "lisp15")
PROVEN_EVIDENCE = {"exact-seed", "exact-selector"}

EXPECTED_SEED = {
    "nil": "000",
    "quote": "001",
    "atom": "010",
    "eq": "011",
    "cons": "100",
    "car": "101",
    "cdr": "110",
    "cond": "111",
}

EXPECTED_SELECTORS = {
    "caar": "1010",
    "cadr": "1011",
    "cadar": "10110",
    "caddr": "10111",
    "cdar": "1100",
    "cddr": "1101",
}

EXPECTED_EVALUATOR_SCC = {
    "lisp1": {"eval_lisp1", "evcon_lisp1", "evlis_lisp1"},
    "lisp15": {"apply_lisp15", "eval_lisp15", "evcon_lisp15", "evlis_lisp15"},
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


NODES = read_tsv(NODES_PATH)
EDGES = read_tsv(EDGES_PATH)
NODE = {row["id"]: row for row in NODES}


def active(era: str, row: dict[str, str]) -> bool:
    return row["era"] in ("both", era)


def active_nodes(era: str) -> set[str]:
    return {row["id"] for row in NODES if active(era, row)}


def proven_map(era: str) -> dict[str, str]:
    out: dict[str, str] = {}
    occupied: dict[str, str] = {}
    for row in NODES:
        if not active(era, row):
            continue
        code = row["prefix_code"]
        if not code or row["prefix_evidence"] not in PROVEN_EVIDENCE:
            continue
        if code in occupied:
            raise AssertionError(
                f"{era}: proven code collision {code}: {occupied[code]} vs {row['id']}"
            )
        occupied[code] = row["id"]
        out[row["id"]] = code
    return out


def verify_no_era_specific_allocation() -> None:
    offenders = [
        (row["id"], row["era"], row["prefix_code"])
        for row in NODES
        if row["era"] != "both" and row["prefix_code"]
    ]
    if offenders:
        raise AssertionError(
            "era-specific research nodes must not steal canonical words: "
            + ", ".join(f"{node}@{era}={code}" for node, era, code in offenders)
        )


def verify_canonical_stability() -> dict[str, str]:
    maps = {era: proven_map(era) for era in ERAS}
    if maps["lisp1"] != maps["lisp15"]:
        left = set(maps["lisp1"].items())
        right = set(maps["lisp15"].items())
        raise AssertionError(
            "proven identity map moved across eras: "
            f"lisp1-only={sorted(left - right)} lisp15-only={sorted(right - left)}"
        )

    expected = EXPECTED_SEED | EXPECTED_SELECTORS
    if maps["lisp1"] != expected:
        missing = set(expected.items()) - set(maps["lisp1"].items())
        extra = set(maps["lisp1"].items()) - set(expected.items())
        raise AssertionError(
            f"bounded proven map drift: missing={sorted(missing)} extra={sorted(extra)}"
        )
    return maps["lisp1"]


def evaluator_graph(era: str) -> tuple[set[str], dict[str, list[str]]]:
    nodes = active_nodes(era)
    evaluator_nodes = {node for node in nodes if NODE[node]["kind"] == "evaluator"}
    adj: dict[str, list[str]] = defaultdict(list)

    for edge in EDGES:
        if not active(era, edge):
            continue
        if edge["relation"] not in {"calls", "recursion"}:
            continue
        source, target = edge["source"], edge["target"]
        if source in evaluator_nodes and target in evaluator_nodes:
            adj[source].append(target)

    for node in evaluator_nodes:
        adj[node]
    return evaluator_nodes, adj


def tarjan(nodes: set[str], adj: dict[str, list[str]]) -> list[set[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    out: list[set[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in adj[node]:
            if target not in indices:
                visit(target)
                lowlink[node] = min(lowlink[node], lowlink[target])
            elif target in on_stack:
                lowlink[node] = min(lowlink[node], indices[target])

        if lowlink[node] == indices[node]:
            component: set[str] = set()
            while True:
                target = stack.pop()
                on_stack.remove(target)
                component.add(target)
                if target == node:
                    break
            out.append(component)

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return out


def verify_topology_evolves() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for era in ERAS:
        nodes, adj = evaluator_graph(era)
        components = tarjan(nodes, adj)
        expected = EXPECTED_EVALUATOR_SCC[era]
        if expected not in components:
            rendered = [sorted(component) for component in components if len(component) > 1]
            raise AssertionError(
                f"{era}: expected evaluator SCC {sorted(expected)} not found; "
                f"multi-node SCCs={rendered}"
            )
        found[era] = expected

    if found["lisp1"] == found["lisp15"]:
        raise AssertionError("fixture no longer demonstrates evaluator-topology evolution")
    if "apply_lisp1" in found["lisp1"]:
        raise AssertionError("Lisp I positive control unexpectedly absorbed apply into evaluator SCC")
    if "apply_lisp15" not in found["lisp15"]:
        raise AssertionError("Lisp 1.5 positive control lost apply from evaluator SCC")
    return found


def main() -> None:
    verify_no_era_specific_allocation()
    stable = verify_canonical_stability()
    scc = verify_topology_evolves()

    print("stable-proven-identities")
    for node, code in sorted(stable.items(), key=lambda item: (len(item[1]), item[1])):
        print(f"{code}\t{node}")

    print("\nevaluator-topology")
    print("lisp1\t{" + ",".join(sorted(scc["lisp1"])) + "}")
    print("lisp15\t{" + ",".join(sorted(scc["lisp15"])) + "}")
    print("change\tapply joins the evaluator SCC in Lisp 1.5")

    print(
        "\nPASS: evaluator topology evolves from Lisp I to Lisp 1.5 "
        "while all bounded proven bīja3/selector identities remain unchanged."
    )


if __name__ == "__main__":
    main()
