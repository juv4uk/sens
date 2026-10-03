#!/usr/bin/env python3
"""#2271: bounded remove-one synthesis attacks for ADD/MUL/RECIP.

Failure to synthesize within the bounded grammar is negative evidence only,
not a global impossibility theorem.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product

Value = Fraction | None
Signature = tuple[Value, ...]

VALUES = (
    Fraction(-2), Fraction(-1), Fraction(0), Fraction(1), Fraction(2)
)
ASSIGNMENTS = tuple(product(VALUES, repeat=2))

BASE: dict[str, Signature] = {
    "x": tuple(x for x, _ in ASSIGNMENTS),
    "y": tuple(y for _, y in ASSIGNMENTS),
    "-1": tuple(Fraction(-1) for _ in ASSIGNMENTS),
    "0": tuple(Fraction(0) for _ in ASSIGNMENTS),
    "1": tuple(Fraction(1) for _ in ASSIGNMENTS),
    "2": tuple(Fraction(2) for _ in ASSIGNMENTS),
}

TARGETS: dict[str, Signature] = {
    "ADD": tuple(x + y for x, y in ASSIGNMENTS),
    "MUL": tuple(x * y for x, y in ASSIGNMENTS),
    "RECIP": tuple(None if x == 0 else 1 / x for x, _ in ASSIGNMENTS),
}


def unary_recip(sig: Signature) -> Signature:
    return tuple(
        None if value is None or value == 0 else 1 / value
        for value in sig
    )


def binary(op: str, left: Signature, right: Signature) -> Signature:
    out: list[Value] = []
    for a, b in zip(left, right):
        if a is None or b is None:
            out.append(None)
        elif op == "ADD":
            out.append(a + b)
        elif op == "MUL":
            out.append(a * b)
        else:
            raise AssertionError(op)
    return tuple(out)


def synthesize(
    allowed: frozenset[str],
    target: Signature,
    max_cost: int = 5,
) -> tuple[int | None, str | None, list[int], int]:
    # One representative expression per observed semantic signature.
    known: dict[Signature, str] = {sig: expr for expr, sig in BASE.items()}
    by_cost: list[list[tuple[Signature, str]]] = [
        [(sig, expr) for expr, sig in BASE.items()]
    ]
    growth: list[int] = [len(by_cost[0])]

    if target in known:
        return 0, known[target], growth, len(known)

    for cost in range(1, max_cost + 1):
        new: dict[Signature, str] = {}

        if "RECIP" in allowed:
            for sig, expr in by_cost[cost - 1]:
                candidate = unary_recip(sig)
                if candidate not in known and candidate not in new:
                    new[candidate] = f"RECIP({expr})"

        for op in ("ADD", "MUL"):
            if op not in allowed:
                continue
            token = "+" if op == "ADD" else "*"
            for left_cost in range(cost):
                right_cost = cost - 1 - left_cost
                for left_sig, left_expr in by_cost[left_cost]:
                    for right_sig, right_expr in by_cost[right_cost]:
                        candidate = binary(op, left_sig, right_sig)
                        if candidate not in known and candidate not in new:
                            new[candidate] = (
                                f"({left_expr}{token}{right_expr})"
                            )

        known.update(new)
        by_cost.append(list(new.items()))
        growth.append(len(new))

        if target in known:
            return cost, known[target], growth, len(known)

    return None, None, growth, len(known)


def main() -> None:
    attacks = (
        ("ADD", frozenset({"MUL", "RECIP"})),
        ("MUL", frozenset({"ADD", "RECIP"})),
        ("RECIP", frozenset({"ADD", "MUL"})),
    )

    for target_name, allowed in attacks:
        cost, expr, growth, total = synthesize(
            allowed, TARGETS[target_name], max_cost=5
        )
        print(f"TARGET={target_name}")
        print(f"ALLOWED={','.join(sorted(allowed))}")
        print("NEW-SIGNATURES-BY-COST=" + ",".join(map(str, growth)))
        print(f"TOTAL-SEMANTIC-SIGNATURES={total}")
        print(f"FOUND-COST={cost if cost is not None else 'NONE'}")
        print(f"FOUND-EXPR={expr if expr is not None else 'NONE'}")
        assert cost is None, (
            f"bounded attack unexpectedly synthesized {target_name}: {expr}"
        )

    print("MAX-COST=5")
    print("ASSIGNMENTS=25")
    print("CONSTANTS=-1,0,1,2")
    print("STATUS=NO-REMOVE-ONE-SYNTHESIS-FOUND-BOUNDED")
    print("CLAIM=NEGATIVE-EVIDENCE-NOT-GLOBAL-MINIMALITY-THEOREM")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
