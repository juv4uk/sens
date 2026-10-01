#!/usr/bin/env python3
"""#2175 — exact D5 selector subtree + residue witness.

Research-only. This script proves only what already follows from the admitted
CAR/CDR selector generator and counts the remaining exact-width D5 residue.
It does NOT allocate macro or other D5 roles.
"""

from __future__ import annotations

from itertools import product

ROOTS = {
    "101": "A",  # CAR
    "110": "D",  # CDR
}

EXPECTED_D5 = {
    "10100": "CAAAR",
    "10101": "CAADR",
    "10110": "CADAR",
    "10111": "CADDR",
    "11000": "CDAAR",
    "11001": "CDADR",
    "11010": "CDDAR",
    "11011": "CDDDR",
}


def selector_name(root_letter: str, suffix: str) -> str:
    letters = root_letter + "".join("A" if bit == "0" else "D" for bit in suffix)
    return "C" + letters + "R"


def generated_d5() -> dict[str, str]:
    out: dict[str, str] = {}
    for root, root_letter in ROOTS.items():
        for bits in product("01", repeat=2):
            suffix = "".join(bits)
            word = root + suffix
            out[word] = selector_name(root_letter, suffix)
    return dict(sorted(out.items()))


def main() -> None:
    generated = generated_d5()
    assert generated == EXPECTED_D5

    all_words = {f"{value:05b}" for value in range(32)}
    fixed = set(generated)
    residue = sorted(all_words - fixed)

    assert len(all_words) == 32
    assert len(fixed) == 8
    assert len(residue) == 24
    assert fixed.isdisjoint(residue)

    # Positive generator control: appended suffix bit is still the admitted
    # local selector action, never a generic D5 semantic rule.
    for word, name in generated.items():
        parent = word[:-1]
        suffix = word[-1]
        assert parent in {"1010", "1011", "1100", "1101"}
        if suffix == "0":
            assert name[-2] == "A"
        else:
            assert name[-2] == "D"

    print("D5 selector/residue witness: PASS")
    print("width=5")
    print("capacity=32")
    print("generator-owned=8")
    print("residue=24")
    for word, name in generated.items():
        print(f"{word} {name} parent={word[:-1]} suffix={word[-1]}")
    print("residue-words=" + ",".join(residue))
    print("NON-CONCLUSION: residue words have no semantic assignment")
    print("NON-CONCLUSION: selector suffix law does not generalize globally")


if __name__ == "__main__":
    main()
