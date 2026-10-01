#!/usr/bin/env python3
"""#2072 first structural lower-bound witness.

Research-only finite-model / bounded-expression search.

This deliberately does NOT use the historical names as evidence.  It models
abstract capabilities:

  ground
  make_pair
  left
  right
  atom_class
  atom_identity
  choose

For each target capability we remove it and ask whether any well-typed
expression made from the remaining roles matches the target extensionally on
an adversarial finite domain.

A failed bounded search is supporting evidence, not a universal theorem.
For each case the script also prints the structural invariant/counterexample
that the later proof must formalize.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Iterable

ERR = object()
YES = ("bool", 1)
NO = ("bool", 0)
GROUND = ("ground",)
A = ("atom", "a")
B = ("atom", "b")
C = ("atom", "c")


def pair(x, y):
    return ("pair", x, y)


def is_pair(v):
    return isinstance(v, tuple) and len(v) == 3 and v[0] == "pair"


def make_pair(x, y):
    if x is ERR or y is ERR:
        return ERR
    return pair(x, y)


def left(v):
    return v[1] if is_pair(v) else ERR


def right(v):
    return v[2] if is_pair(v) else ERR


def atom_class(v):
    if v is ERR or v in (YES, NO):
        return ERR
    return NO if is_pair(v) else YES


def atom_identity(x, y):
    if x is ERR or y is ERR:
        return ERR
    if is_pair(x) or is_pair(y) or x in (YES, NO) or y in (YES, NO):
        return ERR
    return YES if x == y else NO


def choose(t, x, y):
    if t == YES:
        return x
    if t == NO:
        return y
    return ERR


def show(v):
    if v is ERR:
        return "ERR"
    if v == YES:
        return "1"
    if v == NO:
        return "0"
    if v == GROUND:
        return "ground"
    if isinstance(v, tuple) and v and v[0] == "atom":
        return v[1]
    if is_pair(v):
        return f"({show(v[1])}.{show(v[2])})"
    return repr(v)


@dataclass(frozen=True)
class Expr:
    kind: str  # data | bool
    size: int
    text: str
    fn: Callable[[tuple], object]


def signature(expr: Expr, cases: tuple[tuple, ...]):
    return tuple(expr.fn(case) for case in cases)


def leaves(arity: int):
    data = [
        Expr("data", 1, "ground", lambda env: GROUND),
        Expr("data", 1, "x", lambda env: env[0]),
    ]
    if arity == 2:
        data.append(Expr("data", 1, "y", lambda env: env[1]))
    boolean = [
        Expr("bool", 1, "0", lambda env: NO),
        Expr("bool", 1, "1", lambda env: YES),
    ]
    return data, boolean


def enumerate_semantics(
    *,
    arity: int,
    cases: tuple[tuple, ...],
    excluded: str,
    max_size: int,
):
    """Enumerate one cheapest expression for each extensional signature."""

    data_by_size: dict[int, list[Expr]] = {}
    bool_by_size: dict[int, list[Expr]] = {}
    seen_data = {}
    seen_bool = {}

    d0, b0 = leaves(arity)
    for e in d0:
        sig = signature(e, cases)
        if sig not in seen_data:
            seen_data[sig] = e
            data_by_size.setdefault(1, []).append(e)
    for e in b0:
        sig = signature(e, cases)
        if sig not in seen_bool:
            seen_bool[sig] = e
            bool_by_size.setdefault(1, []).append(e)

    def admit(e: Expr):
        sig = signature(e, cases)
        seen = seen_data if e.kind == "data" else seen_bool
        by_size = data_by_size if e.kind == "data" else bool_by_size
        if sig in seen:
            return
        seen[sig] = e
        by_size.setdefault(e.size, []).append(e)

    for size in range(2, max_size + 1):
        # Unary roles.
        if excluded != "left":
            for a in data_by_size.get(size - 1, ()):
                admit(Expr("data", size, f"left({a.text})",
                           lambda env, a=a: left(a.fn(env))))
        if excluded != "right":
            for a in data_by_size.get(size - 1, ()):
                admit(Expr("data", size, f"right({a.text})",
                           lambda env, a=a: right(a.fn(env))))
        if excluded != "atom_class":
            for a in data_by_size.get(size - 1, ()):
                admit(Expr("bool", size, f"atom_class({a.text})",
                           lambda env, a=a: atom_class(a.fn(env))))

        # Binary roles.
        for ls in range(1, size - 1):
            rs = size - 1 - ls
            if excluded != "make_pair":
                for a in data_by_size.get(ls, ()):
                    for b in data_by_size.get(rs, ()):
                        admit(Expr("data", size, f"make_pair({a.text},{b.text})",
                                   lambda env, a=a, b=b: make_pair(a.fn(env), b.fn(env))))
            if excluded != "atom_identity":
                for a in data_by_size.get(ls, ()):
                    for b in data_by_size.get(rs, ()):
                        admit(Expr("bool", size, f"atom_identity({a.text},{b.text})",
                                   lambda env, a=a, b=b: atom_identity(a.fn(env), b.fn(env))))

        # Ternary choose.  Keep only exact total size.
        if excluded != "choose":
            for ts in range(1, size - 2):
                for xs in range(1, size - 1 - ts):
                    ys = size - 1 - ts - xs
                    if ys < 1:
                        continue
                    for t in bool_by_size.get(ts, ()):
                        for x in data_by_size.get(xs, ()):
                            for y in data_by_size.get(ys, ()):
                                admit(Expr(
                                    "data", size,
                                    f"choose({t.text},{x.text},{y.text})",
                                    lambda env, t=t, x=x, y=y:
                                        choose(t.fn(env), x.fn(env), y.fn(env))
                                ))
                        for x in bool_by_size.get(xs, ()):
                            for y in bool_by_size.get(ys, ()):
                                admit(Expr(
                                    "bool", size,
                                    f"choose({t.text},{x.text},{y.text})",
                                    lambda env, t=t, x=x, y=y:
                                        choose(t.fn(env), x.fn(env), y.fn(env))
                                ))

    return seen_data, seen_bool


PAIR_CASES = (
    (pair(A, B),),
    (pair(C, B),),
    (pair(A, C),),
    (pair(pair(A, C), B),),
    (pair(A, pair(B, C)),),
)

ATOM_CASES_2 = tuple((x, y) for x in (A, B, C) for y in (A, B, C))

CONSTRUCT_CASES = (
    (A, B),
    (A, C),
    (B, A),
    (B, C),
    (C, A),
)

CLASS_CASES = (
    (GROUND,),
    (A,),
    (B,),
    (pair(A, B),),
    (pair(B, A),),
    (pair(pair(A, B), C),),
)


def target_sig(name: str, cases):
    if name == "left":
        return tuple(left(env[0]) for env in cases), "data"
    if name == "right":
        return tuple(right(env[0]) for env in cases), "data"
    if name == "make_pair":
        return tuple(make_pair(env[0], env[1]) for env in cases), "data"
    if name == "atom_identity":
        return tuple(atom_identity(env[0], env[1]) for env in cases), "bool"
    if name == "atom_class":
        return tuple(atom_class(env[0]) for env in cases), "bool"
    raise KeyError(name)


TESTS = (
    ("left", 1, PAIR_CASES),
    ("right", 1, PAIR_CASES),
    ("make_pair", 2, CONSTRUCT_CASES),
    ("atom_identity", 2, ATOM_CASES_2),
    ("atom_class", 1, CLASS_CASES),
)


def right_closure(v):
    out = {GROUND, v}
    cur = v
    while is_pair(cur):
        cur = right(cur)
        out.add(cur)
    return out


def left_closure(v):
    out = {GROUND, v}
    cur = v
    while is_pair(cur):
        cur = left(cur)
        out.add(cur)
    return out


def invariant_witnesses():
    p = pair(A, B)
    assert left(p) == A and A not in right_closure(p)
    assert right(p) == B and B not in left_closure(p)

    # Without construction, selecting/projecting existing atomic inputs cannot
    # manufacture this fresh pair.
    assert pair(A, B) not in {GROUND, A, B}

    # Without atom identity, unary atom-class observations are identical for
    # these two binary inputs although identity target differs.
    assert atom_class(A) == atom_class(B) == YES
    assert atom_identity(A, A) == YES
    assert atom_identity(A, B) == NO

    # Without atom_class, available value eliminators/identity are partial on
    # one side of the atom-vs-pair partition; there is no catch/error observer
    # in this abstract basis.
    assert left(A) is ERR
    assert atom_identity(pair(A, B), pair(A, B)) is ERR


def main():
    max_size = 9
    invariant_witnesses()

    print("target\\tmax-size\\tdata-classes\\tbool-classes\\tmatch")
    results = {}
    for name, arity, cases in TESTS:
        data, boolean = enumerate_semantics(
            arity=arity, cases=cases, excluded=name, max_size=max_size
        )
        want, kind = target_sig(name, cases)
        pool = data if kind == "data" else boolean
        found = pool.get(want)
        results[name] = found
        print(
            f"{name}\\t{max_size}\\t{len(data)}\\t{len(boolean)}\\t"
            f"{found.text if found else 'NONE'}"
        )

    assert all(v is None for v in results.values())

    print()
    print("INVARIANCE / LOWER-BOUND WITNESSES")
    print("- without left: left(pair(a,b))=a, but a is outside the right-only subvalue closure")
    print("- without right: right(pair(a,b))=b, but b is outside the left-only subvalue closure")
    print("- without make_pair: pair(a,b) is fresh structure, not an input/ground/projection")
    print("- without atom_identity: (a,a) and (a,b) have identical unary atom-class observations")
    print("- without atom_class: projection/identity probes are partial across atom-vs-pair; no error-catch oracle admitted")
    print()
    print("PASS: no removed structural role was reconstructed through size 9 on its")
    print("adversarial finite domain. This is bounded support for #2072, not a")
    print("universal minimality theorem and not evidence about QUOTE/COND.")
    print()
    print("FOUNDATIONAL CONSEQUENCE TO TEST NEXT:")
    print("the value algebra may have its own lower bounds before evaluator-control")
    print("roles are introduced; historical bīja3 therefore must not be assumed to")
    print("be one homogeneous root layer.")


if __name__ == "__main__":
    main()
