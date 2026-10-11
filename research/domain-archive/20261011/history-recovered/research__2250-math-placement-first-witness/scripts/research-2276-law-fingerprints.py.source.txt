#!/usr/bin/env python3
"""#2276: derive candidate math families from executable law fingerprints.

Names label observations only. Clustering keys are computed law facts.
UNKNOWN is not coerced to false in the output model.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import gcd, lcm
from collections import defaultdict, deque

Q = tuple(sorted({
    Fraction(n, d)
    for n in range(-4, 5)
    for d in range(1, 5)
}))
N0 = tuple(range(0, 9))


def total_binary(op, values):
    table = {}
    for a, b in product(values, repeat=2):
        try:
            table[(a, b)] = op(a, b)
        except (ZeroDivisionError, ValueError):
            table[(a, b)] = None
    return table


def law_fingerprint(op, values):
    table = total_binary(op, values)
    partial = any(v is None for v in table.values())

    commutative = all(
        table[(a, b)] == table[(b, a)]
        for a, b in product(values, repeat=2)
    )

    idempotent = all(
        table[(a, a)] == a
        for a in values
        if table[(a, a)] is not None
    )

    associative = True
    assoc_checked = 0
    for a, b, c in product(values, repeat=3):
        ab = table[(a, b)]
        bc = table[(b, c)]
        if ab is None or bc is None:
            continue
        try:
            left = op(ab, c)
            right = op(a, bc)
        except (ZeroDivisionError, ValueError):
            continue
        assoc_checked += 1
        if left != right:
            associative = False
            break

    return {
        "partial": partial,
        "commutative": commutative,
        "associative": associative,
        "idempotent": idempotent,
        "assoc_checked": assoc_checked,
    }


Q_BINARY = {
    "ADD": lambda a, b: a + b,
    "MUL": lambda a, b: a * b,
    "SUB": lambda a, b: a - b,
    "DIV": lambda a, b: a / b,
    "MIN": min,
    "MAX": max,
}

N_BINARY = {
    "GCD": gcd,
    "LCM": lcm,
}

PRED = {
    "LT": lambda a, b: a < b,
    "GT": lambda a, b: a > b,
    "LE": lambda a, b: a <= b,
    "GE": lambda a, b: a >= b,
    "EQ": lambda a, b: a == b,
    "NE": lambda a, b: a != b,
}


def predicate_signature(fn):
    return tuple(fn(a, b) for a, b in product(Q, repeat=2))


def transformed_predicate_signature(fn, swap=False, negate=False):
    out = []
    for a, b in product(Q, repeat=2):
        if swap:
            a, b = b, a
        value = fn(a, b)
        out.append(not value if negate else value)
    return tuple(out)


def predicate_action_graph():
    reverse = {predicate_signature(fn): name for name, fn in PRED.items()}
    edges = defaultdict(dict)
    for name, fn in PRED.items():
        for action, kwargs in (
            ("S", {"swap": True}),
            ("N", {"negate": True}),
        ):
            sig = transformed_predicate_signature(fn, **kwargs)
            edges[name][action] = reverse.get(sig, "OUTSIDE")
    return edges


def orbits(edges):
    seen = set()
    result = []
    for root in edges:
        if root in seen:
            continue
        q = deque([root])
        orbit = set()
        while q:
            node = q.popleft()
            if node in orbit or node == "OUTSIDE":
                continue
            orbit.add(node)
            for target in edges[node].values():
                if target not in orbit and target != "OUTSIDE":
                    q.append(target)
        seen |= orbit
        result.append(tuple(sorted(orbit)))
    return sorted(result)


def main():
    fingerprints = {}

    for name, op in Q_BINARY.items():
        fp = law_fingerprint(op, Q)
        fingerprints[name] = ("Q", "Q", fp)
        print(
            f"FP {name} carrier=Q codomain=Q "
            f"partial={int(fp['partial'])} "
            f"commutative={int(fp['commutative'])} "
            f"associative={int(fp['associative'])} "
            f"idempotent={int(fp['idempotent'])}"
        )

    for name, op in N_BINARY.items():
        fp = law_fingerprint(op, N0)
        fingerprints[name] = ("N0", "N0", fp)
        print(
            f"FP {name} carrier=N0 codomain=N0 "
            f"partial={int(fp['partial'])} "
            f"commutative={int(fp['commutative'])} "
            f"associative={int(fp['associative'])} "
            f"idempotent={int(fp['idempotent'])}"
        )

    # Role clustering deliberately ignores concrete carrier but preserves
    # partiality. This exposes cross-carrier law-isomorphism candidates.
    clusters = defaultdict(list)
    for name, (_, _, fp) in fingerprints.items():
        role_key = (
            fp["partial"],
            fp["commutative"],
            fp["associative"],
            fp["idempotent"],
        )
        clusters[role_key].append(name)

    print("ROLE-CLUSTERS:")
    for key, names in sorted(clusters.items(), key=lambda item: str(item[0])):
        print(f"  {key}: {','.join(sorted(names))}")

    add_mul_key = (
        False, True, True, False
    )
    lattice_key = (
        False, True, True, True
    )
    assert set(clusters[add_mul_key]) == {"ADD", "MUL"}
    assert set(clusters[lattice_key]) == {"MIN", "MAX", "GCD", "LCM"}

    edges = predicate_action_graph()
    print("PREDICATE-ACTIONS:")
    for name in sorted(edges):
        print(
            f"  {name}: S->{edges[name]['S']} N->{edges[name]['N']}"
        )

    found_orbits = orbits(edges)
    print("PREDICATE-ORBITS=" + ";".join(
        "{" + ",".join(orbit) + "}" for orbit in found_orbits
    ))
    assert set(found_orbits) == {
        ("GE", "GT", "LE", "LT"),
        ("EQ", "NE"),
    }

    print("STATUS=PASS-LAW-FINGERPRINT-FAMILY-RECOVERY")
    print("WARNING=FINGERPRINT-EQUALITY-IS-CANDIDATE-ROLE-NOT-SEMANTIC-IDENTITY")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
