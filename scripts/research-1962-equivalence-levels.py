#!/usr/bin/env python3
"""#1962: typed equivalence guard for domain-graph research.

Research-only. The point is deliberately small:

    implementation equality
    observational equality on a declared domain
    semantic identity

are three different claims. Only semantic identity permits graph-node quotient.

Evidence anchors:
- experiments/function-genealogy.lisp
- docs/architecture/PRIMITIVE-BUDGET-AUDIT-734.md
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Relation:
    left: str
    right: str
    implementation_equal: bool
    observational_domain: str | None
    semantic_identical: bool
    note: str

    @property
    def may_share_executable_path(self) -> bool:
        return self.implementation_equal

    @property
    def may_quotient_semantic_nodes(self) -> bool:
        return self.semantic_identical


CASES = (
    Relation(
        left="second",
        right="cadr",
        implementation_equal=True,
        observational_domain="proper-list",
        semantic_identical=False,
        note="same current CAR∘CDR body; sequence ordinal vs pair-navigation intent",
    ),
    Relation(
        left="pair",
        right="list",
        implementation_equal=False,
        observational_domain="exactly-two-arguments",
        semantic_identical=False,
        note="same observed result at arity 2; binary constructor vs variadic list constructor",
    ),
)


def main() -> None:
    print("left\tright\timpl-equal\tobservational-domain\tsemantic-identical\tshare-path\tquotient")
    for rel in CASES:
        print(
            f"{rel.left}\t{rel.right}\t{int(rel.implementation_equal)}\t"
            f"{rel.observational_domain or '-'}\t{int(rel.semantic_identical)}\t"
            f"{int(rel.may_share_executable_path)}\t{int(rel.may_quotient_semantic_nodes)}"
        )

    second_cadr = CASES[0]
    assert second_cadr.may_share_executable_path
    assert not second_cadr.may_quotient_semantic_nodes

    pair_list = CASES[1]
    assert pair_list.observational_domain == "exactly-two-arguments"
    assert not pair_list.may_share_executable_path
    assert not pair_list.may_quotient_semantic_nodes

    # Core guard: weaker evidence must never silently become semantic identity.
    for rel in CASES:
        if rel.observational_domain is not None or rel.implementation_equal:
            if not rel.semantic_identical:
                assert not rel.may_quotient_semantic_nodes

    print("\nRESULT: path sharing and semantic quotient remain distinct; no weak overlap is quotiented.")


if __name__ == "__main__":
    main()
