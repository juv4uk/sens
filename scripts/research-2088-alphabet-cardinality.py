#!/usr/bin/env python3
"""#2088 alphabet-cardinality foundation witness.

Research-only.

Separates three propositions:

A. Exact identity alone does not force a binary alphabet.
B. A law requiring two distinct one-symbol refinements from the same parent
   forces alphabet cardinality >= 2.
C. Once cardinality 2 is fixed, the exact representative symbols 0/1 are
   arbitrary up to a bijective renaming that preserves word structure.

This does not ratify any particular SENS semantic family.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class Word:
    symbols: tuple[str, ...]

    @property
    def width(self) -> int:
        return len(self.symbols)

    def append(self, symbol: str) -> "Word":
        return Word(self.symbols + (symbol,))

    def parent(self) -> "Word | None":
        if not self.symbols:
            return None
        return Word(self.symbols[:-1])

    def is_prefix_of(self, other: "Word") -> bool:
        return (
            self.width <= other.width
            and self.symbols == other.symbols[: self.width]
        )


def all_words(alphabet: tuple[str, ...], max_width: int, include_empty=False):
    start = 0 if include_empty else 1
    for width in range(start, max_width + 1):
        for xs in product(alphabet, repeat=width):
            yield Word(tuple(xs))


def unary_identity_witness():
    alphabet = ("•",)
    words = [Word(tuple("•" for _ in range(n))) for n in range(1, 9)]

    # Exact identity remains injective simply because widths differ.
    assert len(set(words)) == len(words)
    assert [w.width for w in words] == list(range(1, 9))

    # This proves only that identity distinction is possible over a unary
    # alphabet. It says nothing about branching.
    return words


def distinct_one_step_children(parent: Word, alphabet: tuple[str, ...]):
    return {parent.append(symbol) for symbol in alphabet}


def branching_lower_bound():
    parent = Word(("p",))

    unary = ("•",)
    binary = ("0", "1")
    ternary = ("a", "b", "c")

    u = distinct_one_step_children(parent, unary)
    b = distinct_one_step_children(parent, binary)
    t = distinct_one_step_children(parent, ternary)

    assert len(u) == 1
    assert len(b) == 2
    assert len(t) == 3

    # Therefore any law demanding two distinct immediate one-symbol refinements
    # cannot be represented by a unary alphabet without changing what "one
    # refinement step" means.
    assert len(u) < 2
    assert len(b) >= 2

    return len(u), len(b), len(t)


def rename_word(word: Word, mapping: dict[str, str]) -> Word:
    return Word(tuple(mapping[s] for s in word.symbols))


def binary_renaming_isomorphism():
    src = ("0", "1")
    dst = ("α", "β")
    f = {"0": "α", "1": "β"}
    finv = {"α": "0", "β": "1"}

    src_words = list(all_words(src, 6, include_empty=True))
    dst_words = list(all_words(dst, 6, include_empty=True))

    # Bijection on the bounded universe.
    mapped = {rename_word(w, f) for w in src_words}
    assert mapped == set(dst_words)

    # Exact round-trip.
    for w in src_words:
        assert rename_word(rename_word(w, f), finv) == w

    # Width and equality.
    for a, b in product(src_words, repeat=2):
        fa, fb = rename_word(a, f), rename_word(b, f)
        assert fa.width == a.width
        assert fb.width == b.width
        assert (a == b) == (fa == fb)
        assert a.is_prefix_of(b) == fa.is_prefix_of(fb)

    # Parent and append commute.
    for w in src_words:
        fw = rename_word(w, f)
        if w.parent() is None:
            assert fw.parent() is None
        else:
            assert rename_word(w.parent(), f) == fw.parent()

        for s in src:
            assert rename_word(w.append(s), f) == fw.append(f[s])

    # Explicit two-branch path witness.
    p = Word(("1", "0", "1"))
    c0 = p.append("0")
    c1 = p.append("1")
    fp = rename_word(p, f)
    assert rename_word(c0, f) == fp.append("α")
    assert rename_word(c1, f) == fp.append("β")
    assert c0 != c1
    assert fp.append("α") != fp.append("β")

    return len(src_words)


def main():
    unary = unary_identity_witness()
    u, b, t = branching_lower_bound()
    iso_n = binary_renaming_isomorphism()

    print("IDENTITY-ONLY COUNTERMODEL")
    print("alphabet = {•}")
    print("distinct exact words:", " ".join("•" * w.width for w in unary))
    print("result: exact identity remains distinguishable by width")
    print()

    print("ONE-STEP BRANCH CAPACITY")
    print("alphabet-size\timmediate-distinct-children")
    print(f"1\t{u}")
    print(f"2\t{b}")
    print(f"3\t{t}")
    print("result: two distinct immediate refinements require alphabet cardinality >= 2")
    print()

    print("BINARY RENAMING ISOMORPHISM")
    print("0 <-> α")
    print("1 <-> β")
    print("bounded words checked:", iso_n)
    print("preserved: width equality prefix parent append two-branch structure")
    print()

    print("FOUNDATIONAL CLASSIFICATION")
    print("generic exact identity -> DOES NOT derive binary alphabet")
    print("two-child one-step generator -> DOES derive alphabet cardinality >= 2")
    print("exact symbols 0/1 -> NOT derived by those structural laws; representatives up to renaming")
    print()
    print("PASS: binary necessity is assumption-dependent, not automatic.")


if __name__ == "__main__":
    main()
