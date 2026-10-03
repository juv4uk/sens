#!/usr/bin/env python3
"""#2488 — RETURN placement falsifier.

Research-only. No production control operator and no binary coordinate are
allocated here.

The witness factors historical RETURN into two independently observable policy
axes relative to ordinary D4 completion:
  1. target selection: immediate caller vs nearest active PROG exit;
  2. active-context policy: optional/fallback vs required/fail-closed.

It also checks typed base-operation mismatch against D4 APPLY/EVAL/LAMBDA/COND.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Target(Enum):
    IMMEDIATE = "immediate"
    NEAREST_PROG = "nearest-prog"


class Context(Enum):
    OPTIONAL = "optional"
    REQUIRED = "required"


@dataclass(frozen=True)
class Policy:
    target: Target
    context: Context


@dataclass(frozen=True)
class OperationShape:
    input_role: str
    primary_effect: str


ORDINARY = Policy(Target.IMMEDIATE, Context.OPTIONAL)
HISTORICAL_RETURN = Policy(Target.NEAREST_PROG, Context.REQUIRED)

D4_SHAPES = {
    "APPLY": OperationShape("callable+value-list+environment", "invoke-callable"),
    "EVAL": OperationShape("form+environment", "evaluate-form"),
    "LAMBDA": OperationShape("parameters+body+environment", "construct-closure"),
    "COND": OperationShape("predicate+branches", "select-local-branch"),
}
RETURN_SHAPE = OperationShape("value+implicit-active-prog-context", "nonlocal-transfer")


def deliver(policy: Policy, active_progs: tuple[str, ...]) -> tuple[str, str]:
    if policy.context is Context.REQUIRED and not active_progs:
        return ("error", "no-active-prog")

    if policy.target is Target.NEAREST_PROG and active_progs:
        return ("exit", active_progs[-1])

    return ("return", "immediate-caller")


def signature(policy: Policy) -> tuple[tuple[str, str], ...]:
    return (
        deliver(policy, ()),
        deliver(policy, ("P0",)),
        deliver(policy, ("P0", "P1")),
    )


def distance(a: Policy, b: Policy) -> int:
    return int(a.target != b.target) + int(a.context != b.context)


def main() -> None:
    policies = {
        "immediate-optional": Policy(Target.IMMEDIATE, Context.OPTIONAL),
        "immediate-required": Policy(Target.IMMEDIATE, Context.REQUIRED),
        "nearest-optional": Policy(Target.NEAREST_PROG, Context.OPTIONAL),
        "nearest-required": Policy(Target.NEAREST_PROG, Context.REQUIRED),
    }

    signatures = {name: signature(policy) for name, policy in policies.items()}

    # Full observable square: both axes can vary independently.
    assert len(set(signatures.values())) == 4, signatures

    # Target selection is independently observable while context policy is held.
    assert deliver(policies["immediate-required"], ("P0",)) != deliver(
        policies["nearest-required"], ("P0",)
    )

    # Active-context requirement is independently observable while target is held.
    assert deliver(policies["immediate-optional"], ()) != deliver(
        policies["immediate-required"], ()
    )
    assert deliver(policies["nearest-optional"], ()) != deliver(
        policies["nearest-required"], ()
    )

    # Nested dynamic scope selects the most recent active PROG.
    assert deliver(HISTORICAL_RETURN, ("P0", "P1")) == ("exit", "P1")
    assert deliver(HISTORICAL_RETURN, ()) == ("error", "no-active-prog")

    assert distance(ORDINARY, HISTORICAL_RETURN) == 2

    # Parent theorem: placement-law requires the same base semantic operation,
    # not merely implementation adjacency or control-related vocabulary.
    for name, shape in D4_SHAPES.items():
        assert shape.primary_effect != RETURN_SHAPE.primary_effect, (name, shape)
        assert shape.input_role != RETURN_SHAPE.input_role, (name, shape)

    fixed_d5_selectors = {
        "10100", "10101", "10110", "10111",
        "11000", "11001", "11010", "11011",
    }
    assert len(fixed_d5_selectors) == 8

    print("RETURN-PLACEMENT=PASS")
    print("DOMAIN=Core-post-D4-placement")
    print("RELATION=Core-only")
    print("ORDINARY-COMPLETION=immediate/context-optional")
    print("RETURN-CORE=nearest-active-PROG/context-required")
    print("INDEPENDENT-AXIS-1=target-selection")
    print("INDEPENDENT-AXIS-2=active-context-requirement")
    print("ORDINARY-TO-RETURN-DELTA-COUNT=2")
    print("APPLY-PARENT=REJECT-same-base-operation")
    print("EVAL-PARENT=REJECT-same-base-operation")
    print("LAMBDA-PARENT=REJECT-same-base-operation")
    print("COND-PARENT=REJECT-same-base-operation")
    print("RETURN-ROOT=RESIDUE")
    print("EXACT-DOMAIN=UNRESOLVED")
    print("BINARY-COORDINATE=UNALLOCATED")
    print("NON-CONCLUSION=no-D5-or-D6-address-ratified")


if __name__ == "__main__":
    main()
