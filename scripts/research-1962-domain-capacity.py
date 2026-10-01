#!/usr/bin/env python3
"""#1962: capacity arithmetic for separator-delimited variable-width domains.

Research-only. Assumes:
- D1/D2 are non-function domains already fixed by owner;
- bīja3 has 8 words, one of which is structural ground ();
- D4+ may host callable identities/paths;
- word boundaries are explicit, so codes need not be prefix-free.
"""


def words(width: int) -> int:
    return 1 << width


def function_capacity_through(max_width: int) -> int:
    # bīja3: 8 codes but () is ground, so 7 callable roots.
    return 7 + sum(words(w) for w in range(4, max_width + 1))


def main() -> None:
    print("width\texact-domain\tcumulative-function-capacity")
    for width in range(3, 11):
        exact = words(width)
        cumulative = function_capacity_through(width)
        print(f"{width}\t{exact}\t{cumulative}")

    assert function_capacity_through(3) == 7
    assert function_capacity_through(4) == 23
    assert function_capacity_through(5) == 55
    assert function_capacity_through(6) == 119
    assert function_capacity_through(7) == 247
    assert function_capacity_through(8) == 503

    old = 256
    short = function_capacity_through(7)
    remainder = old - short
    assert remainder == 9

    print()
    print(f"old flat function count: {old}")
    print(f"callable capacity using widths 3..7: {short}")
    print(f"old functions still needing width 8 if all 256 stay distinct: {remainder}")
    print(f"capacity through width 8: {function_capacity_through(8)}")
    print()
    print("PASS: variable-width domains nearly fit 256 distinct functions below 8 bits;")
    print("only 9 of 256 would require 8 bits before any alias/derivation compression.")


if __name__ == "__main__":
    main()
