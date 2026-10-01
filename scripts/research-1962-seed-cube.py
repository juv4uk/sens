#!/usr/bin/env python3
"""#1962: перевірка геометрії повного 3-бітного bīja3.

Research-only. Не є semantic authority.
"""

from itertools import permutations

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

# Лише bounded strong relations, для яких є історична/алгебраїчна підстава.
# Ми навмисно НЕ додаємо слабкі "схожі за змістом" ребра.
RELATIONS = (
    ("CONS", "CAR", "projection-left: CAR(CONS(x,y))=x"),
    ("CONS", "CDR", "projection-right: CDR(CONS(x,y))=y"),
    ("()", "CONS", "list-ground/terminator"),
    ("()", "ATOM", "NIL is an atom in historical Lisp"),
    ("ATOM", "EQ", "historical EQ domain is atomic symbols"),
)


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def verify_current() -> None:
    for left, right, why in RELATIONS:
        d = hamming(SEED[left], SEED[right])
        assert d == 1, (left, right, d, why)


def count_cube_embeddings() -> int:
    """Скільки bijections 8 semantic nodes -> cube vertices зберігають ці ребра як adjacency."""
    labels = tuple(SEED)
    codes = tuple(f"{n:03b}" for n in range(8))
    count = 0
    for perm in permutations(codes):
        placement = dict(zip(labels, perm))
        if all(hamming(placement[a], placement[b]) == 1 for a, b, _ in RELATIONS):
            count += 1
    return count


def main() -> None:
    verify_current()

    print("bīja3 strong-relation geometry")
    for left, right, why in RELATIONS:
        print(
            f"{SEED[left]}:{left:5s} <-> {SEED[right]}:{right:5s} "
            f"hamming=1  {why}"
        )

    embeddings = count_cube_embeddings()
    print(f"\nvalid cube embeddings for these bounded constraints: {embeddings}")
    print("current historical ordering: VALID")
    print(
        "interpretation: current bīja3 preserves every tested strong relation "
        "as a cube edge, but the constraints do not uniquely determine all 8 positions."
    )


if __name__ == "__main__":
    main()
