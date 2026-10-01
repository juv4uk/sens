#!/usr/bin/env python3
"""#1968 research-only: test NULL as a partial refinement action over ATOM.

Candidate law:

    T_empty(P)(x) =
        EQ(x, ())  if P(x) certifies that x is atomic
        NO         otherwise

For P = ATOM this reproduces McCarthy's bounded NULL law:

    NULL(x) = ATOM(x) AND EQ(x, NIL)

The action is intentionally partial at the *predicate* level: it is only
admitted for predicates whose YES result certifies EQ's atomic input domain.
No binary address is allocated here.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGES = ROOT / "docs/research/1962-lisp1-15-edges.tsv"
CORE = ROOT / "lib/core.lisp"
MCCARTHY_TEST = ROOT / "crates/sens/tests/mccarthy_1960_functions.rs"


@dataclass(frozen=True)
class Case:
    name: str
    atomic: bool
    is_empty: bool


CASES = (
    Case("empty-list", True, True),
    Case("symbol", True, False),
    Case("number", True, False),
    Case("one-element-proper-list", False, False),
    Case("multi-element-proper-list", False, False),
    Case("dotted-pair", False, False),
    Case("nested-pair", False, False),
)


def atom(case: Case) -> bool:
    return case.atomic


def eq_empty(case: Case, counters: dict[str, int]) -> bool:
    """Historical EQ-domain model: calling EQ on a pair is a domain error."""
    if not case.atomic:
        raise TypeError("EQ requires atomic operands in the bounded McCarthy model")
    counters["eq_calls"] += 1
    return case.is_empty


def t_empty(predicate, case: Case, counters: dict[str, int]) -> bool:
    """Partial action: predicate YES certifies EQ's atomic input domain."""
    if not predicate(case):
        return False
    return eq_empty(case, counters)


def historical_rows() -> list[dict[str, str]]:
    with EDGES.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return [row for row in rows if row["source"] == "null" and row["rank_edge"] == "1"]


def main() -> None:
    rows = historical_rows()
    by_target = {row["target"]: row for row in rows}

    assert by_target["atom"]["relation"] == "derivable"
    assert by_target["eq"]["relation"] == "derivable"
    assert by_target["nil"]["relation"] == "structure"
    assert "NULL = ATOM(x)" in by_target["atom"]["note"]
    assert "EQ(x,NIL)" in by_target["eq"]["note"]

    counters = {"eq_calls": 0}
    observed = {}
    for case in CASES:
        observed[case.name] = t_empty(atom, case, counters)

    assert observed["empty-list"] is True
    for name, result in observed.items():
        if name != "empty-list":
            assert result is False, (name, result)

    # Only atomic cases reach EQ. Pairs are rejected by ATOM before EQ, proving
    # that the action respects the historical EQ input domain without exceptions.
    atomic_count = sum(1 for case in CASES if case.atomic)
    assert counters["eq_calls"] == atomic_count

    core = CORE.read_text(encoding="utf-8")
    test = MCCARTHY_TEST.read_text(encoding="utf-8")

    assert "(00001001 null?" in core
    assert "fn null_is_true_only_for_the_empty_list()" in test
    assert '(null? (00000001 ()))' in test
    assert '(null? (00000001 a))' in test
    assert '(null? (00000001 (a)))' in test

    # Important research guard: current implementation is not used as proof of
    # the generator formula. It does not literally mention EQ in null?'s body.
    null_start = core.index("(00001001 null?")
    next_definition = core.index("(00001001 subst", null_start)
    null_body = core[null_start:next_definition]
    current_uses_eq = "00000011" in null_body

    print("historical typed relation")
    print("  NULL = ATOM(x) AND EQ(x, NIL)")
    print()
    print("candidate partial action")
    print("  T_empty(P)(x) = EQ(x,()) when P(x)=YES; otherwise NO")
    print("  domain condition: P's YES must certify atomic input")
    print()
    print("bounded truth-domain witness")
    for case in CASES:
        print(
            f"  {case.name:28} atom={int(case.atomic)} "
            f"empty={int(case.is_empty)} null={int(observed[case.name])}"
        )
    print(f"  guarded EQ calls: {counters['eq_calls']} (atomic cases only)")
    print()
    print("current-source cross-check")
    print("  null? definition present: yes")
    print("  extensional regression test present: yes")
    print(f"  current null? body literally uses EQ: {'yes' if current_uses_eq else 'no'}")
    print()
    print("RESULT")
    print("  positive typed-action candidate: ATOM -> NULL by empty-ground refinement")
    print("  status: strong-semantic CANDIDATE, not allocated")
    print("  current implementation path is not taken as semantic proof;")
    print("  historical law + guarded domain witness are the evidence.")
    print("  falsifier: any admitted value for which NULL differs from this refinement,")
    print("  or any future ATOM YES value outside EQ's admitted atomic domain.")


if __name__ == "__main__":
    main()
