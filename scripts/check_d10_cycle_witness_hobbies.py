#!/usr/bin/env python3
"""Independent exact cycle-witness oracles for a proposed D10 graph law.

This is pure bounded mathematical research; no SENS runtime/ratification proof.
No third-party dependency: a DFS enumerator is compared to full permutations.
"""
from __future__ import annotations

import itertools
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER_PATH = "knowledge/d10-canonical-directed-cycle-witness-research-v1.json"
NAME = "CANONICAL-DIRECTED-CYCLE-WITNESS"
EXPECTED_SOURCES = {
    "juv4uk/knowledge-graph-basalt:src/lib/bases.ts": "1bda7dd7a7c04fc7636d2ab90ed2250087af9eb7",
    "juv4uk/knowledge-graph-basalt:src/lib/bases.test.ts": "42b0cd2b54ba8f352e29dedb28b5dc0c752ac249",
    "juv4uk/sens:lib/meta-eval.lisp": "7d3289001cece9ba5997ae7dd7d7d6f65edaf2a6",
    "juv4uk/shiva-sutras:RESEARCH_MAP.md": "763bf48a7ff890ca6947707f16d98bea605f97c1",
}


class ProofFailure(Exception):
    pass


def require(ok, why):
    if not ok:
        raise ProofFailure(why)


def adjacency(vertices, edges):
    """Validate finite graph, retain only edge SET semantics."""
    v = list(vertices)
    require(len(set(v)) == len(v), "duplicate vertices")
    require(all(type(x) is int and x >= 0 for x in v), "vertex identity must be nonnegative integer")
    vset = set(v)
    out = {u: set() for u in v}
    for edge in edges:
        require(len(edge) == 2, "edge not a directed pair")
        u, w = edge
        require(u in vset and w in vset, "unknown edge endpoint")
        out[u].add(w)
    return out


def rotation_normalize(cycle):
    require(cycle and len(set(cycle)) == len(cycle), "non-elementary cycle")
    k = cycle.index(min(cycle))
    return tuple(cycle[k:] + cycle[:k])


def dfs_reference(vertices, edges):
    """Enumerate elementary directed cycles via visiting sorted neighbors."""
    graph = adjacency(vertices, edges)
    solutions = set()

    def visit(start, curr, seen, path):
        if curr == start:
            solutions.add(rotation_normalize(path))
            return
        if curr in seen:
            return
        newseen = seen | {curr}
        for nxt in sorted(graph[curr]):
            # Closing is allowed only after one or more distinct visited nodes.
            visit(start, nxt, newseen, path + [curr])

    for start in sorted(graph):
        for nxt in sorted(graph[start]):
            visit(start, nxt, {start}, [start])
    return min(solutions) if solutions else None


def permutation_oracle(vertices, edges):
    """Independent exhaustive reference: enumerate ordered subsets of vertices."""
    graph = adjacency(vertices, edges)
    vs = sorted(graph)
    best = None
    for length in range(1, len(vs) + 1):
        for nodes in itertools.permutations(vs, length):
            if all(nodes[(i + 1) % length] in graph[nodes[i]]
                   for i in range(length)):
                cycle = rotation_normalize(list(nodes))
                if best is None or cycle < best:
                    best = cycle
    return best


def verify_dossier(dossier, inventory):
    ident = dossier.get("identity") or {}
    basis = dossier.get("basis") or {}
    require(dossier.get("schema") == "d10-canonical-directed-cycle-witness-research/v1",
            "invalid dossier schema")
    require(dossier.get("status") == "RESEARCH-HOLD-LIBRARY-OR-CORE-REVIEW",
            "fake source-level selection")
    require(ident.get("semantic_name") == NAME, "candidate identity drift")
    require(ident.get("status") == "HOLD-CORE-LIBRARY-DERIVABILITY", "library derivability gate bypass")
    require(ident.get("decision") == "RESEARCH-NOT-SELECTED", "candidate selected without evidence")
    require(ident.get("coordinate") is None, "unproved coordinate")
    require(ident.get("ratified_resident") is False, "unapproved ratification")
    require(ident.get("physical_t5_authorized") is False, "invented physical T5 authority")
    require(len(ident.get("positive_witnesses", [])) >= 5, "lost positive witnesses")
    require(len(ident.get("falsifiers", [])) >= 6, "lost falsifiers")
    require(ident.get("dedup", {}).get("core_root_independence", "").startswith("Unproved."),
            "derivability incorrectly claimed")
    require(basis.get("selected_added") == basis.get("D10_ratified_added") == 
            basis.get("coordinates_added") == 0, "dossier illegally grows D10")
    require(len(inventory["rows"]) >= basis.get("baseline_selected_at_research", 99999),
            "historical inventory erased")
    require(inventory["accounting"]["ratified_d10_residents"] == 0, "owner gate changed")
    require(NAME not in {r["semantic_name"] for r in inventory["rows"]},
            "separate research candidate was silently selected")
    donors = dossier.get("donor_evidence") or []
    require(len(donors) == len(EXPECTED_SOURCES), "missing source evidence")
    seen = set()
    for donor in donors:
        key = donor["repo"] + ":" + donor["path"]
        require(key not in seen, "duplicate donor evidence")
        seen.add(key)
        require(EXPECTED_SOURCES.get(key) == donor["git_blob_sha"],
                "wrong or invented donor Git blob SHA: " + key)
        require(bool(donor.get("actual_law")) and donor.get("line", 0) > 0,
                "missing donor scope or line")
    for record in ident["positive_witnesses"]:
        obtained = dfs_reference(record["vertices"], record["edges"])
        expected = None if record["expected"] is None else tuple(record["expected"])
        require(obtained == expected, "dossier witness contradicted: " + str(record))
    return True


