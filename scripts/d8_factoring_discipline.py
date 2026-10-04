#!/usr/bin/env python3
"""#2934 — shared two-bit factoring discipline for D8 parents.

Importable as `d8_factoring_discipline`; no hyphenated module names in Python.

Research-only. A parent admits a D8 child only if its four attested names form a
clean 2x2 product of two independent one-bit refinements, in the discipline of
#2506. This module encodes that discipline once so each parent is an instance
rather than a hand-written copy.

Five independent questions, each with its own falsifier:

  distinct    the four corners are observationally distinguishable
  forced      each axis flips exactly one bit of the 00 parent corner
  routes      no two corners share one coordinate
  consistent  each refinement reaches the 2-state image a real bit produces
  compose     applying the two named operations reproduces the 11 corner, in
              either order

Why the counting test exists. Setting one bit of a genuine 2x2 product and asking
how many distinct states result is a test with a fixed answer: setting bit A maps
(0,0)->(1,0), (1,0)->(1,0), (0,1)->(1,1), (1,1)->(1,1), so it always reaches
exactly 2 of 4. An earlier version of this module demanded 4, which made the
criterion unsatisfiable and turned a false test into five apparent refutations.
The count carries information only if it deviates from 2.

`compose` is the decisive question, and no structural test can see it. Two
independent bits must commute, so applying A then B to the parent must give the
same observable behaviour as the assigned `11` corner.
FLOOR/CEILING/TRUNCATE/ROUND fails exactly here:

```text
x=  7/2   toward-zero then toward-+inf = 3    ROUND = 4
x= -7/2   toward-+inf then toward-zero = -3   ROUND = -4
```

The two orderings disagree with each other *and* with ROUND. Rounding direction
and rounding style are not independent bits; they are two answers to one
question, "where does the remainder go".

A fifth question is needed beyond composition, because a row can satisfy all four
structural questions and still be an accident. REMAINDER is the case: DIV/REM
and CHAR-CODE/CODE-CHAR are each a genuine binary pair, so their 2x2 is a real
cartesian product, but the two pairs share no domain. A quotient and a character
code have nothing to compose, so the joint corner is unreachable rather than
merely wrong. The test is `one_domain`: the axes must be refinements of a single
base policy, which is what #2506 asks for and what a cartesian product of
unrelated pairs is not.

A row passes when all five hold.

A subtlety that produced two wrong verdicts during development and is therefore
asserted explicitly: `commutes` and `injective` are different properties. Field
setters always commute, so syntactic commutation proves nothing on its own. A
parent can commute perfectly and still be disqualified by injectivity.

No production mutation and no D8 coordinate is ratified here.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class Corner:
    """One cell of a candidate square, named for the family it came from."""

    name: str
    bit_a: bool
    bit_b: bool


def corner_set(corner: Corner) -> tuple[bool, bool]:
    """Normalised bit pair.

    Corner names in older witnesses were built from string slices like bits[0]
    == "1", which yields bool, but some were built from int slices, which yield
    int. Comparing (1, 0) against (True, False) silently fails even though they
    are the same corner, which is how an early version of the REPL test reported
    a contradictory pair of verdicts. Every comparison in this module goes
    through here.
    """
    return (bool(corner.bit_a), bool(corner.bit_b))


def refine_a(corner: Corner) -> Corner:
    return Corner(corner.name, bit_a=True, bit_b=corner.bit_b)


def refine_b(corner: Corner) -> Corner:
    return Corner(corner.name, bit_a=corner.bit_a, bit_b=True)


def full_square(a0: Corner, a1: Corner, b0: Corner, b1: Corner) -> dict:
    """Assemble the four corners from the parent plus its three siblings.

    a0 must be the parent itself: the 00 corner is the unrefined base policy and
    must not be mistaken for a new semantic resident merely because it is
    printed with eight bits.
    """
    return {"00": a0, "10": a1, "01": b0, "11": b1}


def distinct(square: dict, signature) -> bool:
    return len({signature(corner) for corner in square.values()}) == 4


def refine_image(square: dict, refine) -> set:
    return {corner_set(refine(corner)) for corner in square.values()}


def expected_refine_image(bit: str) -> set:
    """The image a genuine one-bit refinement must have: exactly 2 states.

    Parameterised by the bit being set. An earlier version hardcoded the bit-A
    image and so reported every bit-B refinement as inconsistent, which is what
    made the first LEQ run claim both axes were projections.
    """
    if bit == "a":
        return {(True, False), (True, True)}
    return {(False, True), (True, True)}


def consistent_refine_image(square: dict, refine, bit: str) -> bool:
    """True when a refinement reaches the standard 2-state image."""
    return refine_image(square, refine) == expected_refine_image(bit)


def forced(square: dict) -> bool:
    """Each axis must flip exactly one bit of the 00 parent corner.

    This is the part that discriminates. If a candidate axis moves the parent
    corner onto the 11 cell, then two axes claim the same destination and the
    reading is not forced.
    """
    parent = corner_set(square["00"])
    moved_a = corner_set(refine_a(square["00"]))
    moved_b = corner_set(refine_b(square["00"]))
    if moved_a != (True, parent[1]):
        return False
    if moved_b != (parent[0], True):
        return False
    return moved_a != moved_b


def unique_routes(square: dict) -> bool:
    """No corner may be reachable by two different single-bit routes."""
    return len({discipline_key(square[key]) for key in square}) == len(square)


def discipline_key(corner: Corner) -> tuple:
    return corner.bit_a, corner.bit_b


def commutes(square: dict, refine_a=refine_a, refine_b=refine_b) -> bool:
    return all(
        corner_set(refine_b(refine_a(corner))) == corner_set(refine_a(refine_b(corner)))
        for corner in square.values()
    )


def composes(square: dict, refine_a=refine_a, refine_b=refine_b) -> bool:
    """Structural check that the 11 corner equals the two orderings.

    True for any well-formed square; retained because it documents the shape the
    semantic check below is testing.
    """
    parent = square["00"]
    return (
        corner_set(refine_b(refine_a(parent))) == corner_set(square["11"])
        and corner_set(refine_a(refine_b(parent))) == corner_set(square["11"])
    )


def compose_ok(composed_signatures) -> bool:
    """Semantic composition check, from the caller's own signatures.

    composed_signatures is a sequence of three signatures: A then B, B then A,
    and the already-assigned 11 corner. Two independent bits commute, so the
    first two must be equal and both must equal the third. Returning False is
    what refutes FLOOR/CEILING/TRUNCATE/ROUND.
    """
    a_then_b, b_then_a, joint = composed_signatures
    return a_then_b == b_then_a == joint


def one_domain(corner_names, base_policy, is_instance) -> bool:
    """All four corners must be instances of one base policy.

    corner_names are the four attested Lisp names. base_policy is the single
    policy both axes are claimed to refine, spelled out so the claim is quotable.
    is_instance(name, base_policy) is the caller's predicate that actually tests
    membership, so the caller cannot pass this by naming two axes and asserting
    they belong together.

    Why a caller-supplied predicate and not a string test. A version of this
    function checked only that two axis names were non-empty, which returned True
    for every input and so tested nothing. Whether two axes share a base policy is
    a semantic judgement about the Lisp vocabulary that no arithmetic on
    coordinates can supply, which is exactly why it has to be argued per row and
    written as executable code rather than inferred.
    """
    missing = [
        name for name in corner_names if not is_instance(name, base_policy)
    ]
    return not missing



def admits_two_bit_law(square: dict, signature) -> tuple[bool, dict]:
    """Return (admitted, reasons-for-refusal)."""
    reasons = {}
    if not distinct(square, signature):
        reasons["NOT_DISTINCT"] = "two corners are observationally identical"
    if not forced(square):
        reasons["NOT_FORCED"] = "the 00 parent corner has no unique sibling per axis"
    if not unique_routes(square):
        reasons["AMBIGUOUS_ROUTES"] = "two corners share one coordinate"
    for label, refine, bit in (("A", refine_a, "a"), ("B", refine_b, "b")):
        if not consistent_refine_image(square, refine, bit):
            reasons[f"INCONSISTENT_REFINE_{label}"] = (
                f"bit {label} reaches {sorted(refine_image(square, refine))}, "
                f"which is not the 2-state image a real bit must produce"
            )
    # Recorded, never used as the deciding test.
    reasons["COMMUTES"] = commutes(square)
    admitted = not any(
        key.startswith("NOT_") for key in reasons
    )
    return admitted, reasons


def all_bit_pairs() -> list:
    return [("".join(bits)) for bits in product("01", repeat=2)]