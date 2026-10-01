#!/usr/bin/env python3
"""#1962: falsify the hypothesis 'every strong seed relation is a cube edge'.

Research-only. Q3 is useful address geometry, but it cannot be the complete
semantic-relation graph because hypercubes are bipartite/triangle-free.
"""

from itertools import combinations, product

SEED = {
    "()": "000",
    "QUOTE": "001",
    "ATOM": "010",
    "EQ": "011",
    "CONS": "100",
    "CAR": "101",
    "CDR": "110",
    "COND": "111",
}


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def cube_has_triangle(width: int) -> bool:
    vertices = ["".join(bits) for bits in product("01", repeat=width)]
    for a, b, c in combinations(vertices, 3):
        if hamming(a, b) == hamming(b, c) == hamming(a, c) == 1:
            return True
    return False


def main() -> None:
    # Three strong historical/algebraic relations around pair-vs-atom structure.
    d_nil_atom = hamming(SEED["()"], SEED["ATOM"])
    d_nil_cons = hamming(SEED["()"], SEED["CONS"])
    d_atom_cons = hamming(SEED["ATOM"], SEED["CONS"])

    print("strong semantic triangle")
    print(f"()   -- ATOM : hamming={d_nil_atom}  historical NIL is atomic")
    print(f"()   -- CONS : hamming={d_nil_cons}  NIL is proper-list ground/terminator")
    print(f"ATOM -- CONS : hamming={d_atom_cons}  ATOM(CONS(x,y)) = 0")

    assert d_nil_atom == 1
    assert d_nil_cons == 1
    assert d_atom_cons == 2

    for width in range(1, 8):
        assert not cube_has_triangle(width), f"Q{width} unexpectedly contains triangle"

    print()
    print("PASS: hypercubes are triangle-free; therefore Hamming-1 adjacency")
    print("cannot represent every strong semantic relation simultaneously.")
    print("Conclusion: cube/prefix geometry is an address substrate; semantic")
    print("relations must remain typed overlays. Local generator subtrees (e.g.")
    print("CAR/CDR selectors) may still have exact semantic path laws.")


if __name__ == "__main__":
    main()
