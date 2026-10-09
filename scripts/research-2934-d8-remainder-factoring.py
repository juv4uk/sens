#!/usr/bin/env python3
"""#2934 — D8 factoring test on D6 parent 100110 REMAINDER.

Research-only. Instances research-2934-d8-factoring-discipline.

Proposed axes for DIV / REM / CHAR-CODE / CODE-CHAR:
  bit A: quotient-like  — produce a numeric decomposition
  bit B: invertible      — a round-trip partner exists

This row is instructive because it contains two genuine inverse pairs, which is
the shape most likely to be mistaken for a product.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import d8_factoring_discipline as discipline

Corner = discipline.Corner


def make(bit_a: bool, bit_b: bool) -> Corner:
    return Corner("", bit_a=bit_a, bit_b=bit_b)


def name_for(bits: str) -> str:
    return {"00": "DIV", "10": "REM", "01": "CHAR-CODE", "11": "CODE-CHAR"}[bits]


def observable(bits: tuple[bool, bool], number: int, char: str) -> tuple:
    """Return what the operation does, judged on a numeric and a char input."""
    bit_a, bit_b = bits
    if bit_a and bit_b:
        return ("char-round-trip", ord(char), chr(ord(char)))
    if bit_a:
        return ("remainder", number % 7)
    if bit_b:
        return ("codepoint", ord(char))
    return ("quotient", number // 7)


def signature(bits: tuple[bool, bool]) -> tuple:
    probes = [(21, "A"), (-21, "Z"), (0, "0")]
    return tuple(observable(bits, n, c) for n, c in probes)


def corner_for(bits: str) -> Corner:
    return Corner(name_for(bits), bit_a=bits[0] == "1", bit_b=bits[1] == "1")


def main() -> None:
    assigned = {bits: corner_for(bits) for bits in discipline.all_bit_pairs()}
    assert set(assigned) == {"00", "01", "10", "11"}, sorted(assigned)
    square = discipline.full_square(
        assigned["00"],
        assigned["10"],
        assigned["01"],
        assigned["11"],
    )

    def sig(corner: Corner) -> tuple:
        return signature(discipline.corner_set(corner))

    admitted, reasons = discipline.admits_two_bit_law(square, sig)

    # Every structural test passes on this row: the four corners are distinct,
    # both axes are forced, and no two corners collide. An earlier version of
    # this witness refused the row on injectivity, which was a false test.
    assert "NOT_DISTINCT" not in reasons, reasons
    assert "NOT_FORCED" not in reasons, reasons
    assert "AMBIGUOUS_ROUTES" not in reasons, reasons

    # Note what is deliberately absent here: an "ill-typed composition" argument.
    # An earlier draft claimed DIV composed with CHAR-CODE raises a TypeError,
    # which was false because both return integers. Only the shared-base
    # question below carries the refutation, so only it is asserted.
    #
    # The disqualifier is the fifth question. DIV/REM and CHAR-CODE/CODE-CHAR are
    # each a genuine binary pair, so their 2x2 is a real cartesian product and
    # every structural test passes. But the two pairs share no base policy: one
    # is arithmetic, the other is character encoding. Four names that pair up by
    # counting to two and two is an accident, not a two-bit law.
    EQUALITY_PREDICATES = {"EQL", "EQUAL", "CHAR=", "STRING="}
    shared_base = discipline.one_domain(
        [corner.name for corner in assigned.values()],
        "equality predicate over admitted values",
        lambda name, policy: name in EQUALITY_PREDICATES,
    )
    assert not shared_base, "DIV/REM and CHAR-CODE/CODE-CHAR share no base policy"

    # Structural admission is therefore a necessary but not sufficient condition:
    # the framework admits this row, and the row is still not a D8 law.

    # DIV and REM are both quotient-like, so bit A cannot tell them apart in
    # kind: they differ by which half of the division they keep.
    assert discipline.corner_set(assigned["00"]) == (False, False)
    assert discipline.corner_set(assigned["10"]) == (True, False)

    # Commutation of field setters is recorded but never decisive here.
    assert reasons["COMMUTES"] is True


if __name__ == "__main__":
    main()