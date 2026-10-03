#!/usr/bin/env python3
"""#2506 helper witness: binding-policy factor commutativity/orientation.

Research-only. Reuses the already-merged #2492 policy model and asks whether
the two independently observed deltas form a product square. No D6 identity is
admitted here.
"""

from __future__ import annotations

import importlib.util
from itertools import permutations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT / "scripts" / "research-2489-setq-placement.py"


def load_donor():
    spec = importlib.util.spec_from_file_location("setq_2489", DONOR)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def refine_scope(mod, policy):
    return mod.Policy(mod.Scope.NEAREST, policy.miss)


def refine_miss(mod, policy):
    return mod.Policy(policy.scope, mod.Miss.FAIL)


def coordinate(policy, *, scope_first: bool) -> str:
    scope_bit = "0" if policy.scope.value == "current" else "1"
    miss_bit = "0" if policy.miss.value == "create" else "1"
    suffix = scope_bit + miss_bit if scope_first else miss_bit + scope_bit
    return "0011" + suffix


def main() -> None:
    mod = load_donor()

    corners = {
        "current/create": mod.Policy(mod.Scope.CURRENT, mod.Miss.CREATE),
        "current/fail": mod.Policy(mod.Scope.CURRENT, mod.Miss.FAIL),
        "nearest/create": mod.Policy(mod.Scope.NEAREST, mod.Miss.CREATE),
        "nearest/fail": mod.Policy(mod.Scope.NEAREST, mod.Miss.FAIL),
    }

    # The donor already proves the four corners are observably distinct.
    signatures = {name: mod.signature(policy) for name, policy in corners.items()}
    assert len(set(signatures.values())) == 4

    # Independent factor transforms commute everywhere and are idempotent.
    for policy in corners.values():
        assert refine_scope(mod, refine_miss(mod, policy)) == refine_miss(
            mod, refine_scope(mod, policy)
        )
        assert refine_scope(mod, refine_scope(mod, policy)) == refine_scope(mod, policy)
        assert refine_miss(mod, refine_miss(mod, policy)) == refine_miss(mod, policy)

    define = corners["current/create"]
    target = corners["nearest/fail"]
    assert define == mod.DEFINE
    assert target == mod.SETQ_CORE

    # Parent preservation: zero deltas are exactly the D4 parent semantics.
    assert coordinate(define, scope_first=True) == "001100"
    assert coordinate(define, scope_first=False) == "001100"

    # Applying both factors reaches the same semantic target regardless of order.
    via_scope_then_miss = refine_miss(mod, refine_scope(mod, define))
    via_miss_then_scope = refine_scope(mod, refine_miss(mod, define))
    assert via_scope_then_miss == via_miss_then_scope == target

    # The target corner is invariant under coordinate-axis order because it is 11.
    assert coordinate(target, scope_first=True) == "001111"
    assert coordinate(target, scope_first=False) == "001111"

    # The two intermediate corners swap binary positions when axis order swaps.
    current_fail = corners["current/fail"]
    nearest_create = corners["nearest/create"]
    assert coordinate(current_fail, scope_first=True) == "001101"
    assert coordinate(nearest_create, scope_first=True) == "001110"
    assert coordinate(current_fail, scope_first=False) == "001110"
    assert coordinate(nearest_create, scope_first=False) == "001101"

    # Enumerate the two admissible axis-order encodings that preserve:
    # parent=00, target=11, and one bit per independent semantic axis.
    encodings = {
        "scope-then-miss": {name: coordinate(p, scope_first=True) for name, p in corners.items()},
        "miss-then-scope": {name: coordinate(p, scope_first=False) for name, p in corners.items()},
    }
    assert len({tuple(sorted(m.items())) for m in encodings.values()}) == 2

    # Falsifier: arbitrary middle-corner mapping that duplicates one coordinate
    # breaks injectivity/product structure.
    bad = {
        "current/create": "001100",
        "current/fail": "001101",
        "nearest/create": "001101",
        "nearest/fail": "001111",
    }
    assert len(set(bad.values())) != 4

    # Falsifier: a local exception for one path destroys path consistency.
    path_a = coordinate(via_scope_then_miss, scope_first=True)
    path_b = coordinate(via_miss_then_scope, scope_first=True)
    assert path_a == path_b == "001111"
    local_exception_path_b = "001110"
    assert path_a != local_exception_path_b

    print("D6-BINDING-POLICY-FACTOR-AUDIT=PASS")
    print("COMMUTES=YES")
    print("SCOPE-REFINEMENT-IDEMPOTENT=YES")
    print("MISS-REFINEMENT-IDEMPOTENT=YES")
    print("PARENT-00=001100")
    print("TARGET-11=001111")
    print("TARGET-INVARIANT-UNDER-AXIS-ORDER=YES")
    print("MIDDLE-CHILDREN-SWAP-UNDER-AXIS-ORDER=YES")
    print("AXIS-BIT-POSITION-ORIENTATION=NOT-FORCED-BY-PRODUCT-LAW")
    print("PRODUCT-STRUCTURE=BOUNDED-WITNESSED")
    print("D6-ADMISSION=NONE")
    print("RELATION=CORE-ONLY")
    print("NON-CONCLUSION=001101/001110 meanings remain orientation-dependent")
    print("NON-CONCLUSION=full D6 generator admission not decided here")


if __name__ == "__main__":
    main()
