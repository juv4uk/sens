#!/usr/bin/env python3
"""#2934 — D8 factoring test on D6 parent 000000 REPL.

Research-only. Proposed axes:
  bit 1: direction  — text -> internal form, or internal form -> text
  bit 2: extent     — one datum, or a whole stream/program

No production mutation and no D8 coordinate is ratified here.
"""

from __future__ import annotations

from dataclasses import dataclass


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


def injective(refine) -> bool:
    return len(refine_image(refine)) == 4


def main() -> None:
    # The parent itself is REPL: read-eval-print, one datum at a time. READ is
    # the faithful parent corner.
    assert (READ.reads, READ.whole_stream) == (True, False)

    # Neither refinement is injective. On a real 2x2 product, setting one bit
    # across four distinct corners reaches four distinct states. Both refinements
    # here reach only two, because the assigned names do not occupy four distinct
    # corners in the first place.
    assert not injective(refine_to_output), refine_image(refine_to_output)
    assert refine_image(refine_to_output) == {
        (False, False),
        (False, True),
    }

    # The decisive test. Extent must be independent of direction, so setting it
    # on all four corners must reach all four states.
    assert not injective(refine_to_whole_stream), refine_image(refine_to_whole_stream)
    assert refine_image(refine_to_whole_stream) == {
        (True, True),
        (False, True),
    }

    # Why: READ and COMPILE occupy the same corner. COMPILE compiles one
    # expression, so it has the same extent as READ; it differs by producing
    # executable code rather than data, which is not the direction axis at all.
    assert (COMPILE.reads, COMPILE.whole_stream) == (READ.reads, READ.whole_stream)
    assert COMPILE.name != READ.name


if __name__ == "__main__":
    main()