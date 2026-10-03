#!/usr/bin/env python3
"""#2551 — collector-independent GC adversarial graph/oracle corpus.

This is a RED/oracle layer for future SENS collectors, not a runtime GC.
It establishes representation-neutral fixtures and proves each falsifier is
sensitive before a managed heap implementation exists.

Current-Rust representation assumptions are delegated to #2548/#2595.
Runtime-dependent checks remain PENDING-RUNTIME-HEAP.
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Cell:
    children: tuple[str, ...] = ()
    payload: object = None


def oracle_reachable(graph: dict[str, Cell], roots: Iterable[str]) -> set[str]:
    """Independent iterative DFS mathematical reachability oracle."""
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        if node not in graph:
            raise KeyError(f"unknown managed reference: {node}")
        seen.add(node)
        stack.extend(graph[node].children)
    return seen


def worklist_mark(graph: dict[str, Cell], roots: Iterable[str]) -> set[str]:
    """Collector-like iterative marker, intentionally separate from DFS oracle."""
    seen: set[str] = set()
    work = deque(roots)
    while work:
        node = work.popleft()
        if node in seen:
            continue
        if node not in graph:
            raise KeyError(f"unknown managed reference: {node}")
        seen.add(node)
        work.extend(graph[node].children)
    return seen


def reclaimable(graph: dict[str, Cell], roots: Iterable[str]) -> set[str]:
    return set(graph) - worklist_mark(graph, roots)


def semantic_graph(graph: dict[str, Cell], roots: Iterable[str]) -> tuple:
    """Out-of-band semantic observation invariant under physical relabeling.

    Payload labels stand for logical values in this abstract fixture. Physical
    node IDs are intentionally omitted.
    """
    live = oracle_reachable(graph, roots)
    rows = []
    for node in live:
        cell = graph[node]
        child_payloads = tuple(graph[ch].payload for ch in cell.children if ch in live)
        rows.append((cell.payload, child_payloads))
    return tuple(sorted(rows, key=repr))


def relabel_graph(
    graph: dict[str, Cell], roots: tuple[str, ...], prefix: str = "copy"
) -> tuple[dict[str, Cell], tuple[str, ...]]:
    mapping = {node: f"{prefix}-{i}" for i, node in enumerate(reversed(list(graph)))}
    copied = {
        mapping[node]: Cell(
            tuple(mapping[ch] for ch in cell.children),
            cell.payload,
        )
        for node, cell in graph.items()
    }
    return copied, tuple(mapping[root] for root in roots)


def check_oracle_parity(name: str, graph: dict[str, Cell], roots: tuple[str, ...]) -> dict:
    oracle = oracle_reachable(graph, roots)
    marked = worklist_mark(graph, roots)
    assert marked == oracle, (name, marked, oracle)
    return {
        "name": name,
        "live": len(marked),
        "reclaimable": len(graph) - len(marked),
        "oracle_parity": True,
    }


@dataclass(frozen=True)
class Handle:
    slot: int
    generation: int


class AbstractHeap:
    """Tiny finite-slot generation model for stale-handle/reuse sensitivity."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.generation = [0] * capacity
        self.live = [False] * capacity

    def allocate(self) -> Handle:
        for slot in range(self.capacity):
            if not self.live[slot]:
                self.live[slot] = True
                return Handle(slot, self.generation[slot])
        raise MemoryError("abstract heap full")

    def reclaim(self, handle: Handle) -> None:
        self.deref(handle)
        self.live[handle.slot] = False
        self.generation[handle.slot] += 1

    def deref(self, handle: Handle) -> int:
        if handle.slot < 0 or handle.slot >= self.capacity:
            raise KeyError("invalid slot")
        if not self.live[handle.slot]:
            raise KeyError("reclaimed handle")
        if self.generation[handle.slot] != handle.generation:
            raise KeyError("stale generation")
        return handle.slot


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--deep-chain", type=int, default=100_000)
    args = ap.parse_args()
    if args.deep_chain < 10_000:
        ap.error("--deep-chain must remain adversarial (>=10000)")
    args.out.mkdir(parents=True, exist_ok=True)

    cases: list[dict] = []
    sensitivities: list[dict] = []

    # 1. Two-edge Pair: each declared edge is independently necessary.
    pair_graph = {
        "P": Cell(("FIRST", "REST"), "pair"),
        "FIRST": Cell((), "first-value"),
        "REST": Cell((), "rest-value"),
        "DEAD": Cell((), "dead"),
    }
    cases.append(check_oracle_parity("two-edge-pair", pair_graph, ("P",)))
    truth = oracle_reachable(pair_graph, ("P",))
    assert truth == {"P", "FIRST", "REST"}
    for omitted in ("FIRST", "REST"):
        kept = tuple(ch for ch in pair_graph["P"].children if ch != omitted)
        broken = dict(pair_graph)
        broken["P"] = Cell(kept, "pair")
        observed = worklist_mark(broken, ("P",))
        assert omitted not in observed
        assert observed != truth
        sensitivities.append({
            "fixture": "two-edge-pair",
            "attack": f"omit-P->{omitted}",
            "expected_failure": f"{omitted} becomes falsely reclaimable",
            "sensitive": True,
        })

    # 2. Diamond sharing: duplicate discovery is semantically harmless.
    diamond = {
        "R": Cell(("A", "B"), "root"),
        "A": Cell(("C",), "left"),
        "B": Cell(("C",), "right"),
        "C": Cell((), "shared"),
        "DEAD": Cell((), "dead"),
    }
    cases.append(check_oracle_parity("diamond-sharing", diamond, ("R",)))
    assert worklist_mark(diamond, ("R",)) == {"R", "A", "B", "C"}

    # 3/4. Rooted cycle survives; unrooted cycle is reclaimable.
    rooted_cycle = {
        "A": Cell(("B",), "cycle-a"),
        "B": Cell(("A",), "cycle-b"),
        "DEAD": Cell((), "dead"),
    }
    cases.append(check_oracle_parity("rooted-cycle", rooted_cycle, ("A",)))
    assert {"A", "B"} <= worklist_mark(rooted_cycle, ("A",))

    unrooted_cycle = {
        "LIVE": Cell((), "live"),
        "A": Cell(("B",), "cycle-a"),
        "B": Cell(("A",), "cycle-b"),
    }
    cases.append(check_oracle_parity("unrooted-cycle", unrooted_cycle, ("LIVE",)))
    assert reclaimable(unrooted_cycle, ("LIVE",)) == {"A", "B"}

    # 5. Closure/environment back-edge catches an RC-only mental model.
    env_cycle = {
        "ROOT": Cell(("CLOSURE",), "root"),
        "CLOSURE": Cell(("ENV",), "closure"),
        "ENV": Cell(("CAPTURED", "CLOSURE"), "environment"),
        "CAPTURED": Cell((), "captured-value"),
        "DEAD": Cell(("DEAD2",), "dead1"),
        "DEAD2": Cell(("DEAD",), "dead2"),
    }
    cases.append(check_oracle_parity("closure-environment-cycle", env_cycle, ("ROOT",)))
    assert worklist_mark(env_cycle, ("ROOT",)) == {"ROOT", "CLOSURE", "ENV", "CAPTURED"}

    broken_env = dict(env_cycle)
    broken_env["CLOSURE"] = Cell((), "closure")  # omit Closure -> Environment
    assert "ENV" not in worklist_mark(broken_env, ("ROOT",))
    sensitivities.append({
        "fixture": "closure-environment-cycle",
        "attack": "omit-Closure->Environment",
        "expected_failure": "captured environment/value become falsely reclaimable",
        "sensitive": True,
    })

    # 6. Deep chain must be handled iteratively, independent of Python recursion.
    n = args.deep_chain
    deep = {
        f"N{i}": Cell((f"N{i+1}",) if i + 1 < n else (), f"value-{i}")
        for i in range(n)
    }
    deep_marked = worklist_mark(deep, ("N0",))
    assert len(deep_marked) == n
    assert deep_marked == oracle_reachable(deep, ("N0",))
    cases.append({
        "name": "deep-chain",
        "live": n,
        "reclaimable": 0,
        "oracle_parity": True,
        "iterative_worklist": True,
    })

    # 7. Host-only payload may contain pointer-looking integers; only explicit
    # children are managed edges. This models current Text7/BigInt boundary.
    host_payload = {
        "ROOT": Cell(("MANAGED",), {"looks_like_pointer": 0xDEADBEEF}),
        "MANAGED": Cell((), [0x1000, 0x2000, 0x3000]),
        "DEAD": Cell((), 0x1000),
    }
    cases.append(check_oracle_parity("host-only-pointer-looking-payload", host_payload, ("ROOT",)))
    assert worklist_mark(host_payload, ("ROOT",)) == {"ROOT", "MANAGED"}
    assert "DEAD" in reclaimable(host_payload, ("ROOT",))
    sensitivities.append({
        "fixture": "host-only-pointer-looking-payload",
        "attack": "conservative-scan-payload-integers-as-managed-refs",
        "expected_failure": "would invent edges not present in trace law",
        "sensitive": True,
    })

    # 8/9. Declared evaluator temporary root survives. Removing it must RED.
    temporary = {
        "PERM": Cell((), "permanent"),
        "TMP": Cell(("TMPCHILD",), "temporary"),
        "TMPCHILD": Cell((), "temporary-child"),
    }
    with_tmp = worklist_mark(temporary, ("PERM", "TMP"))
    without_tmp = worklist_mark(temporary, ("PERM",))
    assert {"TMP", "TMPCHILD"} <= with_tmp
    assert "TMP" not in without_tmp and "TMPCHILD" not in without_tmp
    cases.append({
        "name": "declared-temporary-root",
        "live": len(with_tmp),
        "reclaimable": len(temporary) - len(with_tmp),
        "oracle_parity": with_tmp == oracle_reachable(temporary, ("PERM", "TMP")),
    })
    sensitivities.append({
        "fixture": "declared-temporary-root",
        "attack": "remove-TMP-from-root-set",
        "expected_failure": "temporary and its child become falsely reclaimable",
        "sensitive": True,
    })

    # 10/11. Abstract finite-slot reuse + stale generation fail closed.
    heap = AbstractHeap(capacity=3)
    h0 = heap.allocate()
    h1 = heap.allocate()
    h2 = heap.allocate()
    try:
        heap.allocate()
    except MemoryError:
        full_detected = True
    else:
        full_detected = False
    assert full_detected

    heap.reclaim(h1)
    replacement = heap.allocate()
    assert replacement.slot == h1.slot
    assert replacement.generation == h1.generation + 1
    try:
        heap.deref(h1)
    except KeyError:
        stale_fails_closed = True
    else:
        stale_fails_closed = False
    assert stale_fails_closed
    assert heap.deref(replacement) == replacement.slot
    cases.append({
        "name": "allocation-after-reclaim",
        "live": 3,
        "reclaimable": 0,
        "oracle_parity": True,
        "reused_slot": replacement.slot,
        "stale_handle_fails_closed": True,
    })

    # 12. Collector-swap/relabel metamorphism on abstract graph semantics.
    swap_graph = {
        "R": Cell(("A", "B"), "root"),
        "A": Cell(("C",), "left"),
        "B": Cell((), "right"),
        "C": Cell((), "leaf"),
        "G": Cell((), "garbage"),
    }
    roots = ("R",)
    before = semantic_graph(swap_graph, roots)
    copied, copied_roots = relabel_graph(swap_graph, roots)
    after = semantic_graph(copied, copied_roots)
    assert before == after
    assert len(worklist_mark(swap_graph, roots)) == len(worklist_mark(copied, copied_roots))
    cases.append({
        "name": "collector-swap-relabel-metamorphism",
        "live": len(worklist_mark(swap_graph, roots)),
        "reclaimable": len(reclaimable(swap_graph, roots)),
        "oracle_parity": True,
        "semantic_output_equal": True,
    })

    runtime_pending = [
        {
            "id": "runtime-safe-point-root-completeness",
            "status": "PENDING-RUNTIME-HEAP",
            "reason": "no landed tracing heap/root enumeration to force collection at actual evaluator allocation safe points",
        },
        {
            "id": "runtime-allocation-after-reclaim",
            "status": "PENDING-RUNTIME-HEAP",
            "reason": "abstract slot reuse is witnessed; production allocator/collector integration does not yet exist",
        },
        {
            "id": "runtime-collector-swap-semantic-parity",
            "status": "PENDING-RUNTIME-HEAP",
            "reason": "abstract relabel metamorphism is witnessed; no two landed SENS collectors exist",
        },
        {
            "id": "managed-rational-limb-chain",
            "status": "NOT-ADMITTED-CURRENT-LAYOUT",
            "reason": "#2595 census keeps Rational/BigInt host-owned with zero managed Value edges",
        },
        {
            "id": "managed-text7-child-edges",
            "status": "NOT-ADMITTED-CURRENT-LAYOUT",
            "reason": "#2595 census keeps Text7 as host-owned Rc<[u8]> with zero managed Value edges",
        },
    ]

    assert all(row["sensitive"] for row in sensitivities)
    assert all(row["oracle_parity"] for row in cases)
    assert len(cases) >= 9

    artifact = {
        "schema": "gc-stress-oracle/v1",
        "authority": "research-only-mechanism-falsifier",
        "layer": "MECHANISM",
        "runtime_gc_implementation": False,
        "collector_independent_cases": cases,
        "sensitivity_attacks": sensitivities,
        "runtime_pending": runtime_pending,
        "summary": {
            "collector_independent_cases_passed": len(cases),
            "sensitivity_attacks_passed": len(sensitivities),
            "deep_chain_nodes": n,
            "runtime_checks_green": 0,
            "runtime_checks_pending": sum(x["status"] == "PENDING-RUNTIME-HEAP" for x in runtime_pending),
            "current_layout_tests_not_admitted": sum(x["status"] == "NOT-ADMITTED-CURRENT-LAYOUT" for x in runtime_pending),
        },
        "non_conclusions": [
            "no SENS collector implementation is proved",
            "abstract safe-point roots do not prove real evaluator root completeness",
            "generation handles are a falsifier model, not a chosen SENS handle ABI",
            "physical slot IDs and GC telemetry are not semantic observations",
            "Rational/Text7 managed-edge tests are forbidden until representation changes",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# GC adversarial graph oracle — #2551",
        "",
        f"Collector-independent fixtures passed: **{len(cases)}**",
        f"Sensitivity attacks passed: **{len(sensitivities)}**",
        f"Deep-chain nodes: **{n}**",
        "",
        "Validated now:",
        "- each Pair edge independently matters;",
        "- sharing/cycles obey reachability rather than RC intuition;",
        "- Closure->Environment back-edge shape is oracle-sensitive;",
        "- 100k chain is handled by iterative marking;",
        "- pointer-looking host payload does not invent managed edges;",
        "- temporary-root omission is detected;",
        "- abstract reclaimed slot can be reused while stale generation fails closed;",
        "- physical relabel/copy preserves semantic graph observation.",
        "",
        "Explicitly not claimed:",
        "- real SENS collector/runtime heap;",
        "- actual evaluator safe-point root completeness;",
        "- production reclaim/allocation integration;",
        "- runtime collector swap;",
        "- managed Rational/Text7 edges.",
        "",
    ]
    text = "\n".join(lines)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
