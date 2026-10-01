#!/usr/bin/env python3
"""#2117 proposition co-reference foundation witness.

Same evidence occurrences, same polarity, different co-reference partitions.
Shows proposition status is not determined by occurrence stream alone.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Polarity(Enum):
    SUPPORT = "+"
    REFUTE = "-"


class PStatus(Enum):
    SUPPORTED = "supported"
    REFUTED = "refuted"
    BOTH = "both"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Occurrence:
    oid: str
    polarity: Polarity


OCC = (
    Occurrence("e1", Polarity.SUPPORT),
    Occurrence("e2", Polarity.REFUTE),
    Occurrence("e3", Polarity.SUPPORT),
)


def summarize(classes):
    by_id = {e.oid: e for e in OCC}
    result = []
    covered = set()

    for cls in classes:
        cls = tuple(sorted(cls))
        covered |= set(cls)
        ps = {by_id[x].polarity for x in cls}
        if ps == {Polarity.SUPPORT}:
            status = PStatus.SUPPORTED
        elif ps == {Polarity.REFUTE}:
            status = PStatus.REFUTED
        elif ps == {Polarity.SUPPORT, Polarity.REFUTE}:
            status = PStatus.BOTH
        else:
            status = PStatus.UNKNOWN
        result.append((cls, status))

    assert covered == {e.oid for e in OCC}
    assert sum(len(c) for c, _ in result) == len(OCC)
    return tuple(result)


def canonical_shape(summary):
    """Ignore proposition labels; retain class sizes + polarity/status structure."""
    return tuple(sorted((len(cls), status.value) for cls, status in summary))


def main():
    model_a = (
        {"e1", "e2"},
        {"e3"},
    )
    model_b = (
        {"e1", "e3"},
        {"e2"},
    )
    model_c = (
        {"e1"},
        {"e2"},
        {"e3"},
    )

    sa = summarize(model_a)
    sb = summarize(model_b)
    sc = summarize(model_c)

    print("OCCURRENCES")
    for e in OCC:
        print(e.oid, e.polarity.value)
    print()

    print("MODEL A")
    for cls, status in sa:
        print(cls, "->", status.value)
    print()

    print("MODEL B")
    for cls, status in sb:
        print(cls, "->", status.value)
    print()

    print("MODEL C")
    for cls, status in sc:
        print(cls, "->", status.value)
    print()

    assert sa != sb != sc
    assert canonical_shape(sa) != canonical_shape(sb)
    assert canonical_shape(sb) != canonical_shape(sc)

    print("COUNTERMODEL")
    print("same evidence occurrences: YES")
    print("same polarity markers: YES")
    print("different co-reference partitions: YES")
    print("different proposition-level status/conflict: YES")
    print()

    print("FOUNDATIONAL CLASSIFICATION")
    print("occurrence identity != proposition identity")
    print("polarity stream alone does not derive proposition co-reference")
    print("conflict exists only after occurrences are grouped as concerning the same proposition")
    print("co-reference requires its own evidence/law")
    print()
    print("PASS: proposition status is not determined by evidence occurrences alone.")


if __name__ == "__main__":
    main()
