#!/usr/bin/env python3
"""#2400 — factor current Core1 APPLY into typed callable-case dispatch.

Research only. No census promotion and no production semantic change.

This witness is anchored to the live C1-APPLY source shape, then compares that
ordered branch semantics with an explicit typed-sum dispatcher on an adversarial
bounded corpus.

It also includes an overlap counterexample proving that classifier disjointness
is a required premise rather than free metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE1 = ROOT / "lib" / "core1.lisp"


@dataclass(frozen=True)
class ErrorValue:
    code: str
    payload: Any


@dataclass(frozen=True)
class Primitive:
    identity: str


@dataclass(frozen=True)
class Funarg:
    label: str


@dataclass(frozen=True)
class Invalid:
    value: Any


@dataclass(frozen=True)
class Overlap:
    """Negative-control value admitted by deliberately bad classifiers."""
    identity: str
    label: str


def extract_apply_body() -> str:
    text = "\n".join(
        line.split(";", 1)[0]
        for line in CORE1.read_text(encoding="utf-8").splitlines()
    )
    match = re.search(r"\(00001001\s+C1-APPLY(?=\s|\))", text)
    assert match is not None, "C1-APPLY missing"
    start = match.start()

    depth = 0
    end = start
    while end < len(text):
        ch = text[end]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end += 1
                break
        end += 1
    assert depth == 0
    return text[start:end]


def source_shape_gate(body: str) -> None:
    required_in_order = (
        "C1-ERRORP FN",
        "C1-PRIMITIVE-IDENTITY FN",
        "C1-APPLY-PRIMITIVE",
        "C1-FUNARGP FN",
        "FN ARGS GLOBAL",
        "NOT-CALLABLE",
    )
    cursor = -1
    for needle in required_in_order:
        pos = body.find(needle, cursor + 1)
        assert pos >= 0, f"missing APPLY source shape: {needle}"
        cursor = pos

    # #2395's acyclic classification is rechecked locally.
    # One C1-APPLY token is the definition header; there must be no recursive call.
    assert body.count("C1-APPLY") == 2  # header + C1-APPLY-PRIMITIVE only
    assert "C1-EVAL" not in body
    assert "C1-EVLIS" not in body
    assert "C1-EVCON" not in body


def is_error(value: Any) -> bool:
    return isinstance(value, ErrorValue)


def primitive_identity(value: Any) -> str | None:
    if isinstance(value, Primitive):
        return value.identity
    return None


def is_funarg(value: Any) -> bool:
    return isinstance(value, Funarg)


def apply_primitive(identity: str, args: tuple[Any, ...]) -> tuple[Any, ...]:
    # Mechanism witness, not production behavior: retain route + exact payload.
    return ("primitive", identity, args)


def invoke_funarg(value: Funarg, args: tuple[Any, ...], world: str) -> tuple[Any, ...]:
    return ("funarg", value.label, args, world)


def make_not_callable(value: Any) -> ErrorValue:
    return ErrorValue("NOT-CALLABLE", value)


def direct_ordered_apply(fn: Any, args: tuple[Any, ...], world: str) -> Any:
    """Mirror the ordered branches observed in live C1-APPLY."""
    if is_error(fn):
        return fn
    identity = primitive_identity(fn)
    if identity is not None:
        return apply_primitive(identity, args)
    if is_funarg(fn):
        return invoke_funarg(fn, args, world)
    return make_not_callable(fn)


def classify(fn: Any) -> tuple[str, Any]:
    if is_error(fn):
        return ("error", fn)
    identity = primitive_identity(fn)
    if identity is not None:
        return ("primitive", identity)
    if is_funarg(fn):
        return ("funarg", fn)
    return ("invalid", fn)


def factorized_dispatch(fn: Any, args: tuple[Any, ...], world: str) -> Any:
    kind, payload = classify(fn)
    if kind == "error":
        return payload
    if kind == "primitive":
        return apply_primitive(payload, args)
    if kind == "funarg":
        return invoke_funarg(payload, args, world)
    assert kind == "invalid"
    return make_not_callable(payload)


def bad_primitive_identity(value: Any) -> str | None:
    if isinstance(value, Overlap):
        return value.identity
    return primitive_identity(value)


def bad_is_funarg(value: Any) -> bool:
    return isinstance(value, (Funarg, Overlap))


def overlap_order_counterexample(
    fn: Overlap, args: tuple[Any, ...], world: str
) -> tuple[Any, Any]:
    # Primitive-first semantics.
    identity = bad_primitive_identity(fn)
    if identity is not None:
        primitive_first = apply_primitive(identity, args)
    elif bad_is_funarg(fn):
        primitive_first = ("funarg", fn.label, args, world)
    else:
        primitive_first = make_not_callable(fn)

    # Funarg-first semantics.
    if bad_is_funarg(fn):
        funarg_first = ("funarg", fn.label, args, world)
    else:
        identity2 = bad_primitive_identity(fn)
        if identity2 is not None:
            funarg_first = apply_primitive(identity2, args)
        else:
            funarg_first = make_not_callable(fn)

    return primitive_first, funarg_first


def main() -> None:
    body = extract_apply_body()
    source_shape_gate(body)

    functions = (
        ErrorValue("ARITY", "x"),
        Primitive("CAR"),
        Primitive("CONS"),
        Funarg("closure-A"),
        Funarg("closure-B"),
        Invalid(17),
        Invalid(("plain", "list")),
    )
    arg_sets = (
        tuple(),
        (1,),
        ("a", "b"),
    )
    worlds = ("world-0", "world-1")

    cases = 0
    class_counts = {
        "error": 0,
        "primitive": 0,
        "funarg": 0,
        "invalid": 0,
    }

    for fn in functions:
        kind, _ = classify(fn)
        class_counts[kind] += 1

        # Live classifier premise for this bounded corpus: exactly one class.
        predicates = (
            is_error(fn),
            primitive_identity(fn) is not None,
            is_funarg(fn),
        )
        assert sum(int(x) for x in predicates) <= 1

        for args in arg_sets:
            for world in worlds:
                direct = direct_ordered_apply(fn, args, world)
                factored = factorized_dispatch(fn, args, world)
                assert direct == factored, (fn, args, world, direct, factored)
                cases += 1

    # Error pass-through must preserve object identity/value exactly.
    error = ErrorValue("ARITY", ("too-many", 3))
    assert factorized_dispatch(error, (1, 2), "world-X") is error

    # Funarg receives both args and world exactly once.
    funarg_result = factorized_dispatch(Funarg("F"), (1, 2), "W")
    assert funarg_result == ("funarg", "F", (1, 2), "W")

    # Invalid preserves original payload in NOT-CALLABLE.
    invalid = Invalid({"opaque": 1})
    invalid_result = factorized_dispatch(invalid, tuple(), "W")
    assert invalid_result == ErrorValue("NOT-CALLABLE", invalid)

    # Negative control: if classifiers overlap, branch order becomes semantic.
    overlap = Overlap("CAR", "also-funarg")
    primitive_first, funarg_first = overlap_order_counterexample(
        overlap, (1,), "W"
    )
    assert primitive_first != funarg_first

    print(f"SOURCE-SHAPE=C1-APPLY-LIVE")
    print(f"EQUIVALENCE-CASES={cases}")
    for kind in sorted(class_counts):
        print(f"CLASS-{kind.upper()}={class_counts[kind]}")
    print("ERROR-PASSTHROUGH=PASS")
    print("FUNARG-ARGS-WORLD-PRESERVED=PASS")
    print("INVALID-PAYLOAD-PRESERVED=PASS")
    print("CLASSIFIER-DISJOINT-BOUNDED-CORPUS=PASS")
    print("OVERLAP-ORDER-COUNTEREXAMPLE=PASS")
    print("FACTOR-LAW=CLASSIFY-THEN-DISPATCH")
    print("SEMANTIC-PROMOTION=NONE")
    print(
        "REMAINING-FACTS="
        "classifier,primitive-application,funarg-invocation,"
        "error-passthrough,invalid-call-error"
    )
    print("STATUS=PASS-APPLY-DISPATCH-FACTOR-WITNESS")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
