#!/usr/bin/env python3
"""Independent lexical-reference checks for the F3M-5 lambda research candidate.

This checker deliberately does not import the Rust enumerator.  It validates the
machine-readable candidate law and exercises an independent nameless/de-Bruijn
reference model for alpha-equivalence, lexical depth, closure capture and beta
application.  It proves no production admission or SENS domain allocation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "knowledge/f3m5-lambda-lexical-reference-candidate-v1.json"


class Blocked(ValueError):
    pass


def load_spec() -> dict:
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    assert data["schema"] == "sens-f3m5-lambda-lexical-reference-candidate/v1"
    assert data["status"] == "RESEARCH-CANDIDATE-NOT-RATIFIED"
    assert data["production_mapping_changed"] is False
    assert data["domain_coordinate_allocated"] is False
    assert data["text7_or_d7_required"] is False
    assert data["capacity"]["physical_bits"] == 40
    assert data["capacity"]["physical_bytes"] == 5
    assert data["capacity"]["payloads"] == 1 << 40
    assert data["proof_scope"]["exhaustive_2_pow_40_sweep"] is False
    return data


def lower_named(term, env=()):
    tag = term[0]
    if tag == "var":
        name = term[1]
        for depth, bound in enumerate(env):
            if name == bound:
                return ("bound", depth)
        raise Blocked(f"free variable {name!r}")
    if tag == "lam":
        _, name, body = term
        return ("lam", lower_named(body, (name,) + env))
    raise Blocked(f"unsupported named term {tag!r}")


@dataclass(frozen=True)
class Closure:
    body: tuple
    env: tuple


def eval_term(term, env=()):
    tag = term[0]
    if tag == "lit":
        return term[1]
    if tag == "bound":
        index = term[1]
        if index < 0 or index >= len(env):
            raise Blocked(f"BOUND({index}) outside lexical depth {len(env)}")
        return env[index]
    if tag == "lam":
        return Closure(term[1], tuple(env))
    raise Blocked(f"unsupported nameless term {tag!r}")


def apply(value, argument):
    if not isinstance(value, Closure):
        raise Blocked("application target is not a closure")
    # Nearest binder is always index 0; captured outer bindings move outward.
    return eval_term(value.body, (argument,) + value.env)


def main() -> int:
    spec = load_spec()

    # Alpha-equivalent names collapse to exactly one nameless identity.
    named_i = [
        ("lam", "x", ("var", "x")),
        ("lam", "y", ("var", "y")),
        ("lam", "foo", ("var", "foo")),
    ]
    canonical_i = ("lam", ("bound", 0))
    assert {lower_named(term) for term in named_i} == {canonical_i}

    # Nested binders distinguish nearest from outer deterministically.
    assert lower_named(("lam", "x", ("lam", "y", ("var", "y")))) == (
        "lam", ("lam", ("bound", 0))
    )
    assert lower_named(("lam", "x", ("lam", "y", ("var", "x")))) == (
        "lam", ("lam", ("bound", 1))
    )

    # Free source names and out-of-depth machine references both fail closed.
    try:
        lower_named(("lam", "x", ("var", "z")))
    except Blocked:
        pass
    else:
        raise AssertionError("free named variable was admitted")

    try:
        eval_term(("bound", 0), ())
    except Blocked:
        pass
    else:
        raise AssertionError("free BOUND(0) was admitted at root depth 0")

    # Independent beta witnesses for I, K, KI.
    i = canonical_i
    k = ("lam", ("lam", ("bound", 1)))
    ki = ("lam", ("lam", ("bound", 0)))

    assert apply(eval_term(i), "A") == "A"
    assert apply(apply(eval_term(k), "A"), "B") == "A"
    assert apply(apply(eval_term(ki), "A"), "B") == "B"

    # Captured lexical environment survives after the outer application.
    captured = apply(eval_term(k), "outer")
    assert isinstance(captured, Closure)
    assert apply(captured, "inner") == "outer"

    witnesses = spec["canonical_witnesses"]
    assert witnesses["I"]["payload_hex"] == "0000000000"
    assert witnesses["K"]["payload_hex"] == "0000000010"
    assert witnesses["KI"]["payload_hex"] == "000000000F"
    assert witnesses["all_d1_d3_lambda"]["payload_hex"] == "056169CB4A"

    print("F3M5-LAMBDA-LEXICAL-REFERENCE: PASS")
    print("alpha=canonical debruijn=nearest-zero free=reject beta=I,K,KI capture=pass")
    print("status=research-candidate production-admission=no domain-coordinate=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
