#!/usr/bin/env python3
"""#2395 — factor current D4 UNKNOWN bootstrap functions by dependency SCC.

Research only. This script is an attack-planning tool, not semantic authority.

Inputs:
- knowledge/function-status-census.json
- lib/core1.lisp

It extracts real top-level C1 definitions, builds a dependency graph among the
current D4 bootstrap concepts, computes SCCs, and emits an attack class.

SCC membership is NOT a semantic-fact count and never promotes root/generated.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "knowledge" / "function-status-census.json"
CORE1 = ROOT / "lib" / "core1.lisp"

BOOTSTRAP = {
    "APPLY": "C1-APPLY",
    "EVAL": "C1-EVAL",
    "EVCON": "C1-EVCON",
    "EVLIS": "C1-EVLIS",
    "LOOKUP": "C1-LOOKUP",
    "BIND": "C1-BIND",
}

# Helper definitions that belong to one admitted concept's implementation.
HELPER_OWNER = {
    "C1-LOOKUP-IN": "LOOKUP",
}

DEFINE_PREFIX = "(00001001 "


def strip_comments(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())


def extract_top_level_definitions(text: str) -> dict[str, str]:
    """Extract balanced top-level forms that begin with (00001001 NAME ...)."""
    clean = strip_comments(text)
    defs: dict[str, str] = {}
    i = 0
    n = len(clean)

    while i < n:
        start = clean.find(DEFINE_PREFIX, i)
        if start < 0:
            break

        # Only accept if the form starts at top-level: count balance before start.
        # For this file, prior forms are balanced; this also protects against a
        # nested literal accidentally matching the marker.
        if clean[:start].count("(") != clean[:start].count(")"):
            i = start + 1
            continue

        name_start = start + len(DEFINE_PREFIX)
        name_end = name_start
        while name_end < n and not clean[name_end].isspace() and clean[name_end] not in "()":
            name_end += 1
        name = clean[name_start:name_end]

        depth = 0
        end = start
        while end < n:
            ch = clean[end]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1

        assert depth == 0, f"unbalanced definition for {name}"
        defs[name] = clean[start:end]
        i = end

    return defs


def current_unknown_labels() -> set[str]:
    data = json.loads(CENSUS.read_text(encoding="utf-8"))
    rows = data["rows"]
    return {
        row["human_surface_optional"]
        for row in rows
        if row["status"] == "UNKNOWN" and row["human_surface_optional"]
    }


def word_reference_counts(body: str, names: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in re.findall(r"\bC1-[A-Z0-9?-]+\b", body):
        if token in names:
            counts[token] = counts.get(token, 0) + 1
    return counts


def build_graph(defs: dict[str, str]) -> tuple[dict[str, set[str]], dict[str, bool], dict[str, list[str]]]:
    reverse = {impl: semantic for semantic, impl in BOOTSTRAP.items()}
    known_impls = set(reverse) | set(HELPER_OWNER)

    graph: dict[str, set[str]] = {name: set() for name in BOOTSTRAP}
    self_recursive: dict[str, bool] = {name: False for name in BOOTSTRAP}
    evidence: dict[str, list[str]] = {name: [] for name in BOOTSTRAP}

    for semantic, impl in BOOTSTRAP.items():
        assert impl in defs, f"missing current Core1 definition: {impl}"
        bodies = [defs[impl]]
        helpers = [h for h, owner in HELPER_OWNER.items() if owner == semantic]
        for helper in helpers:
            assert helper in defs, f"missing helper: {helper}"
            bodies.append(defs[helper])

        ref_counts: dict[str, int] = {}
        for body_name, body in [(impl, defs[impl])] + [
            (helper, defs[helper]) for helper in helpers
        ]:
            counts = word_reference_counts(body, known_impls)
            # One occurrence is the top-level definition header, not a call.
            if body_name in counts:
                counts[body_name] -= 1
                if counts[body_name] == 0:
                    del counts[body_name]
            for ref, count in counts.items():
                ref_counts[ref] = ref_counts.get(ref, 0) + count

        refs = set(ref_counts)
        for ref in sorted(refs):
            if ref in HELPER_OWNER:
                target = HELPER_OWNER[ref]
            else:
                target = reverse[ref]

            if target == semantic:
                self_recursive[semantic] = True
            else:
                graph[semantic].add(target)

        evidence[semantic] = sorted(refs)

    return graph, self_recursive, evidence


def tarjan(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    components: list[tuple[str, ...]] = []

    def visit(v: str) -> None:
        nonlocal index
        indices[v] = index
        low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        for w in sorted(graph[v]):
            if w not in indices:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])

        if low[v] == indices[v]:
            members = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                members.append(w)
                if w == v:
                    break
            components.append(tuple(sorted(members)))

    for v in sorted(graph):
        if v not in indices:
            visit(v)

    return sorted(components, key=lambda c: (len(c), c))


def attack_class(name: str, component: tuple[str, ...], self_recursive: bool) -> str:
    if len(component) > 1:
        return "joint-fixed-point-attack"
    if self_recursive:
        return "structural-recursion-attack"
    if name == "APPLY":
        return "acyclic-dispatch-attack"
    return "acyclic-dependency-attack"


def main() -> None:
    unknown = current_unknown_labels()
    for semantic in BOOTSTRAP:
        assert semantic in unknown, f"{semantic} is no longer UNKNOWN; refresh #2395"

    defs = extract_top_level_definitions(CORE1.read_text(encoding="utf-8"))
    graph, self_recursive, evidence = build_graph(defs)
    components = tarjan(graph)
    comp_of = {member: comp for comp in components for member in comp}

    # Critical current-source controls.
    evaluator_scc = comp_of["EVAL"]
    assert set(evaluator_scc) == {"EVAL", "EVCON", "EVLIS"}, evaluator_scc
    assert comp_of["APPLY"] == ("APPLY",)
    assert "APPLY" in graph["EVAL"]
    assert "EVAL" not in graph["APPLY"]
    assert not self_recursive["APPLY"]
    assert self_recursive["BIND"]
    assert self_recursive["LOOKUP"]

    print("BOOTSTRAP-DEPENDENCY-GRAPH:")
    for name in sorted(BOOTSTRAP):
        comp = comp_of[name]
        deps = ",".join(sorted(graph[name])) or "-"
        refs = ",".join(evidence[name]) or "-"
        print(
            f"node={name} "
            f"status=UNKNOWN "
            f"deps={deps} "
            f"self_recursive={int(self_recursive[name])} "
            f"scc={'+'.join(comp)} "
            f"scc_size={len(comp)} "
            f"attack={attack_class(name, comp, self_recursive[name])} "
            f"refs={refs}"
        )

    print("SCCS:")
    for comp in components:
        print("  " + "+".join(comp))

    print("EXPECTED-EVALUATOR-SCC=EVAL+EVCON+EVLIS")
    print("APPLY-IN-EVALUATOR-SCC=0")
    print("APPLY-SELF-RECURSIVE=0")
    print("BIND-SELF-RECURSIVE=1")
    print("LOOKUP-SELF-RECURSIVE=1")
    print("SEMANTIC-PROMOTIONS=0")
    print("RULE=SCC-GUIDES-INDEPENDENCE-ATTACK-NOT-FACT-COUNT")
    print("STATUS=PASS-BOOTSTRAP-SCC-FACTOR")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
