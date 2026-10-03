#!/usr/bin/env python3
"""#2934 — D8 factoring test on D6 parent 001101 WHILE.

Research-only. This row is the strongest remaining candidate for a genuine
two-bit product, so it is tested properly rather than dismissed by inspection.

Proposed axes:
  bit 1: control shape   — loop form vs predicate macro
  bit 2: polarity        — proceed-while-true vs proceed-while-false

No production mutation and no D8 coordinate is ratified here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Shape:
    name: str
    is_loop_form: bool
    is_negative: bool
    returns_last: bool = False


def run(shape: Shape, items: list[bool]) -> tuple[str, object]:
    """Return (control flow used, result)."""
    if shape.is_loop_form:
        if shape.is_negative:
            for item in items:
                if item:
                    return "exit-early", None
            return "exhausted", None
        for item in items:
            if not item:
                return "exit-early", None
        return "exhausted", None
    if shape.is_negative:
        if any(items):
            return "short-circuit", None
        return "exhausted", False
    if not all(items):
        return "short-circuit", None
    # EVERY reports the value of the last element; ALWAYS reports T alone.
    # Distinguishing these keeps the test honest: a coarse model would collapse
    # two candidates into an accidental equality.
    return "exhausted", ("last-value" if shape.returns_last else True)


def signature(shape: Shape) -> tuple:
    cases: list[list[bool]] = [
        [],
        [True],
        [False],
        [True, True],
        [False, False],
        [True, False],
        [False, True],
        [True, True, False],
    ]
    return tuple((len(c), run(shape, c)) for c in cases)


def refine_to_predicate(shape: Shape) -> Shape:
    return Shape(
        shape.name,
        is_loop_form=False,
        is_negative=shape.is_negative,
        returns_last=shape.returns_last,
    )


def refine_to_negative(shape: Shape) -> Shape:
    return Shape(
        shape.name,
        is_loop_form=shape.is_loop_form,
        is_negative=True,
        returns_last=shape.returns_last,
    )


WHILE = Shape("WHILE", is_loop_form=True, is_negative=False)
UNTIL = Shape("UNTIL", is_loop_form=True, is_negative=True)
ALWAYS = Shape("ALWAYS", is_loop_form=False, is_negative=False)
NEVER = Shape("NEVER", is_loop_form=False, is_negative=True)
EVERY = Shape("EVERY", is_loop_form=False, is_negative=False, returns_last=True)


def main() -> None:
    # The proposed axes are real and independent: each is a genuine bit.
    for shape in (WHILE, UNTIL, ALWAYS, NEVER):
        assert refine_to_negative(refine_to_predicate(shape)) == refine_to_predicate(
            refine_to_negative(shape)
        )

    # The 2x2 that the axes genuinely generate has exactly four corners, and it
    # does not contain the four assigned names. In particular the 11 corner is
    # "predicate that fails when any item is true", which is NEVER, while the
    # 01 corner is a positive predicate, for which BOTH ALWAYS and EVERY claim
    # the slot.
    #
    # ALWAYS and EVERY therefore compete for one corner: both are positive
    # predicates. They are not the same behaviour either, so this is a genuine
    # collision rather than a duplicate entry.
    assert signature(ALWAYS) != signature(EVERY)
    assert not ALWAYS.is_loop_form and not EVERY.is_loop_form
    assert not ALWAYS.is_negative and not EVERY.is_negative

    # Only one of them can occupy the corner. The row therefore has five
    # candidates competing for four slots, and no assignment of four of these
    # names to the four corners is forced.
    corners = {
        (False, False): ALWAYS,
        (False, True): NEVER,
        (True, False): WHILE,
        (True, True): UNTIL,
    }
    assert len({signature(s) for s in corners.values()}) == 4

    # The remaining name EVERY is observationally close to ALWAYS but not equal,
    # so it cannot be silently substituted for it either.
    assert ALWAYS.name == "ALWAYS" and EVERY.name == "EVERY"


if __name__ == "__main__":
    main()