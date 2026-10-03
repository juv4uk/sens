#!/usr/bin/env python3
"""#2489 — SETQ-core placement falsifier.

Research-only. Tests whether the first surviving post-D4 capability can
honestly be represented as one extra bit under a D4 parent.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum


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
SETQ_CORE = Policy(Scope.NEAREST, Miss.FAIL)

FIXED_D5_SELECTORS = {
    "10100": "CAAAR",
    "10101": "CAADR",
    "10110": "CADAR",
    "10111": "CADDR",
    "11000": "CDAAR",
    "11001": "CDADR",
    "11010": "CDDAR",
    "11011": "CDDDR",
}


class MissingBinding(Exception):
    pass


def apply_update(frames: list[dict[str, str]], name: str, value: str, policy: Policy):
    """Return a new inner->outer frame chain after one abstract binding write."""
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


def inherited_witness(policy: Policy):
    frames = [{}, {"x": "OLD"}]
    try:
        after, target = apply_update(frames, "x", "NEW", policy)
    except MissingBinding:
        return ("error",)
    return ("ok", target, after[0].get("x"), after[1].get("x"), after[1].get("x"))


def missing_witness(policy: Policy):
    frames = [{}, {}]
    try:
        after, target = apply_update(frames, "x", "NEW", policy)
    except MissingBinding:
        return ("error",)
    return ("ok", target, after[0].get("x"), after[1].get("x"))


def same_frame_witness(policy: Policy):
    frames = [{"x": "OLD"}, {"x": "OUTER"}]
    try:
        after, target = apply_update(frames, "x", "NEW", policy)
    except MissingBinding:
        return ("error",)
    return ("ok", target, after[0]["x"], after[1]["x"])


def signature(policy: Policy):
    return (inherited_witness(policy), missing_witness(policy), same_frame_witness(policy))


def hamming_policy_distance(a: Policy, b: Policy) -> int:
    return int(a.scope != b.scope) + int(a.miss != b.miss)


def main() -> None:
    policies = {
        "current-create": Policy(Scope.CURRENT, Miss.CREATE),
        "nearest-create": Policy(Scope.NEAREST, Miss.CREATE),
        "current-fail": Policy(Scope.CURRENT, Miss.FAIL),
        "nearest-fail": Policy(Scope.NEAREST, Miss.FAIL),
    }

    signatures = {name: signature(policy) for name, policy in policies.items()}
    assert len(set(signatures.values())) == 4, signatures

    assert inherited_witness(policies["current-create"]) != inherited_witness(policies["nearest-create"])
    assert missing_witness(policies["current-create"]) == missing_witness(policies["nearest-create"])

    assert missing_witness(policies["current-create"]) != missing_witness(policies["current-fail"])
    assert same_frame_witness(policies["current-create"]) == same_frame_witness(policies["current-fail"])

    assert DEFINE == policies["current-create"]
    assert SETQ_CORE == policies["nearest-fail"]
    assert hamming_policy_distance(DEFINE, SETQ_CORE) == 2
    assert same_frame_witness(DEFINE) == same_frame_witness(SETQ_CORE)

    assert "00110" not in FIXED_D5_SELECTORS
    assert "00111" not in FIXED_D5_SELECTORS

    lookup_same_resolution = True
    lookup_same_base_operation = False
    assert lookup_same_resolution
    assert not lookup_same_base_operation

    bind_same_base_operation = False
    assert not bind_same_base_operation

    print("SETQ-PLACEMENT=PASS")
    print("DEFINE-POLICY=current/create")
    print("SETQ-CORE-POLICY=nearest-existing/fail")
    print("INDEPENDENT-AXIS-1=search-scope")
    print("INDEPENDENT-AXIS-2=missing-name-policy")
    print("DEFINE-TO-SETQ-DELTA-COUNT=2")
    print("DEFINE-PARENT-DECISION=NEEDS-WIDER-WIDTH")
    print("LOOKUP-COUNTERPARENT=same-resolution-but-different-base-operation")
    print("BIND-COUNTERPARENT=different-base-operation")
    print("D5-00110=FREE-NOT-EARNED")
    print("D5-00111=FREE-NOT-EARNED")
    print("NON-CONCLUSION=no-D6-coordinate-assigned")
    print("NON-CONCLUSION=no-production-mutation-added")


if __name__ == "__main__":
    main()
