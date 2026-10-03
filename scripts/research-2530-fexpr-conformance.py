#!/usr/bin/env python3
"""#2530 — Phase-E FEXPR/FSUBR behavioral conformance witness.

Research-only. Bounded semantic model plus source guards against the live SENS
ordinary/macro call paths. No FEXPR/FSUBR production implementation and no
binary identity allocation.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Callable, TypeAlias

ROOT = Path(__file__).resolve().parent.parent
CLOSURES_RS = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"

Expr: TypeAlias = str | tuple["Expr", ...]


class CallMode(Enum):
    EAGER = 0
    RAW = 1


class UndefinedName(Exception):
    pass


def evaluate(expr: Expr) -> object:
    if expr == "never-defined":
        raise UndefinedName(expr)
    if isinstance(expr, tuple):
        if len(expr) == 2 and expr[0] == "quote":
            return expr[1]
        return tuple(evaluate(item) for item in expr)
    return expr


RawBody: TypeAlias = Callable[[tuple[Expr, ...]], object]


def invoke(mode: CallMode, body: RawBody, operands: tuple[Expr, ...]) -> object:
    if mode is CallMode.EAGER:
        evaluated = tuple(evaluate(operand) for operand in operands)
        return body(evaluated)  # type: ignore[arg-type]
    return body(operands)


def first_raw(operands: tuple[Expr, ...]) -> Expr:
    return operands[0]


def inspect_shape(operands: tuple[Expr, ...]) -> object:
    first = operands[0]
    assert isinstance(first, tuple)
    return (
        len(first),
        first[0],
        isinstance(first[1], tuple) if len(first) > 1 else False,
    )


def inner_raw(operands: tuple[Expr, ...]) -> object:
    return operands[0]


def outer_raw(operands: tuple[Expr, ...]) -> object:
    return invoke(CallMode.RAW, inner_raw, operands)


def source_guards() -> None:
    source = CLOSURES_RS.read_text(encoding="utf-8")

    apply_start = source.index("pub(super) fn apply(")
    apply_end = source.index("pub(super) fn apply_values", apply_start)
    ordinary = source[apply_start:apply_end]

    macro_start = source.index("pub(super) fn apply_macro(")
    macro_end = source.index("pub(super) fn value_to_expr", macro_start)
    macro = source[macro_start:macro_end]

    assert "slots.push(evaluate(argument, calling_environment)?);" in ordinary
    assert "slots.push(quoted(argument)?); // Do NOT evaluate arguments" in macro
    assert "let local_environment = call_frame(&closure, slots);" in macro
    assert "let expanded_value = evaluate(last, &local_environment)?;" in macro
    assert "environment: calling_environment.clone()" in macro
    assert "slots.push(calling_environment" not in macro
    assert macro.count("calling_environment") == 2


def main() -> None:
    source_guards()

    structured: Expr = (
        "wrapper",
        ("quote", ("a", "b")),
        ("branch", "never-defined"),
    )
    raw_shape = invoke(CallMode.RAW, inspect_shape, (structured,))
    assert raw_shape == (3, "wrapper", True)

    try:
        invoke(CallMode.EAGER, inspect_shape, (structured,))
    except UndefinedName:
        eager_structure = "error"
    else:
        eager_structure = "unexpected-success"
    assert eager_structure == "error"

    first: Expr = ("quote", "ok")
    second: Expr = "never-defined"
    nested = invoke(CallMode.RAW, outer_raw, (first, second))
    assert nested is first

    try:
        invoke(CallMode.EAGER, first_raw, (first, second))
    except UndefinedName:
        eager_nested = "error"
    else:
        eager_nested = "unexpected-success"
    assert eager_nested == "error"

    assert set(CallMode) == {CallMode.EAGER, CallMode.RAW}
    assert all(not isinstance(mode.value, str) for mode in CallMode)

    print("FEXPR-CONFORMANCE=PASS")
    print("C1-RAW-LIST-STRUCTURE=PASS")
    print("C2-NESTED-RAW-CALL=PASS")
    print("C3-ORDINARY-LAMBDA-EAGER=PASS")
    print("C4-CURRENT-MACRO-RAW=PASS")
    print("C5-NO-DIRECT-CALLER-ENV-INJECTION-IN-MACRO-BODY=PASS")
    print("C6-TYPED-CALL-MODE-NO-HUMAN-NAME-AUTHORITY=PASS")
    print("FEXPR-FSUBR=RAW+ENV-TWO-CAPABILITIES")
    print("TRANSFORMER-RELATION=ORTHOGONAL")
    print("BINARY-COORDINATE=UNALLOCATED")
    print("EXACT-WIDTH=UNRESOLVED")


if __name__ == "__main__":
    main()
