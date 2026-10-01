#!/usr/bin/env python3
"""#2092 WORD-ALGEBRA-0 research witness.

Compares four tiny identity/path algebras on the same bounded examples.

A: free semigroup Sigma+       -- total concatenation, no empty word
B: free monoid Sigma*          -- total concatenation + epsilon
C: opaque identities           -- exact equality/extent + external parent relation
D: productive paths            -- exact identity + one-step refine/parent only

Purpose:
- determine which algebraic structure is actually required by current
  foundation/generator obligations;
- show when total concatenation, epsilon, cancellation, etc. are stronger than
  the currently needed semantics.

Research-only. Host tuples/integers are witness mechanisms, never authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

ALPHABET = ("0", "1")


# ---------- A: free semigroup Sigma+ ----------

@dataclass(frozen=True)
class SemigroupWord:
    xs: tuple[str, ...]

    def __post_init__(self):
        assert len(self.xs) >= 1
        assert all(x in ALPHABET for x in self.xs)

    @property
    def extent(self) -> int:
        return len(self.xs)

    def concat(self, other: "SemigroupWord") -> "SemigroupWord":
        return SemigroupWord(self.xs + other.xs)

    def refine(self, symbol: str) -> "SemigroupWord":
        return self.concat(SemigroupWord((symbol,)))

    def parent(self) -> Optional["SemigroupWord"]:
        if len(self.xs) == 1:
            return None
        return SemigroupWord(self.xs[:-1])

    def is_prefix_of(self, other: "SemigroupWord") -> bool:
        return self.extent <= other.extent and self.xs == other.xs[: self.extent]


# ---------- B: free monoid Sigma* ----------

@dataclass(frozen=True)
class MonoidWord:
    xs: tuple[str, ...]

    def __post_init__(self):
        assert all(x in ALPHABET for x in self.xs)

    @property
    def extent(self) -> int:
        return len(self.xs)

    def concat(self, other: "MonoidWord") -> "MonoidWord":
        return MonoidWord(self.xs + other.xs)

    def refine(self, symbol: str) -> "MonoidWord":
        return self.concat(MonoidWord((symbol,)))

    def parent(self) -> Optional["MonoidWord"]:
        if not self.xs:
            return None
        return MonoidWord(self.xs[:-1])

    def is_prefix_of(self, other: "MonoidWord") -> bool:
        return self.extent <= other.extent and self.xs == other.xs[: self.extent]


# ---------- C: opaque exact identities + external relation ----------

@dataclass(frozen=True)
class OpaqueIdentity:
    token: int
    extent: int


class OpaqueRelationModel:
    """Identity is opaque. Parent/children are external admitted relations.

    The model intentionally exposes NO concatenation operation.
    """

    def __init__(self):
        # Same visible bounded corpus as words 1, 01, 001, 101, 1010, 1011.
        # Tokens are arbitrary and deliberately non-numeric relative to bits.
        self.by_label = {
            "1": OpaqueIdentity(71, 1),
            "01": OpaqueIdentity(11, 2),
            "001": OpaqueIdentity(53, 3),
            "101": OpaqueIdentity(29, 3),
            "1010": OpaqueIdentity(97, 4),
            "1011": OpaqueIdentity(31, 4),
        }
        self._parent = {
            self.by_label["1010"]: self.by_label["101"],
            self.by_label["1011"]: self.by_label["101"],
        }
        self._edge_label = {
            self.by_label["1010"]: "0",
            self.by_label["1011"]: "1",
        }

    def parent(self, x: OpaqueIdentity) -> Optional[OpaqueIdentity]:
        return self._parent.get(x)

    def children(self, x: OpaqueIdentity) -> tuple[OpaqueIdentity, ...]:
        return tuple(child for child, p in self._parent.items() if p == x)

    def refinement_label(self, child: OpaqueIdentity) -> Optional[str]:
        return self._edge_label.get(child)


# ---------- D: productive paths, one-step only ----------

@dataclass(frozen=True)
class ProductivePath:
    """No arbitrary path x path concatenation is part of the interface."""

    root: str
    steps: tuple[str, ...]

    def __post_init__(self):
        assert self.root
        assert all(s in ALPHABET for s in self.steps)

    @property
    def extent(self) -> int:
        # abstract extent of the path identity in this witness
        return 1 + len(self.steps)

    def refine(self, symbol: str) -> "ProductivePath":
        assert symbol in ALPHABET
        return ProductivePath(self.root, self.steps + (symbol,))

    def parent(self) -> Optional["ProductivePath"]:
        if not self.steps:
            return None
        return ProductivePath(self.root, self.steps[:-1])

    def is_prefix_of(self, other: "ProductivePath") -> bool:
        return (
            self.root == other.root
            and len(self.steps) <= len(other.steps)
            and self.steps == other.steps[: len(self.steps)]
        )


# ---------- shared obligations ----------

def exact_identity_obligation(factory):
    one = factory("1")
    zero_one = factory("01")
    zero_zero_one = factory("001")
    assert one != zero_one != zero_zero_one
    assert len({one, zero_one, zero_zero_one}) == 3


def semigroup_factory(s: str):
    return SemigroupWord(tuple(s))


def monoid_factory(s: str):
    return MonoidWord(tuple(s))


def test_semigroup():
    exact_identity_obligation(semigroup_factory)

    p = SemigroupWord(tuple("101"))
    c0 = p.refine("0")
    c1 = p.refine("1")
    assert c0 != c1
    assert c0.parent() == p
    assert c1.parent() == p
    assert p.is_prefix_of(c0) and p.is_prefix_of(c1)

    # Associativity.
    a, b, c = map(semigroup_factory, ("1", "01", "001"))
    assert a.concat(b).concat(c) == a.concat(b.concat(c))

    # Cancellation in the free semigroup.
    x, y, prefix = map(semigroup_factory, ("01", "001", "1"))
    assert prefix.concat(x) != prefix.concat(y)
    assert x.concat(prefix) != y.concat(prefix)

    return {
        "exact_identity": True,
        "extent": True,
        "one_step_refine": True,
        "parent": True,
        "prefix": True,
        "total_concat": True,
        "neutral_element": False,
        "cancellation": True,
        "opaque_identity_possible": False,
    }


def test_monoid():
    exact_identity_obligation(monoid_factory)

    eps = MonoidWord(())
    x = monoid_factory("101")
    assert eps.concat(x) == x == x.concat(eps)

    c0 = x.refine("0")
    c1 = x.refine("1")
    assert c0 != c1
    assert c0.parent() == x
    assert c1.parent() == x

    a, b, c = map(monoid_factory, ("1", "01", "001"))
    assert a.concat(b).concat(c) == a.concat(b.concat(c))

    return {
        "exact_identity": True,
        "extent": True,
        "one_step_refine": True,
        "parent": True,
        "prefix": True,
        "total_concat": True,
        "neutral_element": True,
        "cancellation": True,
        "opaque_identity_possible": False,
    }


def test_opaque():
    m = OpaqueRelationModel()
    a, b, c = (m.by_label[k] for k in ("1", "01", "001"))
    assert len({a, b, c}) == 3
    assert (a.extent, b.extent, c.extent) == (1, 2, 3)

    p = m.by_label["101"]
    c0, c1 = m.by_label["1010"], m.by_label["1011"]
    assert c0 != c1
    assert m.parent(c0) == p
    assert m.parent(c1) == p
    assert {m.refinement_label(c0), m.refinement_label(c1)} == {"0", "1"}

    # There is deliberately no concat/refine method on OpaqueIdentity/model.
    assert not hasattr(OpaqueIdentity, "concat")
    assert not hasattr(m, "concat")

    return {
        "exact_identity": True,
        "extent": True,
        "one_step_refine": True,  # external admitted relation
        "parent": True,
        "prefix": False,          # not generally provided
        "total_concat": False,
        "neutral_element": False,
        "cancellation": False,
        "opaque_identity_possible": True,
    }


def test_productive():
    # Use roots that correspond only to labels for comparison; no concat exists.
    a = ProductivePath("r1", ())
    b = ProductivePath("r01", ())
    c = ProductivePath("r001", ())
    assert len({a, b, c}) == 3

    p = ProductivePath("selector-root", ())
    c0 = p.refine("0")
    c1 = p.refine("1")
    assert c0 != c1
    assert c0.parent() == p
    assert c1.parent() == p
    assert p.is_prefix_of(c0) and p.is_prefix_of(c1)

    # One-step refinement is injective in both parent and symbol.
    q = ProductivePath("other-root", ())
    assert p.refine("0") != q.refine("0")
    assert p.refine("0") != p.refine("1")

    assert not hasattr(ProductivePath, "concat")

    return {
        "exact_identity": True,
        "extent": True,
        "one_step_refine": True,
        "parent": True,
        "prefix": True,
        "total_concat": False,
        "neutral_element": False,
        "cancellation": False,  # arbitrary concat cancellation is not even stated
        "opaque_identity_possible": False,
    }


def external_frame(items: list[tuple[str, ...]]):
    """Length framing is external; no delimiter symbol enters identity."""
    return tuple((len(x), x) for x in items)


def boundary_witness():
    items = [tuple("10"), tuple("001"), tuple("01")]
    framed = external_frame(items)
    assert tuple(x for _, x in framed) == tuple(items)
    assert framed == (
        (2, ("1", "0")),
        (3, ("0", "0", "1")),
        (2, ("0", "1")),
    )
    return framed


def main():
    rows = {
        "A-semigroup": test_semigroup(),
        "B-monoid": test_monoid(),
        "C-opaque+relation": test_opaque(),
        "D-productive-path": test_productive(),
    }
    framed = boundary_witness()

    props = [
        "exact_identity",
        "extent",
        "one_step_refine",
        "parent",
        "prefix",
        "total_concat",
        "neutral_element",
        "cancellation",
        "opaque_identity_possible",
    ]

    print("model\\t" + "\\t".join(props))
    for name, row in rows.items():
        print(name + "\\t" + "\\t".join("YES" if row[p] else "NO" for p in props))

    print()
    print("EXTERNAL BOUNDARY WITNESS")
    print(framed)
    print("result: word boundaries can live outside identity symbols")
    print()

    print("FOUNDATIONAL CONSEQUENCES")
    print("- exact identity + extent do NOT imply total concatenation")
    print("- a two-child generator needs one-step refinement, but D satisfies it without W×W concat")
    print("- epsilon/neutral element is extra structure present in B only")
    print("- cancellation of arbitrary concatenation is extra algebra, not required by C/D")
    print("- parent-child relation can be admitted externally (C) or generated stepwise (D)")
    print("- serializer framing can remain outside the identity algebra")
    print()
    print("WEAKEST CURRENT-SCOPE CLASSIFICATION")
    print("identity-only obligations: C is already a countermodel to 'sequence concat is necessary'")
    print("productive two-child path obligations: D suffices without total concatenation")
    print("A/B are stronger algebras; usefulness does not by itself make their extra laws semantic")
    print()
    print("PASS: total word concatenation is not forced by the modeled current obligations.")


if __name__ == "__main__":
    main()
