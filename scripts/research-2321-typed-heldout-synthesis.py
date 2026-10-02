#!/usr/bin/env python3
"""#2321 typed held-out function synthesis.

Research only. The synthesizer receives:
- typed primitive morphisms;
- bounded input corpora;
- hidden target behavior signatures.

It does NOT receive hand-written target derivation rules.

Positive controls:
- GT/GE/LE from SWAP, LT, NOT;
- QUOTIENT/REMAINDER from DIVMOD, CAR, CDR.

Negative controls:
- EQ and GCD should remain unresolved under bounded pure composition.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from collections import deque
from typing import Callable, Any


@dataclass(frozen=True)
class Morphism:
    name: str
    source: str
    target: str
    fn: Callable[[Any], Any]


PRIMITIVES: tuple[Morphism, ...] = ()


def euclidean_divmod(a: int, b: int) -> tuple[int, int]:
    if b == 0:
        raise ZeroDivisionError("divmod by zero")
    d = abs(b)
    q_pos = a // d
    r = a - d * q_pos
    q = q_pos if b > 0 else -q_pos
    assert a == b * q + r
    assert 0 <= r < d
    return q, r


SWAP = Morphism("SWAP", "QxQ", "QxQ", lambda p: (p[1], p[0]))
LT = Morphism("LT", "QxQ", "PredicateBit", lambda p: p[0] < p[1])
NOT = Morphism("NOT", "PredicateBit", "PredicateBit", lambda x: not x)

DIVMOD = Morphism(
    "DIVMOD",
    "ZxZ_nonzero_divisor",
    "PairZZ",
    lambda p: euclidean_divmod(p[0], p[1]),
)
CAR = Morphism("CAR", "PairZZ", "Z", lambda p: p[0])
CDR = Morphism("CDR", "PairZZ", "Z", lambda p: p[1])

PRIMITIVES = (SWAP, LT, NOT, DIVMOD, CAR, CDR)


def run_path(path: tuple[Morphism, ...], value: Any) -> Any:
    out = value
    for morphism in path:
        out = morphism.fn(out)
    return out


def path_types_ok(path: tuple[Morphism, ...], source: str) -> bool:
    current = source
    for morphism in path:
        if morphism.source != current:
            return False
        current = morphism.target
    return True


def path_target(path: tuple[Morphism, ...], source: str) -> str:
    current = source
    for morphism in path:
        if morphism.source != current:
            raise TypeError("ill-typed path")
        current = morphism.target
    return current


def signature(path: tuple[Morphism, ...], corpus: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(run_path(path, x) for x in corpus)


def synthesize(
    source: str,
    target: str,
    corpus: tuple[Any, ...],
    target_signature: tuple[Any, ...],
    max_depth: int,
) -> tuple[Morphism, ...] | None:
    queue = deque([tuple()])
    seen: set[tuple[str, tuple[Any, ...]]] = set()

    while queue:
        path = queue.popleft()
        current_type = path_target(path, source)

        if path:
            sig = signature(path, corpus)
            key = (current_type, sig)
            if key in seen:
                continue
            seen.add(key)

            if current_type == target and sig == target_signature:
                return path

        if len(path) >= max_depth:
            continue

        for primitive in PRIMITIVES:
            if primitive.source == current_type:
                queue.append(path + (primitive,))

    return None


Q = tuple(Fraction(n) for n in (-2, -1, 0, 1, 2))
ORDER_CORPUS = tuple((a, b) for a in Q for b in Q)

Z_CORPUS = tuple(
    (a, b)
    for a in range(-8, 9)
    for b in range(-4, 5)
    if b != 0
)


def target_order(name: str) -> tuple[bool, ...]:
    if name == "GT":
        return tuple(a > b for a, b in ORDER_CORPUS)
    if name == "GE":
        return tuple(a >= b for a, b in ORDER_CORPUS)
    if name == "LE":
        return tuple(a <= b for a, b in ORDER_CORPUS)
    if name == "EQ":
        return tuple(a == b for a, b in ORDER_CORPUS)
    raise AssertionError(name)


def target_structural(name: str) -> tuple[int, ...]:
    if name == "QUOTIENT":
        return tuple(euclidean_divmod(a, b)[0] for a, b in Z_CORPUS)
    if name == "REMAINDER":
        return tuple(euclidean_divmod(a, b)[1] for a, b in Z_CORPUS)
    if name == "GCD":
        from math import gcd
        return tuple(gcd(a, b) for a, b in Z_CORPUS)
    raise AssertionError(name)


def certificate(path: tuple[Morphism, ...], source: str) -> str:
    current = source
    parts = []
    for morphism in path:
        parts.append(f"{current}-[{morphism.name}]->{morphism.target}")
        current = morphism.target
    return "|".join(parts)


def main() -> None:
    positives = (
        ("GT", "QxQ", "PredicateBit", ORDER_CORPUS, target_order("GT"), 3),
        ("GE", "QxQ", "PredicateBit", ORDER_CORPUS, target_order("GE"), 3),
        ("LE", "QxQ", "PredicateBit", ORDER_CORPUS, target_order("LE"), 3),
        (
            "QUOTIENT",
            "ZxZ_nonzero_divisor",
            "Z",
            Z_CORPUS,
            target_structural("QUOTIENT"),
            3,
        ),
        (
            "REMAINDER",
            "ZxZ_nonzero_divisor",
            "Z",
            Z_CORPUS,
            target_structural("REMAINDER"),
            3,
        ),
    )

    negative = (
        ("EQ", "QxQ", "PredicateBit", ORDER_CORPUS, target_order("EQ"), 4),
        (
            "GCD",
            "ZxZ_nonzero_divisor",
            "Z",
            Z_CORPUS,
            target_structural("GCD"),
            4,
        ),
    )

    found = 0
    for name, source, target, corpus, oracle, depth in positives:
        path = synthesize(source, target, corpus, oracle, depth)
        assert path is not None, name
        assert path_types_ok(path, source)
        assert signature(path, corpus) == oracle
        found += 1
        print(
            f"FOUND target={name} depth={len(path)} "
            f"path={'>'.join(m.name for m in path)} "
            f"certificate={certificate(path, source)}"
        )

    unresolved = 0
    for name, source, target, corpus, oracle, depth in negative:
        path = synthesize(source, target, corpus, oracle, depth)
        assert path is None, (name, tuple(m.name for m in path or ()))
        unresolved += 1
        print(f"UNRESOLVED target={name} max_depth={depth}")

    print(f"POSITIVE-TARGETS-FOUND={found}")
    print(f"NEGATIVE-TARGETS-UNRESOLVED={unresolved}")
    print(f"ORDER-CORPUS={len(ORDER_CORPUS)}")
    print(f"STRUCTURAL-CORPUS={len(Z_CORPUS)}")
    print("SEARCH=TYPE-DIRECTED-BFS-SEMANTIC-SIGNATURE-DEDUP")
    print("STATUS=PASS-TYPED-HELDOUT-SYNTHESIS")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
