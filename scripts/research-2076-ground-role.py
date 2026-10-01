#!/usr/bin/env python3
"""#2076 ground-role isomorphism witness.

Research-only. Tests whether the structural value algebra distinguishes the
*particular* ground representative, or only a zero-arity ground role.

Two worlds differ only in which opaque token plays ground:
  M0 ground = g0
  M1 ground = g1

A recursive bijection maps g0->g1 and preserves atoms, pairs and predicate bits.

If every operation in the modeled structural signature commutes with that
bijection, then the structural laws characterize ground only up to isomorphism.
This does not rule out reader/evaluator/owner laws that pin exact () elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

ERR = object()
YES = ("bool", 1)
NO = ("bool", 0)


@dataclass(frozen=True)
class World:
    tag: str
    eq_ground_policy: str  # "not-admitted" | "admitted-reflexive"

    @property
    def ground(self):
        return ("ground", self.tag)

    def atom(self, name: str):
        return ("atom", name)

    def pair(self, x, y):
        return ("pair", x, y)

    def is_pair(self, v):
        return isinstance(v, tuple) and len(v) == 3 and v[0] == "pair"

    def make_pair(self, x, y):
        if x is ERR or y is ERR:
            return ERR
        return self.pair(x, y)

    def left(self, v):
        return v[1] if self.is_pair(v) else ERR

    def right(self, v):
        return v[2] if self.is_pair(v) else ERR

    def atom_class(self, v):
        if v is ERR or v in (YES, NO):
            return ERR
        return NO if self.is_pair(v) else YES

    def atom_identity(self, x, y):
        if x is ERR or y is ERR:
            return ERR
        if self.is_pair(x) or self.is_pair(y) or x in (YES, NO) or y in (YES, NO):
            return ERR

        gx = x == self.ground
        gy = y == self.ground
        if self.eq_ground_policy == "not-admitted" and (gx or gy):
            return ERR
        return YES if x == y else NO

    def lisp_list(self, *items):
        out = self.ground
        for item in reversed(items):
            out = self.pair(item, out)
        return out


def map_value(v, src: World, dst: World):
    if v is ERR:
        return ERR
    if v in (YES, NO):
        return v
    if v == src.ground:
        return dst.ground
    if isinstance(v, tuple) and len(v) == 2 and v[0] == "atom":
        return dst.atom(v[1])
    if src.is_pair(v):
        return dst.pair(
            map_value(v[1], src, dst),
            map_value(v[2], src, dst),
        )
    raise AssertionError(("unmapped", v))


def finite_values(w: World):
    atoms = [w.ground, w.atom("a"), w.atom("b")]
    pairs1 = [w.pair(x, y) for x, y in product(atoms, repeat=2)]
    # Include a few nested pairs/proper lists, enough to exercise recursive map.
    nested = [
        w.pair(pairs1[0], w.atom("a")),
        w.pair(w.atom("b"), pairs1[-1]),
        w.lisp_list(w.atom("a"), w.atom("b")),
    ]
    return tuple(atoms + pairs1 + nested)


def commute_unary(name, op0, op1, values, w0, w1):
    checked = 0
    for x in values:
        lhs = map_value(op0(x), w0, w1)
        rhs = op1(map_value(x, w0, w1))
        assert lhs == rhs, (name, x, lhs, rhs)
        checked += 1
    return checked


def commute_binary(name, op0, op1, values, w0, w1):
    checked = 0
    for x, y in product(values, repeat=2):
        lhs = map_value(op0(x, y), w0, w1)
        rhs = op1(map_value(x, w0, w1), map_value(y, w0, w1))
        assert lhs == rhs, (name, x, y, lhs, rhs)
        checked += 1
    return checked


def check_policy(policy: str):
    w0 = World("g0", policy)
    w1 = World("g1", policy)
    values = finite_values(w0)

    # Bijection sanity on the bounded universe.
    mapped = [map_value(v, w0, w1) for v in values]
    assert len(set(mapped)) == len(values)
    assert w0.ground != w1.ground
    assert map_value(w0.ground, w0, w1) == w1.ground

    counts = {}
    counts["left"] = commute_unary("left", w0.left, w1.left, values, w0, w1)
    counts["right"] = commute_unary("right", w0.right, w1.right, values, w0, w1)
    counts["atom_class"] = commute_unary(
        "atom_class", w0.atom_class, w1.atom_class, values, w0, w1
    )
    counts["make_pair"] = commute_binary(
        "make_pair", w0.make_pair, w1.make_pair, values, w0, w1
    )
    counts["atom_identity"] = commute_binary(
        "atom_identity", w0.atom_identity, w1.atom_identity, values, w0, w1
    )

    # Proper-list shape commutes as well.
    l0 = w0.lisp_list(w0.atom("a"), w0.atom("b"))
    l1 = w1.lisp_list(w1.atom("a"), w1.atom("b"))
    assert map_value(l0, w0, w1) == l1

    # Structural facts agree despite exact ground token differing.
    assert w0.atom_class(w0.ground) == w1.atom_class(w1.ground) == YES
    assert w0.left(l0) == w0.atom("a")
    assert w1.left(l1) == w1.atom("a")
    assert map_value(w0.right(w0.right(l0)), w0, w1) == w1.ground

    if policy == "admitted-reflexive":
        assert w0.atom_identity(w0.ground, w0.ground) == YES
        assert w1.atom_identity(w1.ground, w1.ground) == YES
    else:
        assert w0.atom_identity(w0.ground, w0.ground) is ERR
        assert w1.atom_identity(w1.ground, w1.ground) is ERR

    return len(values), counts


def main():
    print("policy\tvalues\tleft\tright\tatom-class\tmake-pair\tatom-identity")
    for policy in ("not-admitted", "admitted-reflexive"):
        n, c = check_policy(policy)
        print(
            f"{policy}\t{n}\t{c['left']}\t{c['right']}\t"
            f"{c['atom_class']}\t{c['make_pair']}\t{c['atom_identity']}"
        )

    print()
    print("COUNTERMODEL PAIR")
    print("M0 exact ground token: ('ground','g0')")
    print("M1 exact ground token: ('ground','g1')")
    print("recursive bijection f maps g0 -> g1 and preserves all modeled structural roles")
    print()
    print("PASS:")
    print("- pair construction commutes with f")
    print("- left/right commute with f")
    print("- atom-vs-pair classification commutes with f")
    print("- atom identity commutes with f under BOTH tested ground-domain policies")
    print("- proper-list termination shape commutes with f")
    print()
    print("BOUNDED MODEL-THEORETIC CONSEQUENCE:")
    print("the modeled structural signature cannot distinguish the exact ground")
    print("representative g0 from g1; it characterizes a ground ROLE up to")
    print("isomorphism. Any proof that exact () is uniquely required must import")
    print("an additional non-structural law (reader/evaluator/ratified identity/etc.).")


if __name__ == "__main__":
    main()
