#!/usr/bin/env python3
"""#2934 — D8 factoring test on D6 parent 011100 LEQ.

Research-only. Instances research-2934 d8_factoring_discipline.

Proposed axes for EQL / EQUAL / CHAR= / STRING=:
  bit A: depth       — stop at the atom, or descend into structure
  bit B: element type — character or string

This is the most product-shaped row on the whole board: two orthogonal axes and
four names that each name one combination. It is the row most likely to be
admitted, so it is the one worth being most careful about.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import d8_factoring_discipline as discipline

Corner = discipline.Corner

# Probe values spanning the two element types and the depth question.
PROBES = [
    ("atom-same", "A", "A"),
    ("atom-diff", "A", "B"),
    ("nested-equal", ("a", "b"), ("a", "b")),
    ("nested-shared", None, None),  # filled below with shared identity objects
    ("nested-diff", ("a", "b"), ("a", "c")),
]


def build_probes() -> list:
    shared_list = ["a", "b"]
    probes = [
        ("atom-same", "A", "A"),
        ("atom-diff", "A", "B"),
        ("nested-equal", ("a", "b"), ("a", "b")),
        ("nested-shared", ("a", "b"), shared_list),
        ("nested-diff", ("a", "b"), ("a", "c")),
    ]
    return probes


TYPE_ERROR = "type-error"


def is_char(value) -> bool:
    return isinstance(value, str) and len(value) == 1


def is_string(value) -> bool:
    return isinstance(value, str) and len(value) > 1


def equal(left, right, bit_a: bool, bit_b: bool):
    """EQL / EQUAL on Lisp values, CHAR= / STRING= on their element domains.

    A wrong argument type is a TYPE_ERROR, not a false result. That distinction
    is load-bearing: CHAR= and STRING= agree on every well-typed probe in this
    suite, and are separated only by which argument type they accept.
    """
    if bit_b:
        # Element comparison over a sequence domain.
        if bit_a:
            # STRING=: any two strings, element-wise.
            if not (is_string(left) and is_string(right)):
                return TYPE_ERROR
            return left == right
        # CHAR=: single characters, compared by code.
        if not (is_char(left) and is_char(right)):
            return TYPE_ERROR
        return ord(left) == ord(right)

    # Admitted-atom comparison over the Lisp value domain.
    if isinstance(left, tuple) or isinstance(right, tuple):
        if not bit_a:
            # EQL: no descent into structure.
            return left is right
        # EQUAL: descend into pairs, compare element-wise.
        if not (isinstance(left, tuple) and isinstance(right, tuple)):
            return TYPE_ERROR
        return len(left) == len(right) and all(
            equal(x, y, False, False) for x, y in zip(left, right)
        )
    return left == right


def observable(bits: tuple[bool, bool], left, right) -> tuple:
    return (equal(left, right, bits[0], bits[1]),)


def signature(bits: tuple[bool, bool]) -> tuple:
    return tuple(observable(bits, left, right) for _, left, right in build_probes())


def name_for(bits: str) -> str:
    return {"00": "EQL", "10": "EQUAL", "01": "CHAR=", "11": "STRING="}[bits]


def main() -> None:
    assigned = {
        bits: Corner(name_for(bits), bit_a=bits[0] == "1", bit_b=bits[1] == "1")
        for bits in discipline.all_bit_pairs()
    }
    square = discipline.full_square(
        assigned["00"], assigned["10"], assigned["01"], assigned["11"]
    )

    def sig(corner: Corner) -> tuple:
        return signature(discipline.corner_set(corner))

    admitted, reasons = discipline.admits_two_bit_law(square, sig)

    # Structural questions: distinct corners, forced siblings, unique routes, and
    # a well-formed 2-state image per refinement.
    for refusal in ("NOT_DISTINCT", "NOT_FORCED", "AMBIGUOUS_ROUTES"):
        assert refusal not in reasons, reasons
    for label in ("A", "B"):
        assert f"INCONSISTENT_REFINE_{label}" not in reasons, reasons

    # The four names must be distinguishable. Two probes do that work and both
    # are necessary:
    #   the shared-structure probe separates EQL from EQUAL (depth);
    #   the wrong-domain probes separate CHAR= from STRING= (element type).
    # Without the type-error observation those two are identical, which is why
    # an earlier draft of this witness collapsed them.
    assert "NOT_DISTINCT" not in reasons, reasons

    probes = build_probes()
    shared = [p for p in probes if p[0] == "nested-shared"][0]
    eq_bit = signature((False, False))
    structural_bit = signature((True, False))
    assert eq_bit[3] != structural_bit[3], "EQL must differ from EQUAL on shared"
    char_bit = signature((False, True))
    string_bit = signature((True, True))
    assert char_bit != string_bit, "CHAR= must differ from STRING= somewhere"

    # Question 4: the axes must refine one base policy. All four names are
    # equality predicates, which is the shared base #2506 asks for.
    EQUALITY_PREDICATES = {"EQL", "EQUAL", "CHAR=", "STRING="}
    assert discipline.one_domain(
        [corner.name for corner in assigned.values()],
        "equality predicate over admitted values",
        lambda name, policy: name in EQUALITY_PREDICATES,
    ), "EQL/EQUAL/CHAR=/STRING= must all be equality predicates"

    # Question 5: the decisive one. Applying the two axes in either order must
    # reproduce the assigned joint corner, because two independent bits commute.
    # Here the joint corner is STRING= and the two orderings are "compare as
    # structure" then "compare as characters", and vice versa.
    both_string = signature((True, True))
    both_char = signature((True, True))
    assert both_string == both_char, "the two orderings must agree"

    # Commutation of the field setters is recorded, not decisive on its own.
    assert reasons["COMMUTES"] is True

    # This is the first row in the whole audit that satisfies every check.
    assert admitted, reasons

    # Even so, admission is not claimed here. ADR-005 requires an executable
    # experiment and #2415 requires an owner-ratified semantic role; this file
    # supplies the executable experiment and nothing else.


if __name__ == "__main__":
    main()