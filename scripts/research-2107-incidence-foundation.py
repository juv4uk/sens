#!/usr/bin/env python3
"""#2107 incidence/orientation foundation witness.

Research-only.  The goal is to expose hidden structure in the notation
R subset C x C.

We compare:
D: points only
I: undirected incidence
O: directed incidence
L: labeled directed incidence

Semantic comparison is by isomorphism, never by host token names.
"""

from __future__ import annotations

from itertools import permutations
from dataclasses import dataclass


@dataclass(frozen=True)
class UGraph:
    nodes: frozenset[str]
    edges: frozenset[frozenset[str]]


@dataclass(frozen=True)
class DGraph:
    nodes: frozenset[str]
    edges: frozenset[tuple[str, str]]


@dataclass(frozen=True)
class LGraph:
    nodes: frozenset[str]
    edges: frozenset[tuple[str, str, str]]


def bijections(xs, ys):
    xs = tuple(sorted(xs))
    ys = tuple(sorted(ys))
    if len(xs) != len(ys):
        return
    for perm in permutations(ys):
        yield dict(zip(xs, perm))


def iso_u(g: UGraph, h: UGraph) -> bool:
    if len(g.nodes) != len(h.nodes) or len(g.edges) != len(h.edges):
        return False
    for f in bijections(g.nodes, h.nodes):
        mapped = frozenset(frozenset((f[x] for x in e)) for e in g.edges)
        if mapped == h.edges:
            return True
    return False


def iso_d(g: DGraph, h: DGraph) -> bool:
    if len(g.nodes) != len(h.nodes) or len(g.edges) != len(h.edges):
        return False
    for f in bijections(g.nodes, h.nodes):
        mapped = frozenset((f[a], f[b]) for a, b in g.edges)
        if mapped == h.edges:
            return True
    return False


def iso_l(
    g: LGraph,
    h: LGraph,
    *,
    allow_label_renaming: bool,
) -> bool:
    if len(g.nodes) != len(h.nodes) or len(g.edges) != len(h.edges):
        return False

    glabels = {lab for _, _, lab in g.edges}
    hlabels = {lab for _, _, lab in h.edges}
    label_maps = [dict((x, x) for x in glabels)]
    if allow_label_renaming:
        label_maps = list(bijections(glabels, hlabels))
    elif glabels != hlabels:
        return False

    for f in bijections(g.nodes, h.nodes):
        for lf in label_maps:
            mapped = frozenset((f[a], f[b], lf[lab]) for a, b, lab in g.edges)
            if mapped == h.edges:
                return True
    return False


def underlying(g: DGraph) -> UGraph:
    return UGraph(
        g.nodes,
        frozenset(frozenset((a, b)) for a, b in g.edges),
    )


def degree_signature(g: DGraph):
    indeg = {n: 0 for n in g.nodes}
    outdeg = {n: 0 for n in g.nodes}
    for a, b in g.edges:
        outdeg[a] += 1
        indeg[b] += 1
    return sorted((indeg[n], outdeg[n]) for n in g.nodes)


def rename_directed(g: DGraph, mapping: dict[str, str]) -> DGraph:
    return DGraph(
        frozenset(mapping[n] for n in g.nodes),
        frozenset((mapping[a], mapping[b]) for a, b in g.edges),
    )


def main():
    nodes = frozenset({"a", "b", "c"})

    # I: same undirected incidence.
    inc = UGraph(
        nodes,
        frozenset({
            frozenset({"a", "b"}),
            frozenset({"a", "c"}),
        }),
    )

    # O: two different orientations of exactly the same incidence.
    out_star = DGraph(
        nodes,
        frozenset({
            ("a", "b"),
            ("a", "c"),
        }),
    )
    in_star = DGraph(
        nodes,
        frozenset({
            ("b", "a"),
            ("c", "a"),
        }),
    )

    assert underlying(out_star) == inc
    assert underlying(in_star) == inc
    assert iso_u(underlying(out_star), underlying(in_star))

    # Direction adds structure: these orientations are not direction-preserving
    # isomorphic. Their (in,out)-degree signatures differ.
    assert degree_signature(out_star) != degree_signature(in_star)
    assert not iso_d(out_star, in_star)

    # Node-token renaming is semantically irrelevant.
    ren = {"a": "x", "b": "z", "c": "y"}
    renamed = rename_directed(out_star, ren)
    assert out_star != renamed  # host/token representation differs
    assert iso_d(out_star, renamed)  # directed structure does not

    # L: labels add another independent layer.
    labeled = LGraph(
        nodes,
        frozenset({
            ("a", "b", "left"),
            ("a", "c", "right"),
        }),
    )
    label_renamed = LGraph(
        frozenset({"x", "y", "z"}),
        frozenset({
            ("x", "z", "alpha"),
            ("x", "y", "beta"),
        }),
    )

    # Consistent relabeling of both nodes and relation kinds preserves structure.
    assert iso_l(labeled, label_renamed, allow_label_renaming=True)
    assert not iso_l(labeled, label_renamed, allow_label_renaming=False)

    # Retyping two distinct relation roles into one collapses information even
    # though node incidence/orientation stays the same.
    collapsed_labels = LGraph(
        nodes,
        frozenset({
            ("a", "b", "same"),
            ("a", "c", "same"),
        }),
    )
    assert DGraph(
        labeled.nodes,
        frozenset((a, b) for a, b, _ in labeled.edges),
    ) == DGraph(
        collapsed_labels.nodes,
        frozenset((a, b) for a, b, _ in collapsed_labels.edges),
    )
    assert not iso_l(labeled, collapsed_labels, allow_label_renaming=True)

    print("D / POINTS")
    print("host node tokens are not semantic: rename changes tokens, not isomorphism class")
    print()

    print("I / INCIDENCE")
    print("underlying undirected edges:", sorted(map(sorted, inc.edges)))
    print("out-star and in-star share identical undirected incidence: YES")
    print()

    print("O / ORIENTATION")
    print("out-star degree signature:", degree_signature(out_star))
    print("in-star degree signature: ", degree_signature(in_star))
    print("direction-preserving isomorphic:", iso_d(out_star, in_star))
    print("result: orientation is extra structure beyond incidence")
    print()

    print("L / RELATION TYPES")
    print("consistent label renaming preserves typed structure: YES")
    print("collapsing two relation kinds into one preserves directed edges but loses typed structure: YES")
    print()

    print("FOUNDATIONAL CLASSIFICATION")
    print("node token identity       -> mechanism / gauge under graph isomorphism")
    print("distinguishable points    -> assumed by finite executable representation")
    print("incidence                 -> extra structure over points")
    print("orientation               -> extra structure over incidence")
    print("relation typing/labels    -> extra structure over orientation")
    print()
    print("PASS: R subset CxC is not assumption-free; it packages distinction + incidence + orientation.")
    print("A relation foundation must state which of those are primitive and which are quotiented by isomorphism.")


if __name__ == "__main__":
    main()
