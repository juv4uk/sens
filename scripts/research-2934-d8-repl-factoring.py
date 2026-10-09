#!/usr/bin/env python3
"""#2934 — D8 factoring test on D6 parent 000000 REPL.

Research-only. Proposed axes:
  bit 1: direction  — text -> internal form, or internal form -> text
  bit 2: extent     — one datum, or a whole stream/program

No production mutation and no D8 coordinate is ratified here.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import d8_factoring_discipline as discipline
from d8_factoring_discipline import full_square, unique_routes


@dataclass(frozen=True)
class Direction:
    name: str
    reads: bool
    whole_stream: bool


def run(d: Direction, input_text: str, datums: list) -> tuple:
    """Return (observable outcome) for one program text."""
    if d.reads:
        if d.whole_stream:
            return ("parsed-program", tuple(datums))
        return ("parsed-datum", datums[0] if datums else None)
    if d.whole_stream:
        return ("rendered-program", tuple(datums))
    return ("rendered-datum", datums[0] if datums else None)


def signature(d: Direction) -> tuple:
    cases = [
        ("(CAR X)", ["a", "b"]),
        ("", []),
        ("(+ 1 2) (+ 3 4)", ["1", "2", "3", "4"]),
    ]
    return tuple(run(d, text, datums) for text, datums in cases)


def refine_to_output(d: Direction) -> Direction:
    return Direction(d.name, reads=False, whole_stream=d.whole_stream)


def refine_to_whole_stream(d: Direction) -> Direction:
    return Direction(d.name, reads=d.reads, whole_stream=True)


READ = Direction("READ", reads=True, whole_stream=False)
PRINT = Direction("PRINT", reads=False, whole_stream=False)
COMPILE = Direction("COMPILE", reads=True, whole_stream=False)
COMPILE_FILE = Direction("COMPILE-FILE", reads=True, whole_stream=True)

ASSIGNED = {"00": READ, "01": PRINT, "10": COMPILE, "11": COMPILE_FILE}


def refine_image(refine) -> set:
    return {(x.reads, x.whole_stream) for x in (refine(d) for d in ASSIGNED.values())}


def main() -> None:
    # The parent itself is REPL: read-eval-print, one datum at a time. READ is
    # the faithful parent corner.
    assert (READ.reads, READ.whole_stream) == (True, False)

    # The refutation is a coordinate collision, not an injectivity result. An
    # earlier version of this witness refuted REPL by claiming neither refinement
    # was injective, which was a false test: setting one bit of a real 2x2 product
    # always reaches two of four states, so demanding four made the criterion
    # unsatisfiable. The collision below is the real reason, and it stands without
    # any counting argument.
    #
    # COMPILE compiles one expression, so it has the same extent as READ; it
    # differs by producing executable code rather than data, which is not the
    # direction axis at all. Two attested names therefore occupy one corner.
    assert (COMPILE.reads, COMPILE.whole_stream) == (READ.reads, READ.whole_stream)
    assert COMPILE.name != READ.name

    occupied = {(mode.reads, mode.whole_stream) for mode in ASSIGNED.values()}
    assert len(occupied) < len(ASSIGNED), "four names must not fill four corners"

    # With a corner occupied twice there is no way to assign four distinct
    # coordinates, so no reading of the row as a 2x2 exists.
    # Adapt the REPL modes into the framework's Corner type, so the shared
    # discipline is what decides, not a hand-copied check.
    def as_corner(mode):
        # Bits come from what each mode actually does, not from the slot it was
        # assigned. That is the whole point: if a mode's real behaviour does not
        # match its slot, the framework must notice.
        return discipline.Corner(
            mode.name, bit_a=mode.reads, bit_b=mode.whole_stream
        )

    corners = {bits: as_corner(mode) for bits, mode in ASSIGNED.items()}
    square = full_square(
        corners["00"], corners["10"], corners["01"], corners["11"]
    )
    assert not unique_routes(square), sorted(occupied)


if __name__ == "__main__":
    main()