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


OPS = {"zero": toward_zero, "inf": toward_plus_inf, "round": to_nearest_even}


def chain(x, order_names):
    """Apply rounding operations in the given order, left to right."""
    value = x
    for name in order_names:
        value = OPS[name](value)
    return value


def chain_signature(order_names):
    return tuple(chain(x, order_names) for x in PROBES)


def main() -> None:
    # Distinct: all four rounding behaviours are observationally different.
    assert distinct(), "the four rounding modes must be distinguishable"

    # Forced: the reading is not arbitrary.
    assert forced(), "the two-bit reading must be forced"

    # Structural tests all pass on this row, and none of them can detect the
    # failure. Recorded so the docs can say so precisely.
    assert commutes(), "field setters commute syntactically"
    assert entangled(), "the two axes move the same probes"
    assert forced(), "the 00 corner has a unique sibling per axis"

    # The decisive test is semantic composition. Two independent bits commute, so
    # applying the two rounding operations in either order must give ROUND.
    zero_then_inf = chain_signature(["zero", "inf"])
    inf_then_zero = chain_signature(["inf", "zero"])
    round_only = chain_signature(["round"])

    assert zero_then_inf != inf_then_zero, "the two orderings must disagree"
    assert zero_then_inf != round_only, "toward-zero then toward-+inf is not ROUND"
    assert inf_then_zero != round_only, "toward-+inf then toward-zero is not ROUND"

    # A concrete witness pair, kept so the refutation is quotable rather than
    # merely a boolean.
    witness = next(
        x for x in PROBES if to_nearest_even(toward_zero(x)) != toward_zero(to_nearest_even(x))
    )
    assert toward_zero(toward_plus_inf(witness)) != toward_plus_inf(toward_zero(witness))


if __name__ == "__main__":
    main()