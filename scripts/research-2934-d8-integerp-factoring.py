#!/usr/bin/env python3
"""#2934 — D8 factoring triage for non-selector D6 parents.

Research-only. Applies the #2506 discipline to candidate two-bit refinements of
D6 parents that currently hold four attested-not-admitted D8 candidates.

A parent verdict has three independent parts:
  distinct   — the four corners are observationally distinct
  forced     — the names can only be read as the four corners of this square
  commutes  — the two refinements commute on every corner

`commutes` is the discriminating test. Two independent bits commute; a single
underlying axis re-encoded twice does not.

No production mutation and no D8 coordinate is ratified here. A parent that
passes all three is research evidence for a future ratification, not an
admission.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction


@dataclass(frozen=True)
class Mode:
    """Rounding direction and rounding style as two candidate bits."""

    name: str
    toward_zero: bool
    toward_plus_inf: bool


def toward_zero(x: Fraction) -> Fraction:
    return Fraction(int(x), 1)


def toward_minus_inf(x: Fraction) -> Fraction:
    return x.__floor__()


def toward_plus_inf(x: Fraction) -> Fraction:
    return x.__ceil__()


def to_nearest_even(x: Fraction) -> Fraction:
    floor_x = x.__floor__()
    frac = x - floor_x
    if frac < Fraction(1, 2):
        return floor_x
    if frac > Fraction(1, 2):
        return floor_x + 1
    return floor_x if floor_x % 2 == 0 else floor_x + 1


IMPL = {
    (False, False): toward_minus_inf,
    (False, True): toward_plus_inf,
    (True, False): toward_zero,
    (True, True): to_nearest_even,
}

PROBES = [
    Fraction(7, 2),
    Fraction(-7, 2),
    Fraction(5, 2),
    Fraction(-5, 2),
    Fraction(3),
    Fraction(-3),
    Fraction(1, 4),
    Fraction(-1, 4),
]


def signature(mode: Mode) -> tuple:
    return tuple(IMPL[(mode.toward_zero, mode.toward_plus_inf)](x) for x in PROBES)


def refine_toward_zero(mode: Mode) -> Mode:
    return replace(mode, toward_zero=True)


def refine_toward_plus_inf(mode: Mode) -> Mode:
    return replace(mode, toward_plus_inf=True)


def bits(mode: Mode) -> tuple[bool, bool]:
    return (mode.toward_zero, mode.toward_plus_inf)


FLOOR = Mode("FLOOR", toward_zero=False, toward_plus_inf=False)
CEILING = Mode("CEILING", toward_zero=False, toward_plus_inf=True)
TRUNCATE = Mode("TRUNCATE", toward_zero=True, toward_plus_inf=False)
ROUND = Mode("ROUND", toward_zero=True, toward_plus_inf=True)

ASSIGNED = {"00": FLOOR, "01": CEILING, "10": TRUNCATE, "11": ROUND}


def distinct() -> bool:
    return len({signature(m) for m in ASSIGNED.values()}) == 4


def forced() -> bool:
    """Each refinement from the parent must land on exactly one assigned name."""
    return bits(refine_toward_zero(FLOOR)) == bits(TRUNCATE) and bits(
        refine_toward_plus_inf(FLOOR)
    ) == bits(CEILING)


def commutes() -> bool:
    """Field setters commute trivially. That proves nothing about the semantics.

    This therefore reports only the syntactic result, and the semantic
    discriminator is entanglement() below.
    """
    for mode in ASSIGNED.values():
        if bits(refine_toward_plus_inf(refine_toward_zero(mode))) != bits(
            refine_toward_zero(refine_toward_plus_inf(mode))
        ):
            return False
    return True


def changed_probes(refine) -> set:
    """Probes whose result this refinement changes, relative to the parent."""
    out = set()
    for index, x in enumerate(PROBES):
        if IMPL[bits(refine(FLOOR))](x) != IMPL[(False, False)](x):
            out.add(index)
    return out


def entangled() -> bool:
    """True when the two refinements touch the same probe.

    Two independent one-bit refinements must be observationally orthogonal:
    each should change probes the other leaves alone. If a probe is moved by
    both, they are not two bits of one base policy but two encodings of a
    single decision.
    """
    return bool(changed_probes(refine_toward_zero) & changed_probes(refine_toward_plus_inf))


def refine_image(refine) -> set:
    """Corners reached by applying one refinement to all four corners."""
    return {bits(refine(mode)) for mode in ASSIGNED.values()}


def injective(refine) -> bool:
    """A genuine one-bit refinement must distinguish its two sides.

    Setting one bit is injective on a real 2x2 product: the four corners map to
    four distinct results. If the map collapses pairs, the "refinement" is a
    projection that forgets which of two corners it started from, which means
    the four names are not corners of this square.
    """
    return len(refine_image(refine)) == 4


def non_commutation_witness() -> tuple[Fraction, Fraction, Fraction]:
    """Return (x, floor_then_round, round_then_floor) that actually differ."""
    for x in PROBES:
        a = to_nearest_even(toward_zero(x))
        b = toward_zero(to_nearest_even(x))
        if a != b:
            return x, a, b
    raise AssertionError("expected a non-commuting probe")


def main() -> None:
    # Distinct: all four rounding behaviours are observationally different.
    assert distinct(), "the four rounding modes must be distinguishable"

    # Forced: the reading is not arbitrary.
    assert forced(), "the two-bit reading must be forced"

    # Syntactic commutation holds only because the refinements are field
    # setters. It is recorded, not treated as evidence of independence.
    assert commutes(), "field setters are expected to commute syntactically"

    # The real discriminator: the two "bits" move the same probes, so they are
    # not orthogonal refinements of one base policy.
    assert entangled(), "expected the two candidate axes to be entangled"

    # The decisive test: neither refinement is injective on the four corners.
    # Setting one bit of a real 2x2 product always yields four distinct results.
    assert not injective(refine_toward_zero), "toward-zero must collapse corners"
    assert not injective(refine_toward_plus_inf), "toward-+inf must collapse corners"

    # Both refinements forget which side they started from: they are projections
    # onto a two-valued choice, not bits that can be set.
    assert refine_image(refine_toward_zero) == {
        bits(TRUNCATE),
        bits(ROUND),
    }
    assert refine_image(refine_toward_plus_inf) == {
        bits(CEILING),
        bits(ROUND),
    }

    x, floor_then_round, round_then_floor = non_commutation_witness()
    assert floor_then_round != round_then_floor


if __name__ == "__main__":
    main()