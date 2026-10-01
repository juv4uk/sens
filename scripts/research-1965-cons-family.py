#!/usr/bin/env python3
"""#1965 research-only bounded falsifier for the CONS seed family.

Question: does the current Lisp I/Lisp 1.5 corpus provide a compact fixed local
binary action for CONS comparable to the proven CAR/CDR selector subtree?

This script does NOT prove impossibility. It reports whether the bounded corpus
currently contains that level of evidence. A negative result means "leave the
branch unallocated under the strong-semantic criterion", not "CONS can never
have descendants".
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGES = ROOT / "docs/research/1962-lisp1-15-edges.tsv"

SEED = {"nil", "quote", "atom", "eq", "cons", "car", "cdr", "cond"}
SELECTOR_CONTROL = ("caar", "cadr", "cddr")
CONS_CANDIDATES = ("list", "append", "pair_lisp1", "pairlis_lisp15")


def read_edges():
    with EDGES.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def direct(rows, source):
    return [
        row for row in rows
        if row["source"] == source and row["rank_edge"] == "1"
    ]


def non_recursive_targets(rows, source):
    return {
        row["target"] for row in direct(rows, source)
        if row["relation"] != "recursion"
    }


def relation_kinds(rows, source):
    return {
        row["relation"] for row in direct(rows, source)
    }


def seed_support(rows):
    nodes = set(SEED)
    for row in rows:
        nodes.add(row["source"])
        nodes.add(row["target"])

    support = {node: ({node} if node in SEED else set()) for node in nodes}

    changed = True
    while changed:
        changed = False
        for row in rows:
            if row["rank_edge"] != "1":
                continue
            source = row["source"]
            target = row["target"]
            if source == target and row["relation"] == "recursion":
                continue
            merged = support[source] | support[target]
            if merged != support[source]:
                support[source] = merged
                changed = True
    return support


def main():
    rows = read_edges()
    support = seed_support(rows)

    # Positive control: selector family is represented by ordered composition
    # edges over CAR/CDR rather than a heterogeneous helper graph.
    for name in SELECTOR_CONTROL:
        kinds = relation_kinds(rows, name)
        assert kinds <= {"composition"}, (name, kinds)
        deps = non_recursive_targets(rows, name)
        assert deps <= {"car", "cdr"}, (name, deps)

    observed = {
        name: (
            non_recursive_targets(rows, name),
            relation_kinds(rows, name),
            support.get(name, set()),
        )
        for name in CONS_CANDIDATES
    }

    # Pin the bounded primary-source corpus so future edits make the research
    # conclusion visibly re-evaluate instead of drifting silently.
    assert observed["list"][0] == {"cons", "nil"}
    assert observed["list"][1] == {"composition", "structure"}

    assert {"null", "cons", "car", "cdr", "cond"} <= observed["append"][0]
    assert "recursion" in observed["append"][1]

    assert {"null", "atom", "cons", "list", "car", "cdr", "cond"} <= observed["pair_lisp1"][0]
    assert "recursion" in observed["pair_lisp1"][1]

    assert {"null", "cons", "car", "cdr", "cond"} <= observed["pairlis_lisp15"][0]
    assert "recursion" in observed["pairlis_lisp15"][1]

    print("positive-control selector family")
    for name in SELECTOR_CONTROL:
        print(
            f"{name}\tdirect={','.join(sorted(non_recursive_targets(rows, name)))}"
            f"\trelations={','.join(sorted(relation_kinds(rows, name)))}"
        )

    print("\nCONS-family bounded candidates")
    for name in CONS_CANDIDATES:
        deps, kinds, seeds = observed[name]
        print(
            f"{name}\tdirect={','.join(sorted(deps))}"
            f"\trelations={','.join(sorted(kinds))}"
            f"\tseed-support={','.join(sorted(seeds))}"
        )

    print("\nRESULT")
    print("No CONS candidate in the bounded corpus currently has the same evidence shape")
    print("as the CAR/CDR strong-semantic control. LIST needs CONS+NIL and changes arity;")
    print("APPEND/PAIR/PAIRLIS combine multiple roots, control and/or recursion.")
    print("Classification for now: CONS branch is not proven strong-semantic.")
    print("Action: leave children unallocated unless a smaller reusable generator law is found.")
    print("This is a bounded negative result, not a proof that no future CONS-family law exists.")


if __name__ == "__main__":
    main()
