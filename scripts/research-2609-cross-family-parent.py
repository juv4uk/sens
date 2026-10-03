#!/usr/bin/env python3
"""#2609 — typed same-base guard for post-D4 structural factors.

Research-only. This checker does not define runtime types and does not allocate
D5/D6 coordinates. It makes one #2236 precondition executable:

    a generated child must refine the same base semantic object/operation.

Cross-family vocabulary overlap ("context", "environment", "state") is not
same-base evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations


@dataclass(frozen=True)
class Family:
    id: str
    domain: str
    base_carrier: str
    operation_shape: str
    observable: tuple[bool, bool, bool]
    evidence: str


MUTATION = Family(
    id="mutation",
    domain="Core.PostD4.MutationFamily",
    base_carrier="shared-store/location",
    operation_shape="(store,target,value)->updated-store",
    observable=(True, False, False),  # store change, continuation skip, syntax protocol
    evidence="#2604 + #2589 donors",
)

NONLOCAL = Family(
    id="non-local-control",
    domain="Core.PostD4.NonLocalControl",
    base_carrier="dynamic-exit-context",
    operation_shape="(value,exit-context)->non-local-transfer",
    observable=(False, True, False),
    evidence="#2604 + #2590 donors",
)

SPECIAL = Family(
    id="special-call-protocol",
    domain="Core.PostD4.SpecialCallProtocol",
    base_carrier="source-invocation/caller-context",
    operation_shape="(syntax,caller-context)->value-or-replacement-form",
    observable=(False, False, True),
    evidence="#2522/#2597/#2588 donors",
)

FAMILIES = (MUTATION, NONLOCAL, SPECIAL)


def same_base(a: Family, b: Family) -> bool:
    return (
        a.domain == b.domain
        and a.base_carrier == b.base_carrier
        and a.operation_shape == b.operation_shape
    )


def typed_apply(law_owner: Family, object_owner: Family) -> str:
    return "DOMAIN-VALID" if law_owner.domain == object_owner.domain else "DOMAIN-MISMATCH"


def parent_verdict(parent: Family, child: Family) -> str:
    if same_base(parent, child):
        return "SAME-FAMILY-CANDIDATE"
    return "NO-PROVED-SAME-BASE-PARENT"


def main() -> None:
    # #2604 positive orthogonality control: mutation and non-local exit have
    # different observable signatures, neither subsumes the other.
    assert MUTATION.observable == (True, False, False)
    assert NONLOCAL.observable == (False, True, False)
    assert SPECIAL.observable == (False, False, True)
    assert len({family.observable for family in FAMILIES}) == 3

    # Standing #2508 domain firewall: each family's law applies locally and
    # fails closed on every other declared family.
    for family in FAMILIES:
        assert typed_apply(family, family) == "DOMAIN-VALID"

    cross_rows = []
    for parent, child in permutations(FAMILIES, 2):
        assert typed_apply(parent, child) == "DOMAIN-MISMATCH"
        assert not same_base(parent, child)
        verdict = parent_verdict(parent, child)
        assert verdict == "NO-PROVED-SAME-BASE-PARENT"
        cross_rows.append(
            (
                parent.id,
                child.id,
                "no",
                "no",
                "DOMAIN-MISMATCH",
                verdict,
            )
        )

    assert len(cross_rows) == 6

    # Positive placement-law control: a same-family classification is only a
    # prerequisite, never an automatic one-bit child theorem. DEFINE/SETQ is
    # the canonical example: same mutation/binding family, yet #2492/#2518
    # found two independently observable policy deltas.
    define_setq_same_family = True
    define_setq_delta_count = 2
    assert define_setq_same_family
    assert define_setq_delta_count > 1

    print("CROSS-FAMILY-PARENT-GUARD=PASS")
    print("parent\tchild\tsame-base-carrier\tsame-base-operation\tdomain-firewall\tparenthood")
    for row in cross_rows:
        print("\t".join(row))
    print("POSITIVE-CONTROL=DEFINE-SETQ-SAME-FAMILY-BUT-TWO-DELTAS")
    print("ROOTS-PROVEN=0")
    print("D5-RESIDENTS=0")
    print("COORDINATES-ALLOCATED=0")
    print("WIDTH-INFERENCE=NONE")
    print("RULE=same-family-is-necessary-not-sufficient-for-generated-child")


if __name__ == "__main__":
    main()
