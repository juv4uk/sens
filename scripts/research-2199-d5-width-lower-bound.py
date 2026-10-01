#!/usr/bin/env python3
"""#2199 — D5 width lower-bound falsifier.

Research-only. The witness asks a stricter question than #2193:

    does the existence of one new observable semantic distinction force
    the *minimum exact identity width* to be 5?

Current answer must remain NOT-PROVED while any honest <=4-bit placement model
survives under the ratified contract.
"""

from __future__ import annotations

from dataclasses import dataclass


D4_OCCUPIED = {
    "0000": "APPLY",
    "0001": "EVAL",
    "0010": "LAMBDA",
    "0011": "DEFINE",
    "0100": "NOT",
    "0110": "EVCON",
    "0111": "EVLIS",
    "1000": "LIST",
    "1010": "CAAR",
    "1011": "CADR",
    "1100": "CDAR",
    "1101": "CDDR",
    "1110": "LOOKUP",
    "1111": "BIND",
}
D4_FREE = ("0101", "1001")

# These are deliberately false until a ratified authority closes the escape
# hatch.  #2158 says the cells are intentionally unallocated, but it does not
# state that D4 membership is permanently closed; it also explicitly recognizes
# "allocation-only" as a placement-rationale class.
D4_MEMBERSHIP_CLOSED = False
ALLOCATION_ONLY_D4_FORBIDDEN = False

SEMANTIC_LOWER_BOUND_ESTABLISHED = True  # #2193 / merged PR #2194
D5_CANDIDATE = "00101"


@dataclass(frozen=True)
class Model:
    name: str
    width: int
    identity: str
    needs_family_claim: bool
    needs_reratification: bool
    survives_current_laws: bool
    reason: str


def classify() -> list[Model]:
    models: list[Model] = []

    for word, neighbor in (("0101", "NOT"), ("1001", "LIST")):
        models.append(
            Model(
                name=f"W4-{word}",
                width=4,
                identity=word,
                needs_family_claim=False,
                needs_reratification=True,
                survives_current_laws=(
                    word in D4_FREE
                    and not D4_MEMBERSHIP_CLOSED
                    and not ALLOCATION_ONLY_D4_FORBIDDEN
                ),
                reason=(
                    f"{word} is currently unallocated next to {neighbor}; "
                    "allocation-only residency is not yet forbidden by a "
                    "ratified closure theorem"
                ),
            )
        )

    models.append(
        Model(
            name="W4-allocation-only",
            width=4,
            identity="0101|1001",
            needs_family_claim=False,
            needs_reratification=True,
            survives_current_laws=(
                bool(D4_FREE)
                and not D4_MEMBERSHIP_CLOSED
                and not ALLOCATION_ONLY_D4_FORBIDDEN
            ),
            reason=(
                "exact width=4 still has free capacity and current law does "
                "not yet prove that unrelated allocation-only residency is illegal"
            ),
        )
    )

    models.append(
        Model(
            name="W5-lambda-stage-child",
            width=5,
            identity=D5_CANDIDATE,
            needs_family_claim=True,
            needs_reratification=True,
            survives_current_laws=True,
            reason=(
                "00101 is a viable candidate under LAMBDA if the local staged "
                "family law survives; viability is not minimality"
            ),
        )
    )

    return models


def main() -> None:
    assert len(D4_OCCUPIED) == 14
    assert set(D4_OCCUPIED).isdisjoint(D4_FREE)
    assert len(set(D4_OCCUPIED) | set(D4_FREE)) == 16
    assert SEMANTIC_LOWER_BOUND_ESTABLISHED

    models = classify()
    shorter_survivors = [m for m in models if m.width <= 4 and m.survives_current_laws]
    d5_survivors = [m for m in models if m.width == 5 and m.survives_current_laws]

    print("D5 width lower-bound witness")
    print(f"d4-occupied={len(D4_OCCUPIED)}")
    print(f"d4-free={','.join(D4_FREE)}")
    print(f"d4-membership-closed={int(D4_MEMBERSHIP_CLOSED)}")
    print(f"allocation-only-d4-forbidden={int(ALLOCATION_ONLY_D4_FORBIDDEN)}")
    print(f"semantic-lower-bound-established={int(SEMANTIC_LOWER_BOUND_ESTABLISHED)}")
    print()

    for model in models:
        print(
            f"{model.name}: width={model.width} identity={model.identity} "
            f"survives={'YES' if model.survives_current_laws else 'NO'} "
            f"family-claim={'YES' if model.needs_family_claim else 'NO'} "
            f"reratification={'YES' if model.needs_reratification else 'NO'}"
        )
        print(f"  reason={model.reason}")

    print()
    if shorter_survivors:
        print("D5-WIDTH-LOWER-BOUND=NOT-PROVED")
        print(
            "blocking-escape-hatches="
            + ",".join(model.name for model in shorter_survivors)
        )
        print(
            "required-next-proof=D4-membership-closure-or-explicit-falsification-"
            "of-allocation-only-staged-residency"
        )
    elif not d5_survivors:
        print("D5-WIDTH-LOWER-BOUND=NOT-PROVED")
        print("blocking-reason=no-surviving-width5-witness")
    else:
        print("D5-WIDTH-LOWER-BOUND=PROVED")
        print("NON-CONCLUSION: exact D5 placement still requires owner ratification")

    # Current expected state.  If this assertion starts failing, the witness
    # must be updated together with ratified contract evidence.
    assert shorter_survivors, (
        "Do not silently upgrade the theorem. Link the ratified D4 closure "
        "evidence and update this witness explicitly."
    )


if __name__ == "__main__":
    main()
