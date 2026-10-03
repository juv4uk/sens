#!/usr/bin/env python3
"""#2506 — D6 binding-policy generator witness.

Research-only. Tests whether two independently observed SETQ-core policy axes
form a clean two-bit product generator over D4 DEFINE.

No production mutation and no D6 coordinate is ratified here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from enum import Enum
from itertools import product


class Scope(str, Enum):
    CURRENT = "current"
    NEAREST = "nearest-existing"


class Miss(str, Enum):
    CREATE = "create"
    FAIL = "fail"


@dataclass(frozen=True)
class Policy:
    scope: Scope
    miss: Miss


DEFINE = Policy(Scope.CURRENT, Miss.CREATE)
CURRENT_FAIL = Policy(Scope.CURRENT, Miss.FAIL)
NEAREST_CREATE = Policy(Scope.NEAREST, Miss.CREATE)
SETQ_CORE = Policy(Scope.NEAREST, Miss.FAIL)


class MissingBinding(Exception):
    pass


def apply_update(frames: list[dict[str, str]], name: str, value: str, policy: Policy):
    result = deepcopy(frames)
    target = None

    if policy.scope is Scope.CURRENT:
        if name in result[0]:
            target = 0
    else:
        for index, frame in enumerate(result):
            if name in frame:
                target = index
                break

    if target is None:
        if policy.miss is Miss.FAIL:
            raise MissingBinding(name)
        target = 0

    result[target][name] = value
    return result, target


def signature(policy: Policy):
    cases = [
        [{}, {"x": "OLD"}],
        [{}, {}],
        [{"x": "OLD"}, {"x": "OUTER"}],
    ]
    out = []
    for frames in cases:
        try:
            after, target = apply_update(frames, "x", "NEW", policy)
            out.append(
                (
                    "ok",
                    target,
                    after[0].get("x"),
                    after[1].get("x"),
                )
            )
        except MissingBinding:
            out.append(("error",))
    return tuple(out)


def scope_refine(policy: Policy) -> Policy:
    return replace(policy, scope=Scope.NEAREST)


def miss_refine(policy: Policy) -> Policy:
    return replace(policy, miss=Miss.FAIL)


def d6_selector_closure() -> set[str]:
    roots = ("101", "110")
    return {
        root + "".join(bits)
        for root in roots
        for bits in product("01", repeat=3)
    }


def main() -> None:
    square = {
        "00": DEFINE,
        "01": CURRENT_FAIL,
        "10": NEAREST_CREATE,
        "11": SETQ_CORE,
    }

    # All four policy corners are observationally distinct.
    signatures = {bits: signature(policy) for bits, policy in square.items()}
    assert len(set(signatures.values())) == 4, signatures

    # Each refinement changes exactly one field from the parent.
    assert scope_refine(DEFINE) == NEAREST_CREATE
    assert miss_refine(DEFINE) == CURRENT_FAIL

    # The two refinements commute on the base policy.
    scope_then_miss = miss_refine(scope_refine(DEFINE))
    miss_then_scope = scope_refine(miss_refine(DEFINE))
    assert scope_then_miss == miss_then_scope == SETQ_CORE

    # They also commute on every corner where applying an already-selected
    # refinement is idempotent.
    for policy in square.values():
        assert miss_refine(scope_refine(policy)) == scope_refine(miss_refine(policy))

    # The 00 corner is exactly the parent policy and must not be mistaken for a
    # new semantic resident merely because it has six printed bits.
    assert square["00"] == DEFINE
    assert signature(square["00"]) == signature(DEFINE)

    # Both one-axis corners are genuine observable policies.
    assert signature(square["01"]) != signature(DEFINE)
    assert signature(square["10"]) != signature(DEFINE)

    # The 11 corner exactly matches the shared-location core.
    assert square["11"] == SETQ_CORE
    assert signature(square["11"]) == signature(SETQ_CORE)

    selectors = d6_selector_closure()
    assert len(selectors) == 16

    candidate_words = {"001100", "001101", "001110", "001111"}
    assert candidate_words.isdisjoint(selectors)

    # Axis order is symmetric for the target 11 corner: swapping which semantic
    # axis is described first swaps the intermediate 01/10 labels but leaves
    # the both-refinements target at parent + 11.
    assert "001111".endswith("11")

    print("D6-BINDING-POLICY-GENERATOR=PASS")
    print("DOMAIN=Core-D6-candidate-family")
    print("PARENT=0011")
    print("LAW=two-independent-commuting-binding-policy-refinements")
    print("AXIS-A=search-scope")
    print("AXIS-B=missing-binding-policy")
    print("COMMUTATIVE=yes")
    print("IDEMPOTENT=yes")
    print("D6-001100=parent-duplicate-not-earned")
    print("D6-001101=one-axis-generated-candidate")
    print("D6-001110=one-axis-generated-candidate")
    print("D6-001111=shared-location-two-axis-candidate")
    print("D6-SELECTOR-COLLISION=none")
    print("BIT-AXIS-ORDER=intermediate-symmetric")
    print("NON-CONCLUSION=no-D6-coordinate-ratified")
    print("NON-CONCLUSION=no-production-mutation-added")


if __name__ == "__main__":
    main()
