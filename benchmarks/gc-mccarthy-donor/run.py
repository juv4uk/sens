#!/usr/bin/env python3
"""#2549 — historical GC donor witness.

This is deliberately NOT a collector implementation for SENS.
It extracts one representation-independent law from the LISP 1.5
mark/sweep description:

    explicit roots -> reachability mark -> linear sweep -> reusable slots

The witness compares that mechanism with an independent reachability oracle
and attacks the result by deleting one required trace edge.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Cell:
    children: tuple[str, ...] = ()


def oracle_reachable(graph: dict[str, Cell], roots: Iterable[str]) -> set[str]:
    """Independent DFS oracle for mathematical graph reachability."""
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        if node not in graph:
            raise KeyError(f"unknown root/reference: {node}")
        seen.add(node)
        stack.extend(graph[node].children)
    return seen


def donor_mark(graph: dict[str, Cell], roots: Iterable[str]) -> set[str]:
    """Iterative worklist mark phase, intentionally separate from the oracle."""
    marked: set[str] = set()
    work = deque(roots)
    while work:
        node = work.popleft()
        if node in marked:
            continue
        if node not in graph:
            raise KeyError(f"unknown root/reference: {node}")
        marked.add(node)
        for child in graph[node].children:
            work.append(child)
    return marked


def linear_sweep(slot_order: list[str], marked: set[str]) -> list[str]:
    """Return unmarked slots in physical sweep order."""
    return [slot for slot in slot_order if slot not in marked]


def check_case(
    name: str,
    graph: dict[str, Cell],
    roots: tuple[str, ...],
    slot_order: list[str],
) -> tuple[int, int]:
    oracle = oracle_reachable(graph, roots)
    marked = donor_mark(graph, roots)
    assert marked == oracle, (name, marked, oracle)
    reclaimed = linear_sweep(slot_order, marked)
    assert set(reclaimed) == set(graph) - oracle
    return len(marked), len(reclaimed)


def relabel_graph(
    graph: dict[str, Cell], mapping: dict[str, str]
) -> dict[str, Cell]:
    return {
        mapping[node]: Cell(tuple(mapping[child] for child in cell.children))
        for node, cell in graph.items()
    }


def main() -> None:
    cases: list[tuple[str, dict[str, Cell], tuple[str, ...], list[str]]] = []

    # Reachable chain plus garbage tail.
    g1 = {
        "A": Cell(("B",)),
        "B": Cell(("C",)),
        "C": Cell(),
        "G1": Cell(("G2",)),
        "G2": Cell(),
    }
    cases.append(("chain-plus-garbage", g1, ("A",), list(g1)))

    # Shared diamond: repeated discovery must not duplicate work semantically.
    g2 = {
        "R": Cell(("L", "Q")),
        "L": Cell(("S",)),
        "Q": Cell(("S",)),
        "S": Cell(),
        "DEAD": Cell(),
    }
    cases.append(("shared-diamond", g2, ("R",), list(g2)))

    # Rooted cycle survives.
    g3 = {
        "X": Cell(("Y",)),
        "Y": Cell(("X",)),
        "DEAD": Cell(),
    }
    cases.append(("rooted-cycle", g3, ("X",), list(g3)))

    # Unrooted cycle is reclaimable under tracing reachability.
    g4 = {
        "LIVE": Cell(),
        "U": Cell(("V",)),
        "V": Cell(("U",)),
    }
    cases.append(("unrooted-cycle", g4, ("LIVE",), list(g4)))

    # Empty root set: every managed slot is reclaimable.
    g5 = {
        "P": Cell(("Q",)),
        "Q": Cell(),
    }
    cases.append(("empty-roots", g5, (), list(g5)))

    total_live = 0
    total_reclaimed = 0
    for name, graph, roots, order in cases:
        live, reclaimed = check_case(name, graph, roots, order)
        total_live += live
        total_reclaimed += reclaimed

    # Representation relabeling invariance:
    # rename every physical slot while preserving graph topology.
    base = {
        "pair0": Cell(("pair1", "pair2")),
        "pair1": Cell(),
        "pair2": Cell(("pair3",)),
        "pair3": Cell(),
        "garbage": Cell(),
    }
    roots = ("pair0",)
    oracle_before = oracle_reachable(base, roots)
    mapping = {
        "pair0": "slot-91",
        "pair1": "slot-07",
        "pair2": "slot-44",
        "pair3": "slot-12",
        "garbage": "slot-63",
    }
    renamed = relabel_graph(base, mapping)
    renamed_roots = tuple(mapping[r] for r in roots)
    oracle_after = oracle_reachable(renamed, renamed_roots)
    assert {mapping[n] for n in oracle_before} == oracle_after
    assert donor_mark(renamed, renamed_roots) == oracle_after

    # Falsifier: omit one required trace edge from the mechanism model.
    truth = {
        "R": Cell(("A",)),
        "A": Cell(("B",)),
        "B": Cell(),
    }
    broken_trace = {
        "R": Cell(("A",)),
        "A": Cell(),  # missing A -> B
        "B": Cell(),
    }
    oracle_truth = oracle_reachable(truth, ("R",))
    marked_broken = donor_mark(broken_trace, ("R",))
    assert oracle_truth == {"R", "A", "B"}
    assert marked_broken == {"R", "A"}
    assert marked_broken != oracle_truth

    # Invalid roots/references fail closed instead of silently retaining/freeing.
    try:
        donor_mark({"A": Cell()}, ("MISSING",))
    except KeyError:
        invalid_reference_fails_closed = True
    else:
        invalid_reference_fails_closed = False
    assert invalid_reference_fails_closed

    print("GC-DONOR-WITNESS=PASS")
    print("LAW=explicit-roots->iterative-mark->linear-sweep")
    print(f"CASES={len(cases)}")
    print(f"TOTAL-LIVE-WITNESSED={total_live}")
    print(f"TOTAL-RECLAIMED-WITNESSED={total_reclaimed}")
    print("INDEPENDENT-ORACLE=PASS")
    print("ROOTED-CYCLE=PASS")
    print("UNROOTED-CYCLE-RECLAIMABLE=PASS")
    print("RELABELING-INVARIANCE=PASS")
    print("MISSING-EDGE-FALSIFIER=PASS")
    print("INVALID-REFERENCE-FAILS-CLOSED=PASS")
    print("SEMANTIC-IDENTITY-FROM-SLOT=0")
    print("RUNTIME-IMPLEMENTATION=0")
    print("STATUS=HISTORICAL-DONOR-LAW-WITNESSED")


if __name__ == "__main__":
    main()
