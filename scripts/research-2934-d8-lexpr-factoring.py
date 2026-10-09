#!/usr/bin/env python3
"""#2934 — D8 factoring test on D6 parent 000101 LEXPR.

Research-only. Tests whether the four assigned D8 children of LEXPR
(ARGLIST, &REST, &OPTIONAL, &WHOLE) are the corners of two independent
one-bit refinements of LEXPR, in the discipline of #2506.

No production mutation and no D8 coordinate is ratified here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from itertools import product

MissingDefault = object()


@dataclass(frozen=True)
class LambdaList:
    """A lambda list over an evaluated argument list."""

    name: str
    has_rest: bool
    has_optional: bool
    has_whole: bool = False


def apply(ll: LambdaList, args: list[object]) -> tuple[object, ...]:
    """Apply the lambda list and return an observation signature."""
    if ll.has_whole:
        return ("whole", tuple(args))
    if ll.has_optional:
        # Optional leading arguments are bound with defaults when absent.
        head = args[0] if args else MissingDefault
        tail = tuple(args[1:])
        return ("optional", head, tail)
    if ll.has_rest:
        required = args[0] if args else MissingDefault
        rest = tuple(args[1:])
        return ("rest", required, rest)
    return ("plain", tuple(args))


def signature(ll: LambdaList) -> tuple:
    cases: list[list[object]] = [
        [],
        ["A"],
        ["A", "B"],
        ["A", "B", "C"],
    ]
    out = []
    for args in cases:
        out.append((len(args), apply(ll, args)))
    return tuple(out)


def refine_rest(ll: LambdaList) -> LambdaList:
    return replace(ll, has_rest=True)


def refine_optional(ll: LambdaList) -> LambdaList:
    return replace(ll, has_optional=True)


def semantics(ll: LambdaList) -> tuple[bool, bool, bool]:
    """Name-independent semantics: the bits that actually drive apply()."""
    return (ll.has_rest, ll.has_optional, ll.has_whole)


ARGLIST = LambdaList("ARGLIST", has_rest=False, has_optional=False)
REST = LambdaList("&REST", has_rest=True, has_optional=False)
OPTIONAL = LambdaList("&OPTIONAL", has_rest=False, has_optional=True)
WHOLE = LambdaList("&WHOLE", has_rest=False, has_optional=False, has_whole=True)
REST_AND_OPTIONAL = LambdaList(
    "&REST+&OPTIONAL", has_rest=True, has_optional=True
)


def main() -> None:
    assigned = {"00": ARGLIST, "01": OPTIONAL, "10": REST, "11": WHOLE}

    # 1. The four assigned names are observationally distinct. This part holds,
    #    so distinctness alone cannot falsify the square.
    sigs = {bits: signature(ll) for bits, ll in assigned.items()}
    assert len(set(sigs.values())) == 4, "assigned names collide"

    # 2. The two axes commute, on every corner, and are idempotent. This is the
    #    #2506 discipline applied to lambda lists.
    for ll in (ARGLIST, REST, OPTIONAL, WHOLE):
        assert semantics(refine_optional(refine_rest(ll))) == semantics(
            refine_rest(refine_optional(ll))
        )
        assert semantics(refine_rest(refine_rest(ll))) == semantics(refine_rest(ll))
        assert semantics(refine_optional(refine_optional(ll))) == semantics(
            refine_optional(ll)
        )

    # 3. Therefore &REST x &OPTIONAL is a genuine commuting square. The two bits
    #    really are independent, and the 11 corner is well defined.
    assert semantics(refine_optional(refine_rest(ARGLIST))) == semantics(REST_AND_OPTIONAL)

    # 4. FALSIFIER: the 11 corner of that real square is &REST+&OPTIONAL, which
    #    is not the assigned 11 corner &WHOLE. The assigned names therefore do
    #    not form the square, even though the axes themselves commute.
    assert REST_AND_OPTIONAL != WHOLE
    assert signature(REST_AND_OPTIONAL) != signature(WHOLE)

    # 5. FALSIFIER: the 00 corner must be the parent LEXPR itself. ARGLIST is a
    #    distinct accessor of the argument list, not a parameterless LEXPR.
    assert signature(ARGLIST) != signature(WHOLE)
    assert ARGLIST.has_rest is False and ARGLIST.has_optional is False

    # 6. Record the separable finding: a commuting pair exists for lambda lists,
    #    but it is a different pair than the one the assigned names imply, and
    #    the four assigned names are not its corners.
    axis_square = {
        "".join(bits): LambdaList(
            "", has_rest=bits[1] == "1", has_optional=bits[0] == "1"
        )
        for bits in product("01", repeat=2)
    }
    # The four assigned names are NOT the corners of the real axis square:
    # the genuine 11 corner is &REST+&OPTIONAL, but the map assigns &WHOLE.
    assert semantics(axis_square["11"]) == semantics(REST_AND_OPTIONAL)
    assert signature(axis_square["11"]) != signature(assigned["11"])
    assert semantics(axis_square["00"]) != semantics(WHOLE)


if __name__ == "__main__":
    main()