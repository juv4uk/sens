#!/usr/bin/env python3
"""#1962: executable witness for the 3-bit seed and CAR/CDR prefix subtree.

Research-only. Скрипт не читає production tables і не змінює runtime.
"""

from __future__ import annotations

SEED3 = {
    "000": "()",
    "001": "QUOTE",
    "010": "ATOM",
    "011": "EQ",
    "100": "CONS",
    "101": "CAR",
    "110": "CDR",
    "111": "COND",
}

EXPECTED_WIDTH4 = {
    "1010": "CAAR",
    "1011": "CADR",
    "1100": "CDAR",
    "1101": "CDDR",
}

EXPECTED_WIDTH5 = {
    "10100": "CAAAR",
    "10101": "CAADR",
    "10110": "CADAR",
    "10111": "CADDR",
    "11000": "CDAAR",
    "11001": "CDADR",
    "11010": "CDDAR",
    "11011": "CDDDR",
}


def selector_name(code: str) -> str:
    """Перетворює selector-prefix на історичне C[AD]+R ім'я.

    101 = CAR, 110 = CDR.
    Після кореня кожен 0 додає A (CAR), кожен 1 додає D (CDR).
    """
    if len(code) < 3:
        raise ValueError("selector code must be at least 3 bits")
    if code[:3] == "101":
        letters = ["A"]
    elif code[:3] == "110":
        letters = ["D"]
    else:
        raise ValueError(f"{code} is outside the CAR/CDR selector subtree")

    for bit in code[3:]:
        if bit == "0":
            letters.append("A")
        elif bit == "1":
            letters.append("D")
        else:
            raise ValueError(f"non-binary code: {code}")

    return "C" + "".join(letters) + "R"


def selector_level(width: int) -> dict[str, str]:
    if width < 3:
        raise ValueError("width must be >= 3")
    suffix_width = width - 3
    out: dict[str, str] = {}
    for root in ("101", "110"):
        for n in range(1 << suffix_width):
            suffix = format(n, f"0{suffix_width}b") if suffix_width else ""
            code = root + suffix
            out[code] = selector_name(code)
    return out


def verify_seed_projection() -> None:
    assert len(SEED3) == 8
    assert set(SEED3) == {format(n, "03b") for n in range(8)}

    # Старі first-eight rows are exactly zero-padded projections of the 3-bit seed.
    padded = [code.zfill(8) for code in sorted(SEED3)]
    assert padded == [format(n, "08b") for n in range(8)]


def verify_selector_tree(max_width: int = 8) -> None:
    for width in range(3, max_width + 1):
        level = selector_level(width)
        expected_count = 2 ** (width - 2)
        assert len(level) == expected_count, (width, len(level), expected_count)
        assert len(set(level.values())) == len(level)

        if width > 3:
            previous = selector_level(width - 1)
            for code in level:
                assert code[:-1] in previous

    assert selector_level(4) == EXPECTED_WIDTH4
    assert selector_level(5) == EXPECTED_WIDTH5


def main() -> None:
    verify_seed_projection()
    verify_selector_tree()

    print("seed3\told-padded8\trole")
    for code in sorted(SEED3):
        print(f"{code}\t{code.zfill(8)}\t{SEED3[code]}")

    print("\nselector-prefix-tree")
    for width in range(3, 7):
        print(f"width={width}")
        for code, name in selector_level(width).items():
            print(f"{code}\t{name}\tparent={code[:-1] if width > 3 else '-'}")

    print("\nPASS: seed3 is full; padded first-eight projection is lossless; "
          "CAR/CDR descendants form a collision-free binary prefix tree.")


if __name__ == "__main__":
    main()
