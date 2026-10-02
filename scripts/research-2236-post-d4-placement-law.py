#!/usr/bin/env python3
"""#2236 — post-D4 placement-law falsifier.

Research-only. This script does not ratify any new non-selector D5 identity.
It checks whether a historical candidate earns a child address by the rule:

    parent + exactly one observable semantic delta -> width+1 child

History selects the candidate order. Executable semantic evidence decides
derivability and parenthood. Empty addresses are valid outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    DERIVED = "DERIVED"
    HISTORICAL_MECHANISM = "HISTORICAL-MECHANISM"
    GENERATED_CHILD_0 = "GENERATED-CHILD-0"
    GENERATED_CHILD_1 = "GENERATED-CHILD-1"
    RESIDUE = "RESIDUE"
    NEEDS_WIDER_WIDTH = "NEEDS-WIDER-WIDTH"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class Candidate:
    name: str
    era: str
    d1_d4_derivable: bool | None
    historical_mechanism_only: bool = False
    strongest_parent: str | None = None
    same_base_object: bool | None = None
    one_new_delta: bool | None = None
    delta_axes: tuple[str, ...] = ()
    suffix_0_fit: bool = False
    suffix_1_fit: bool = False
    delta: str = ""


D4 = {
    "0000": "APPLY",
    "0001": "EVAL",
    "0010": "LAMBDA",
    "0011": "DEFINE",
    "0100": "NOT",
    "0110": "EVCON",
    "0111": "EVLIS",
    "1000": "LIST",
    "1010": "CAAR",
    "1011": "CADR",
    "1100": "CDAR",
    "1101": "CDDR",
    "1110": "LOOKUP",
    "1111": "BIND",
}

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


def classify(candidate: Candidate) -> Decision:
    if candidate.historical_mechanism_only:
        return Decision.HISTORICAL_MECHANISM

    if candidate.d1_d4_derivable is True:
        return Decision.DERIVED

    if candidate.d1_d4_derivable is None:
        return Decision.UNRESOLVED

    if candidate.strongest_parent is None:
        return Decision.RESIDUE

    assert candidate.strongest_parent in D4, (
        f"{candidate.name}: unknown D4 parent {candidate.strongest_parent}"
    )

    if candidate.same_base_object is not True:
        return Decision.RESIDUE

    if candidate.one_new_delta is not True:
        return Decision.NEEDS_WIDER_WIDTH

    assert len(candidate.delta_axes) == 1, (
        f"{candidate.name}: a one-bit generated child must name exactly one "
        f"independent observable delta axis, got {candidate.delta_axes}"
    )

    if candidate.suffix_0_fit and not candidate.suffix_1_fit:
        return Decision.GENERATED_CHILD_0

    if candidate.suffix_1_fit and not candidate.suffix_0_fit:
        return Decision.GENERATED_CHILD_1

    return Decision.RESIDUE


def generated_word(candidate: Candidate, decision: Decision) -> str | None:
    if decision is Decision.GENERATED_CHILD_0:
        assert candidate.strongest_parent is not None
        return candidate.strongest_parent + "0"
    if decision is Decision.GENERATED_CHILD_1:
        assert candidate.strongest_parent is not None
        return candidate.strongest_parent + "1"
    return None


def assert_no_collision(word: str | None, name: str) -> None:
    if word is None:
        return
    assert word not in FIXED_D5_SELECTORS, (
        f"{name}: candidate {word} collides with fixed selector "
        f"{FIXED_D5_SELECTORS[word]}"
    )


def assert_unique_generated_child(
    first: Candidate,
    second: Candidate,
    first_decision: Decision,
    second_decision: Decision,
) -> None:
    first_word = generated_word(first, first_decision)
    second_word = generated_word(second, second_decision)
    if first_word is None or second_word is None:
        return
    assert not (
        first_word == second_word and first.delta_axes != second.delta_axes
    ), (
        f"{first.name} and {second.name} demand the same exact child "
        f"{first_word} for independent delta axes "
        f"{first.delta_axes} vs {second.delta_axes}; one extra bit cannot "
        "encode two unrelated refinements"
    )


def main() -> None:
    # Positive control: if LABEL is proven irreducible exactly as
    # "LAMBDA closure + local self-reference binding", the placement law
    # derives 00101 rather than choosing it by spare capacity.
    label_if_gap = Candidate(
        name="LABEL",
        era="Lisp-I-1960",
        d1_d4_derivable=False,
        strongest_parent="0010",
        same_base_object=True,
        one_new_delta=True,
        delta_axes=("local-self-binding",),
        suffix_1_fit=True,
        delta="add local recursive self-binding to closure environment",
    )
    label_gap_decision = classify(label_if_gap)
    assert label_gap_decision is Decision.GENERATED_CHILD_1
    label_gap_word = generated_word(label_if_gap, label_gap_decision)
    assert label_gap_word == "00101"
    assert_no_collision(label_gap_word, "LABEL")

    # Historical-reset collision control: the old macro-first TRANSFORMER
    # hypothesis wanted the same LAMBDA+suffix-1 address for a different
    # semantic axis (raw/staged invocation). If both LABEL recursion and
    # TRANSFORMER staging survive as independent observable deltas, D5 cannot
    # encode both under the same parent/suffix. One must derive, find another
    # honest parent, or move to a wider representation.
    transformer_if_gap = Candidate(
        name="TRANSFORMER",
        era="post-Lisp-1.5-macro",
        d1_d4_derivable=False,
        strongest_parent="0010",
        same_base_object=True,
        one_new_delta=True,
        delta_axes=("raw-staged-invocation",),
        suffix_1_fit=True,
        delta="change ordinary eager closure invocation to raw staged invocation",
    )
    transformer_decision = classify(transformer_if_gap)
    assert transformer_decision is Decision.GENERATED_CHILD_1
    assert generated_word(transformer_if_gap, transformer_decision) == "00101"

    collision_detected = False
    try:
        assert_unique_generated_child(
            label_if_gap,
            transformer_if_gap,
            label_gap_decision,
            transformer_decision,
        )
    except AssertionError:
        collision_detected = True
    assert collision_detected

    # Strong falsifier: if #2234 proves LABEL derivable from D4, no address
    # is admitted and 00101 remains empty.
    label_if_derived = Candidate(
        name="LABEL",
        era="Lisp-I-1960",
        d1_d4_derivable=True,
        strongest_parent="0010",
        same_base_object=True,
        one_new_delta=True,
        delta_axes=("local-self-binding",),
        suffix_1_fit=True,
        delta="would be local recursive self-binding",
    )
    assert classify(label_if_derived) is Decision.DERIVED
    assert generated_word(label_if_derived, classify(label_if_derived)) is None

    # Counterplacement: LABEL under DEFINE is not currently admitted as a
    # one-delta child because persistent/global definition and local recursive
    # closure identity are not the same base semantic object.
    label_under_define = Candidate(
        name="LABEL@DEFINE-countermodel",
        era="Lisp-I-1960",
        d1_d4_derivable=False,
        strongest_parent="0011",
        same_base_object=False,
        one_new_delta=False,
        delta_axes=("base-object-kind", "binding-lifetime", "local-self-reference"),
        suffix_0_fit=False,
        suffix_1_fit=False,
        delta="global/persistent binding -> local recursive closure is not proven",
    )
    assert classify(label_under_define) is Decision.RESIDUE

    # Current historical ladder remains intentionally unresolved until its
    # executable witnesses run. The script records search order, not outcomes.
    resolved_label = Candidate(
        "LABEL",
        "Lisp-I-1960",
        True,
        strongest_parent="0010",
        same_base_object=True,
        one_new_delta=True,
        delta_axes=("local-self-binding",),
        suffix_1_fit=True,
        delta="local recursion is derivable through D4 applicative fixed point",
    )
    assert classify(resolved_label) is Decision.DERIVED
    assert generated_word(resolved_label, classify(resolved_label)) is None

    ladder = [
        Candidate("FUNCTION/FUNARG", "Lisp-1.5", None, strongest_parent="0010"),
        Candidate("EVALQUOTE", "Lisp-1.5", None, strongest_parent="0001"),
        Candidate("APPEND", "Lisp-I-1960", None),
        Candidate("PAIR/PAIRLIS", "Lisp-I/Lisp-1.5", None, strongest_parent="1111"),
        Candidate("ASSOC", "Lisp-I-1960", None, strongest_parent="1110"),
        Candidate("SUBST/SUBLIS", "Lisp-I/Lisp-1.5", None),
        Candidate("MAPLIST", "Lisp-I/Lisp-1.5", None),
        Candidate("SET/SETQ", "Lisp-1.5", None, strongest_parent="0011"),
        Candidate("PROG/GO/RETURN", "Lisp-1.5", None),
    ]

    for candidate in ladder:
        assert classify(candidate) is Decision.UNRESOLVED

    # Free D4 capacity is not a placement theorem.
    for allocation_only in ("0101", "1001"):
        assert allocation_only not in D4
        assert len(allocation_only) == 4

    print("POST-D4-PLACEMENT-LAW=PASS")
    print("LAW=parent+one-observable-delta")
    print("HISTORY=chooses-candidate-order")
    print("PLACEMENT=requires-executable-local-generator")
    print("FREE-SLOT-ALLOCATION=FORBIDDEN")
    print("LABEL-IF-DERIVED=NO-ADDRESS")
    print("LABEL-IF-ONE-DELTA-GAP=00101")
    print("LABEL-LAMBDA-DELTA-AXES=local-self-binding")
    print("LABEL-DEFINE-DELTA-AXES=base-object-kind,binding-lifetime,local-self-reference")
    print("LABEL-DEFINE-COUNTERMODEL=RESIDUE")
    print("LAMBDA-SUFFIX1-COLLISION=LABEL-vs-TRANSFORMER")
    print("COLLISION-RESULT=derive-or-reparent-or-widen")
    print("FIXED-D5-SELECTORS=" + ",".join(sorted(FIXED_D5_SELECTORS)))
    print("RESOLVED-LABEL=DERIVED-D4")
    print("RESOLVED-LABEL-ADDRESS=NONE")
    print("UNRESOLVED-LADDER=" + ",".join(c.name for c in ladder))
    print("NON-CONCLUSION: 00101 LABEL is not ratified")
    print("NON-CONCLUSION: no global D5 suffix theorem is claimed")


if __name__ == "__main__":
    main()
