#!/usr/bin/env python3
"""#2214 — exact-width Pareto witness for one-cap TRANSFORMER placement.

This benchmark deliberately refuses a scalar score.  It keeps bit cost,
ratification/revision cost, and semantic-parent evidence as separate axes.

Current evidence:
- #2193: eager/raw discriminator is necessary.
- #2196: one transformer capability is sufficient.
- #2198: LAMBDA is the strongest known typed parent.
- #2158/#2162: 0101 and 1001 remain free and suffix-1 compatible.
- #2204: current D4 law does not yet falsify those shorter placements.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Candidate:
    name: str
    word: str
    width: int
    slot_free: bool
    d4_revision_required: bool
    typed_parent: str | None
    generic_suffix_compatible: bool
    allocation_only: bool
    missing_independent_assertions: int

    def cost_vector(self) -> tuple[int, int, int, int, int]:
        """Axes minimized for Pareto dominance; never collapse to one score."""
        return (
            self.width,
            int(self.d4_revision_required),
            int(self.typed_parent is None),
            int(self.allocation_only),
            self.missing_independent_assertions,
        )


CANDIDATES = (
    Candidate(
        name="W4-0101",
        word="0101",
        width=4,
        slot_free=True,
        d4_revision_required=True,
        typed_parent=None,
        generic_suffix_compatible=True,
        allocation_only=True,
        # (1) reopen D4 residency, (2) justify unrelated allocation-only use.
        missing_independent_assertions=2,
    ),
    Candidate(
        name="W4-1001",
        word="1001",
        width=4,
        slot_free=True,
        d4_revision_required=True,
        typed_parent=None,
        generic_suffix_compatible=True,
        allocation_only=True,
        missing_independent_assertions=2,
    ),
    Candidate(
        name="W5-00101",
        word="00101",
        width=5,
        slot_free=True,
        d4_revision_required=False,
        typed_parent="0010/LAMBDA",
        generic_suffix_compatible=True,
        allocation_only=False,
        # #2198 supplies the typed derivation; owner placement ratification
        # remains a decision, represented here as one unresolved assertion.
        missing_independent_assertions=1,
    ),
)

OCCURRENCES = (1, 8, 64, 1024)


def packed_payload(width: int, occurrences: int) -> tuple[int, int, int]:
    bits = width * occurrences
    octets = ceil(bits / 8)
    unused_tail_bits = octets * 8 - bits
    return bits, octets, unused_tail_bits


def dominates(left: Candidate, right: Candidate) -> bool:
    a = left.cost_vector()
    b = right.cost_vector()
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def pareto_live() -> list[Candidate]:
    return [
        candidate
        for candidate in CANDIDATES
        if not any(
            other is not candidate and dominates(other, candidate)
            for other in CANDIDATES
        )
    ]


def main() -> None:
    assert {c.word for c in CANDIDATES} == {"0101", "1001", "00101"}
    assert all(c.slot_free for c in CANDIDATES)
    assert all(c.generic_suffix_compatible for c in CANDIDATES)

    print("DOMAIN-WIDTH-PARETO-1")
    print("axes=min(width,d4-revision,no-typed-parent,allocation-only,missing-assertions)")
    print()
    print("candidate,word,width,d4-revision,typed-parent,allocation-only,missing-assertions")
    for c in CANDIDATES:
        print(
            f"{c.name},{c.word},{c.width},"
            f"{int(c.d4_revision_required)},{c.typed_parent or '-'},"
            f"{int(c.allocation_only)},{c.missing_independent_assertions}"
        )

    print()
    print("payload-economics (framing excluded)")
    print("candidate,N,semantic-bits,packed-bytes,unused-tail-bits")
    for c in CANDIDATES:
        for n in OCCURRENCES:
            bits, octets, unused = packed_payload(c.width, n)
            print(f"{c.name},{n},{bits},{octets},{unused}")

    live = pareto_live()
    print()
    print("PARETO-LIVE=" + ",".join(c.name for c in live))

    shorter = [c for c in live if c.width <= 4]
    if shorter:
        print("D5-WIDTH-LOWER-BOUND=NOT-PROVED")
        print("SHORTER-LIVE=" + ",".join(c.name for c in shorter))
    else:
        print("D5-WIDTH-LOWER-BOUND=PROVED")

    w4_8 = packed_payload(4, 8)
    w5_8 = packed_payload(5, 8)
    w4_1024 = packed_payload(4, 1024)
    w5_1024 = packed_payload(5, 1024)
    assert w4_8[:2] == (32, 4)
    assert w5_8[:2] == (40, 5)
    assert w4_1024[:2] == (4096, 512)
    assert w5_1024[:2] == (5120, 640)

    # Under current ratified evidence no candidate may disappear merely because
    # one address looks more elegant.  A future theorem may intentionally
    # change this assertion together with its cited authority.
    assert {c.name for c in live} == {"W4-0101", "W4-1001", "W5-00101"}


if __name__ == "__main__":
    main()