def differential_suite():
    # 2^(3*3) = 512 different finite directed graphs incl all loops.
    count = 0
    for n in (0, 1, 2, 3):
        edges = [(i, j) for i in range(n) for j in range(n)]
        for mask in range(1 << len(edges)):
            actual = [edge for i, edge in enumerate(edges) if (mask >> i) & 1]
            got = dfs_reference(list(range(n)), actual)
            want = permutation_oracle(list(range(n)), actual)
            require(got == want, "full graph exhaustive difference n=" + str(n))
            count += 1
    # Additional 4096 deterministic directed 4-node graphs with orientation changes.
    rng = random.Random(20261009)
    edges = [(i, j) for i in range(4) for j in range(4)]
    for _ in range(4096):
        mask = rng.getrandbits(16)
        actual = [edge for i, edge in enumerate(edges) if (mask >> i) & 1]
        got = dfs_reference(list(range(4)), actual)
        want = permutation_oracle(list(range(4)), actual)
        require(got == want, "bounded randomized graph proof mismatch")
        # Ordering of input vertices and edge tuples cannot affect result.
        rng.shuffle(actual)
        require(dfs_reference([3, 0, 2, 1], actual) == want, "non-deterministic order")
        count += 1
    require(count == (1 + 2 + 16 + 512 + 4096), "unexpected differential corpus size")
    # Orientation is semantically meaningful.
    require(dfs_reference([0,1,2],[(0,1),(1,2),(2,0)]) == (0,1,2),
            "correct oriented triangular witness missing")
    require(dfs_reference([0,1,2],[(1,0),(2,1),(2,0)]) is None,
            "reverse orientation silently identified")
    # Valid independent self-loop.
    require(dfs_reference([0,1],[(1,1)]) == (1,), "self-loop suppressed")
    for bad_vertices, bad_edges in (([0,0],[]),([0],[(0,1)]),([-1],[])):
        try:
            dfs_reference(bad_vertices,bad_edges)
        except ProofFailure:
            continue
        raise ProofFailure("invalid graph admitted")
    return count


def negative_controls(dossier, inv):
    import copy
    tests = [
      ("forged coordinate", lambda a: a["identity"].update(coordinate="0000000000")),
      ("claimed ratification", lambda a: a["identity"].update(ratified_resident=True)),
      ("claimed D10 selection", lambda a: a["identity"].update(decision="SELECTED")),
      ("invented T5 authorization", lambda a: a["identity"].update(physical_t5_authorized=True)),
      ("drop source", lambda a: a["donor_evidence"].pop()),
      ("forge source blob", lambda a: a["donor_evidence"][0].update(git_blob_sha="0"*40)),
      ("erase falsifiers", lambda a: a["identity"].update(falsifiers=[])),
      ("claim irreducibility", lambda a: a["identity"]["dedup"].update(core_root_independence="PROVED")),
      ("wrong selected count", lambda a: a["basis"].update(selected_added=1)),
    ]
    for label, update in tests:
        mutated = copy.deepcopy(dossier)
        update(mutated)
        try:
            verify_dossier(mutated, inv)
        except ProofFailure:
            continue
        raise ProofFailure("negative control escaped: " + label)
    return len(tests)


if __name__ == "__main__":
    dossier = json.loads((ROOT / DOSSIER_PATH).read_text(encoding="utf-8"))
    inv = json.loads((ROOT / "knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
    try:
        verify_dossier(dossier, inv)
        checked = differential_suite()
        forged = negative_controls(dossier, inv)
        print("D10-CANONICAL-CYCLE: PASS independent_oracles=" + str(checked)
              + " negative_mutations=" + str(forged)
              + " selected_delta=0, ratified_delta=0, physical_T5=0")
    except ProofFailure as exc:
        print("D10-CANONICAL-CYCLE: FAIL " + str(exc), file=sys.stderr)
        sys.exit(1)
