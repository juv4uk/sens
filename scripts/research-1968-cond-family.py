#!/usr/bin/env python3
"""#1968 — bounded COND-family falsifier under answer-contract/2.

Research-only. This tests an attractive local-family hypothesis before any
allocation:

    1110 -> predicate AND
    1111 -> predicate OR

The model is intentionally tiny and follows the current shared answer contract:
- predicate answers are exact one-bit 0/1;
- structural () is not predicate FALSE;
- COND has only (test expression) clauses;
- COND selects on 1, skips on 0, and exhaustion returns structural ().

If AND/OR need another root merely to manufacture PredicateBit(0), they are not
strong local children of COND under this bounded criterion.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/answer-contract.lisp"


@dataclass(frozen=True)
class PredicateBit:
    bit: int

    def __post_init__(self) -> None:
        if self.bit not in (0, 1):
            raise ValueError(self.bit)


@dataclass(frozen=True)
class StructuralEmpty:
    pass


EMPTY = StructuralEmpty()
P0 = PredicateBit(0)
P1 = PredicateBit(1)


def verify_contract_anchor() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    required = (
        "(predicate-answer . no)",
        "(false-sentinel . no)",
        "(result-form . predicate-one-bit)",
        "(select-on . one)",
        "(skip-on . zero)",
        "(exhaustion-result . structural-empty)",
        "(three-part-clause . forbidden)",
        "(generic-truthiness . forbidden)",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError(f"answer-contract anchors changed/missing: {missing}")


def cond2(clauses: list[tuple[PredicateBit, object]]) -> object:
    """Exact answer-contract/2 control model."""
    for test, expression in clauses:
        if not isinstance(test, PredicateBit):
            raise TypeError("COND test must be PredicateBit")
        if test.bit == 1:
            return expression
    return EMPTY


def expected_and(p: PredicateBit, q: PredicateBit) -> PredicateBit:
    return P1 if p.bit == 1 and q.bit == 1 else P0


def expected_or(p: PredicateBit, q: PredicateBit) -> PredicateBit:
    return P1 if p.bit == 1 or q.bit == 1 else P0


def naive_and_via_cond(p: PredicateBit, q: PredicateBit) -> object:
    # Attractive short-circuit form: if p then q, otherwise exhaustion.
    return cond2([(p, q)])


def naive_or_via_cond(p: PredicateBit, q: PredicateBit) -> object:
    # If either input is YES return YES; otherwise exhaustion.
    return cond2([(p, P1), (q, P1)])


def truth_table(candidate, expected):
    rows = []
    for p in (P0, P1):
        for q in (P0, P1):
            got = candidate(p, q)
            want = expected(p, q)
            rows.append((p.bit, q.bit, got, want, got == want))
    return rows


def render(value: object) -> str:
    if value == EMPTY:
        return "()"
    if isinstance(value, PredicateBit):
        return str(value.bit)
    return repr(value)


def main() -> None:
    verify_contract_anchor()
    assert EMPTY != P0
    assert EMPTY != P1

    and_rows = truth_table(naive_and_via_cond, expected_and)
    or_rows = truth_table(naive_or_via_cond, expected_or)

    print("candidate\tp\tq\tgot\texpected\tmatch")
    for name, rows in (("AND", and_rows), ("OR", or_rows)):
        for p, q, got, want, ok in rows:
            print(
                f"{name}\t{p}\t{q}\t{render(got)}\t{render(want)}\t"
                f"{str(ok).lower()}"
            )

    and_fail = [row for row in and_rows if not row[-1]]
    or_fail = [row for row in or_rows if not row[-1]]

    assert len(and_fail) == 2  # p=0, either q: exhaustion () != PredicateBit 0
    assert len(or_fail) == 1   # p=q=0: exhaustion () != PredicateBit 0

    print()
    print("bounded classification")
    print("COND -> predicate AND : attractive partial-specialization law FALSIFIED")
    print("COND -> predicate OR  : attractive partial-specialization law FALSIFIED")
    print("reason: structural () is not PredicateBit(0)")
    print("1110/1111             : remain unallocated by this experiment")

    print()
    print("repair analysis")
    print(
        "A correct total PredicateBit connective would need an explicit way to "
        "produce PredicateBit(0) on the skipped/exhausted path."
    )
    print(
        "Under answer-contract/2, source cannot use structural () as that value; "
        "adding EQ/other predicate machinery would make the construction multi-root."
    )
    print(
        "Therefore the current bounded evidence supports at most a typed control "
        "relationship, not a selector-strength local COND child law."
    )

    print()
    print("PASS: the falsifier preserves the () != 0 boundary and rejects the")
    print("tempting AND/OR allocation instead of weakening predicate semantics.")


if __name__ == "__main__":
    main()
