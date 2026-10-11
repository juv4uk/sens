#!/usr/bin/env python3
"""Cross-check finite Horn abduction against ATMS-style assumption-label propagation.

This is a research oracle only, not an implementation of the SENS runtime.
The test compares two different algorithms:
  * powerset enumeration + least fixed-point Horn closure;
  * minimal-label propagation through Horn justifications, followed by nogood filtering.
"""
from __future__ import annotations

from itertools import combinations, product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-abductive-minimal-explanations-v1.json"
ATOMS = ("a", "b", "g")


def add_minimal(family: set[frozenset[str]], candidate: frozenset[str]) -> bool:
    """Insert candidate iff it improves the inclusion-minimal antichain."""
    if any(existing <= candidate for existing in family):
        return False
    supersets = {existing for existing in family if candidate < existing}
    family.difference_update(supersets)
    family.add(candidate)
    return True


def antichain(items):
    result: set[frozenset[str]] = set()
    for item in items:
        add_minimal(result, frozenset(item))
    return result


def canonical(family):
    return [list(item) for item in sorted(
        (tuple(sorted(x)) for x in family), key=lambda x: (len(x), x)
    )]


def powerset_reference(case: dict):
    """Small specification oracle: enumerate every allowed assumption subset."""
    abducibles = sorted(set(case["abducibles"]))
    accepted: list[frozenset[str]] = []
    for mask in range(1 << len(abducibles)):
        hypothesis = frozenset(
            atom for i, atom in enumerate(abducibles) if mask & (1 << i)
        )
        closure = set(case["facts"]) | set(hypothesis)
        changed = True
        while changed:
            changed = False
            for rule in case["rules"]:
                if set(rule["body"]) <= closure and rule["head"] not in closure:
                    closure.add(rule["head"])
                    changed = True
        if case["goal"] not in closure:
            continue
        if any(set(bad) <= closure for bad in case["integrity_constraints"]):
            continue
        accepted.append(hypothesis)
    minimal = [
        x for x in accepted
        if not any(y < x for y in accepted)
    ]
    return canonical(set(minimal))


def atms_labels(case: dict):
    """Compute subset-minimal assumption labels by finite Horn label propagation."""
    supports: dict[str, set[frozenset[str]]] = {}

    def labels(atom: str) -> set[frozenset[str]]:
        return supports.setdefault(atom, set())

    # Facts have unconditional support; an abducible may be hypothesized.
    for atom in case["facts"]:
        add_minimal(labels(atom), frozenset())
    for atom in case["abducibles"]:
        add_minimal(labels(atom), frozenset({atom}))

    # Each Horn rule combines one support label for each antecedent.
    changed = True
    while changed:
        changed = False
        for rule in case["rules"]:
            body_families = [labels(atom) for atom in rule["body"]]
            if any(not family for family in body_families):
                continue
            for chosen in product(*body_families):
                joined = frozenset().union(*chosen)
                if add_minimal(labels(rule["head"]), joined):
                    changed = True
            # product(*[]) yields one empty choice for an unconditional rule.

    # Convert forbidden conjunctions into assumption nogoods. A forbidden
    # conjunction is reachable under a hypothesis iff a support label for each
    # atom can be combined into a subset of that hypothesis.
    nogoods: set[frozenset[str]] = set()
    for forbidden in case["integrity_constraints"]:
        body_families = [labels(atom) for atom in forbidden]
        if any(not family for family in body_families):
            continue
        for chosen in product(*body_families):
            joined = frozenset().union(*chosen)
            add_minimal(nogoods, joined)

    coherent_goal_labels = {
        label for label in labels(case["goal"])
        if not any(nogood <= label for nogood in nogoods)
    }
    return canonical(antichain(coherent_goal_labels))


def fixture_cases():
    data = json.loads(DOSSIER.read_text(encoding="utf-8"))
    return data["oracle"]["cases"]


def exhaustive_small_cases():
    """Exhaust all 16,704 tiny theories in a 3-atom, <=2-rule fragment."""
    bodies = [
        subset for size in range(0, len(ATOMS))
        for subset in combinations(ATOMS, size)
    ]
    rule_pool = [
        {"head": head, "body": list(body)}
        for head in ATOMS for body in bodies
    ]
    rule_sets = [()]
    rule_sets.extend((rule,) for rule in rule_pool)
    rule_sets.extend(combinations(rule_pool, 2))
    abducible_sets = [
        tuple(atom for i, atom in enumerate(ATOMS) if mask & (1 << i))
        for mask in range(1 << len(ATOMS))
    ]
    fact_sets = ((), ("a",), ("b",))
    constraint_sets = ((), (("a",),), (("a", "b"),))
    for rules in rule_sets:
        for abducibles in abducible_sets:
            for facts in fact_sets:
                for constraints in constraint_sets:
                    yield {
                        "facts": list(facts),
                        "rules": [
                            {"head": row["head"], "body": list(row["body"])}
                            for row in rules
                        ],
                        "abducibles": list(abducibles),
                        "integrity_constraints": [list(c) for c in constraints],
                        "goal": "g",
                    }


def main() -> None:
    fixtures = fixture_cases()
    for case in fixtures:
        expected = case["expected"]
        reference = powerset_reference(case)
        propagated = atms_labels(case)
        assert reference == expected, (case["id"], "fixture/reference", reference, expected)
        assert propagated == reference, (case["id"], "fixture/ATMS", propagated, reference)

    generated_count = 0
    for case in exhaustive_small_cases():
        reference = powerset_reference(case)
        propagated = atms_labels(case)
        assert propagated == reference, {
            "case_index": generated_count,
            "case": case,
            "reference": reference,
            "atms": propagated,
        }
        generated_count += 1

    print(
        "ATMS reduction PASS:",
        len(fixtures),
        "named fixtures +",
        generated_count,
        "exhaustive tiny Horn theories; powerset and support-label outputs agree",
    )


if __name__ == "__main__":
    main()
