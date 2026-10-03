#!/usr/bin/env python3
"""#2271: bounded exact-Q desugaring into ADD + MUL + RECIP.

Research only. This proves bounded sufficiency under an explicit premise:
negative rational constants (in particular -1) are values, not operations.

It does NOT prove global minimality and does NOT request production renumbering.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import TypeAlias

Expr: TypeAlias = tuple

LEAVES: tuple[Expr, ...] = (
    ("var", "x"),
    ("var", "y"),
    ("const", Fraction(-1)),
    ("const", Fraction(0)),
    ("const", Fraction(1)),
    ("const", Fraction(2)),
)
UNARY = ("neg", "recip")
BINARY = ("add", "mul", "sub", "div")
ASSIGNMENTS = tuple(
    {"x": x, "y": y}
    for x, y in product(
        (Fraction(-2), Fraction(-1), Fraction(0), Fraction(1), Fraction(2)),
        repeat=2,
    )
)


def generate(depth: int) -> tuple[Expr, ...]:
    levels: list[tuple[Expr, ...]] = [LEAVES]
    all_exprs: dict[str, Expr] = {repr(e): e for e in LEAVES}

    for _ in range(depth):
        prior = tuple(all_exprs.values())
        new: dict[str, Expr] = {}
        for op in UNARY:
            for a in prior:
                e = (op, a)
                new.setdefault(repr(e), e)
        for op in BINARY:
            for a, b in product(prior, repeat=2):
                e = (op, a, b)
                new.setdefault(repr(e), e)
        all_exprs.update(new)
        levels.append(tuple(new.values()))

    return tuple(all_exprs.values())


def desugar(expr: Expr) -> Expr:
    tag = expr[0]
    if tag in ("var", "const"):
        return expr
    if tag == "add":
        return ("add", desugar(expr[1]), desugar(expr[2]))
    if tag == "mul":
        return ("mul", desugar(expr[1]), desugar(expr[2]))
    if tag == "recip":
        return ("recip", desugar(expr[1]))
    if tag == "neg":
        return ("mul", ("const", Fraction(-1)), desugar(expr[1]))
    if tag == "sub":
        return (
            "add",
            desugar(expr[1]),
            ("mul", ("const", Fraction(-1)), desugar(expr[2])),
        )
    if tag == "div":
        return ("mul", desugar(expr[1]), ("recip", desugar(expr[2])))
    raise AssertionError(f"unknown tag: {tag}")


def evaluate(expr: Expr, env: dict[str, Fraction]) -> Fraction | None:
    tag = expr[0]
    if tag == "var":
        return env[expr[1]]
    if tag == "const":
        return expr[1]

    if tag in ("neg", "recip"):
        value = evaluate(expr[1], env)
        if value is None:
            return None
        if tag == "neg":
            return -value
        if value == 0:
            return None
        return 1 / value

    left = evaluate(expr[1], env)
    right = evaluate(expr[2], env)
    if left is None or right is None:
        return None
    if tag == "add":
        return left + right
    if tag == "mul":
        return left * right
    if tag == "sub":
        return left - right
    if tag == "div":
        if right == 0:
            return None
        return left / right
    raise AssertionError(f"unknown tag: {tag}")


def count_ops(expr: Expr) -> int:
    tag = expr[0]
    if tag in ("var", "const"):
        return 0
    if tag in UNARY:
        return 1 + count_ops(expr[1])
    return 1 + count_ops(expr[1]) + count_ops(expr[2])


def contains_surface_sugar(expr: Expr) -> bool:
    tag = expr[0]
    if tag in ("neg", "sub", "div"):
        return True
    if tag in ("var", "const"):
        return False
    if tag in UNARY:
        return contains_surface_sugar(expr[1])
    return contains_surface_sugar(expr[1]) or contains_surface_sugar(expr[2])


def core_only(expr: Expr) -> bool:
    tag = expr[0]
    if tag in ("var", "const"):
        return True
    if tag == "recip":
        return core_only(expr[1])
    if tag in ("add", "mul"):
        return core_only(expr[1]) and core_only(expr[2])
    return False


def main() -> None:
    expressions = generate(depth=2)
    sugar = tuple(e for e in expressions if contains_surface_sugar(e))

    eval_cases = 0
    undefined_cases = 0
    original_ops = 0
    core_ops = 0
    max_expansion = 0

    for expr in sugar:
        core = desugar(expr)
        assert core_only(core)
        before = count_ops(expr)
        after = count_ops(core)
        original_ops += before
        core_ops += after
        max_expansion = max(max_expansion, after - before)

        for env in ASSIGNMENTS:
            lhs = evaluate(expr, env)
            rhs = evaluate(core, env)
            assert lhs == rhs, (expr, core, env, lhs, rhs)
            eval_cases += 1
            if lhs is None:
                undefined_cases += 1

    print(f"EXPRESSIONS-TOTAL={len(expressions)}")
    print(f"EXPRESSIONS-WITH-NEG-SUB-DIV={len(sugar)}")
    print(f"ASSIGNMENTS={len(ASSIGNMENTS)}")
    print(f"EXACT-Q-EVALUATION-CASES={eval_cases}")
    print(f"UNDEFINED-PARITY-CASES={undefined_cases}")
    print(f"ORIGINAL-OP-NODES={original_ops}")
    print(f"CORE-OP-NODES={core_ops}")
    print(f"OP-NODE-EXPANSION={core_ops-original_ops}")
    print(f"MAX-PER-EXPR-OP-EXPANSION={max_expansion}")
    print("CORE=ADD,MUL,RECIP")
    print("DERIVED=NEG,SUB,DIV")
    print("PREMISE=NEGATIVE-RATIONAL-CONSTANTS-ARE-VALUES")
    print("STATUS=PASS-BOUNDED-SUFFICIENCY-NOT-MINIMALITY")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
