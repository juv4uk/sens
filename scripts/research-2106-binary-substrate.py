#!/usr/bin/env python3
"""#2106 Foundation−1 binary substrate witness.

Research-only. No production syntax, identity, or semantic authority changes.

Questions:
1. Which laws belong to a neutral two-symbol carrier?
2. Which current layer-0 claims require extra semantic orientation?
3. Can arbitrary binary payloads use a fixed raw delimiter safely?
4. Does the neutral carrier itself force exclusion of epsilon?

The witness is intentionally tiny and exhaustive over bounded spaces.
"""

from __future__ import annotations

# Оптимізований Python прибирає assert; доказові перевірки обов'язкові.
if not __debug__:
    raise SystemExit("FOUNDATION-1: BLOCKED — Python -O вимикає assert")

import itertools
from dataclasses import dataclass

BITS = ("0", "1")
RACANA_CODES = ("00", "01", "10", "11")
RACANA_ROLES = ("sep", "open", "close", "dot")


def bitflip(word: str) -> str:
    return "".join("1" if ch == "0" else "0" for ch in word)


def is_prefix(a: str, b: str) -> bool:
    return b.startswith(a)


def all_words(max_width: int, include_epsilon: bool = True) -> list[str]:
    out = [""] if include_epsilon else []
    for width in range(1, max_width + 1):
        out.extend("".join(bits) for bits in itertools.product(BITS, repeat=width))
    return out


def test_carrier_flip_equivariance() -> int:
    """Neutral carrier structure is invariant under global 0<->1 renaming."""
    words = all_words(5, include_epsilon=True)
    checked = 0
    for a in words:
        fa = bitflip(a)
        assert len(fa) == len(a)
        assert bitflip(fa) == a

        for b in words:
            fb = bitflip(b)

            # Equality/non-equality is preserved.
            assert (a == b) == (fa == fb)

            # Prefix structure is preserved.
            assert is_prefix(a, b) == is_prefix(fa, fb)

            # Concatenation is equivariant.
            assert bitflip(a + b) == fa + fb
            checked += 1

    return checked


def test_predicate_orientation_is_extra() -> None:
    """Carrier symmetry does not choose which symbol means NO or YES."""
    polarity = {"0": "NO", "1": "YES"}

    # Under carrier renaming 0<->1, fixed semantic labels do not remain attached
    # to the same raw bit. Therefore polarity is an added semantic orientation,
    # not a theorem of the neutral alphabet.
    assert polarity["0"] != polarity[bitflip("0")]
    assert polarity["1"] != polarity[bitflip("1")]

    # If semantic labels are swapped together with carrier symbols, behavior is
    # isomorphic. The carrier itself cannot choose between the two orientations.
    flipped_polarity = {bitflip(bit): meaning for bit, meaning in polarity.items()}
    assert flipped_polarity == {"1": "NO", "0": "YES"}


@dataclass(frozen=True)
class RacanaAssignment:
    role_to_code: dict[str, str]

    @property
    def code_to_role(self) -> dict[str, str]:
        return {code: role for role, code in self.role_to_code.items()}

    def encode(self, roles: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(self.role_to_code[role] for role in roles)

    def decode(self, codes: tuple[str, ...]) -> tuple[str, ...]:
        inv = self.code_to_role
        return tuple(inv[code] for code in codes)


def test_racana_label_symmetry() -> int:
    """Abstract structural roles alone do not derive one exact 2-bit labeling."""
    sample_structures = (
        ("open", "close"),
        ("open", "sep", "close"),
        ("open", "open", "close", "close"),
        ("open", "dot", "close"),
        ("sep",),
        ("dot",),
    )

    assignments = []
    for perm in itertools.permutations(RACANA_CODES):
        assignments.append(
            RacanaAssignment(dict(zip(RACANA_ROLES, perm, strict=True)))
        )

    assert len(assignments) == 24

    for assignment in assignments:
        for structure in sample_structures:
            encoded = assignment.encode(structure)
            decoded = assignment.decode(encoded)
            assert decoded == structure

    # Current research labeling is only one of the 24 abstractly valid labels.
    current = RacanaAssignment(
        {
            "sep": "00",
            "open": "10",
            "close": "01",
            "dot": "11",
        }
    )
    assert any(a.role_to_code == current.role_to_code for a in assignments)

    return len(assignments)


def test_raw_delimiter_impossibility(max_delim_width: int = 8) -> int:
    """No fixed unescaped bit pattern can delimit arbitrary binary payloads."""
    collisions = 0
    for width in range(1, max_delim_width + 1):
        for bits in itertools.product(BITS, repeat=width):
            delimiter = "".join(bits)

            # The delimiter itself is an admissible payload under an unrestricted
            # finite-bit carrier, so substring scanning cannot know whether this
            # occurrence is payload or boundary without an escape/framing rule.
            payload = delimiter
            assert delimiter in payload

            # And it can occur strictly inside a larger payload too.
            larger = "0" + delimiter + "1"
            assert delimiter in larger

            collisions += 1

    return collisions


def test_boundary_vs_payload() -> None:
    """A structural word '00' is not the same thing as substring 00 in a word."""
    words = ("10", "00", "101001", "01")
    # Boundaries are represented here by tuple membership/position, not by
    # scanning payload substrings.
    assert words[1] == "00"
    assert "00" in words[2]
    assert words[2] != "00"


def test_order_is_semantically_observable() -> None:
    """Selector positive control proves sequence order cannot be discarded."""

    def left(value):
        return value[0]

    def right(value):
        return value[1]

    actions = {"0": left, "1": right}

    def run(value, suffix: str):
        out = value
        for bit in suffix:
            out = actions[bit](out)
        return out

    value = (("a", "b"), ("c", "d"))

    # Same multiset of bits, different ordered program.
    assert sorted("01") == sorted("10")
    assert run(value, "01") == "b"
    assert run(value, "10") == "c"
    assert run(value, "01") != run(value, "10")

    # Multiplicity/width is observable too.
    deeper = ((("x", "y"), "z"), "w")
    assert run(deeper, "0") == (("x", "y"), "z")
    assert run(deeper, "00") == ("x", "y")
    assert run(deeper, "0") != run(deeper, "00")


def test_epsilon_models() -> None:
    """Both epsilon-including and positive-word carriers satisfy common laws."""
    monoid_words = set(all_words(4, include_epsilon=True))
    semigroup_words = set(all_words(4, include_epsilon=False))

    assert "" in monoid_words
    assert "" not in semigroup_words

    # Shared positive-word laws hold in both models.
    positives = all_words(3, include_epsilon=False)
    for a in positives:
        for b in positives:
            assert (a == b) == (a == b)
            assert len(a + b) == len(a) + len(b)
            assert a + b in monoid_words or len(a + b) > 4
            assert a + b in semigroup_words or len(a + b) > 4

    # Epsilon has a clean carrier-level algebraic role if included.
    for a in all_words(4, include_epsilon=True):
        assert "" + a == a
        assert a + "" == a
        assert is_prefix("", a)

    # This demonstrates consistency of epsilon at the carrier layer only.
    # It does not prove epsilon should be a SENS semantic identity.


def main() -> None:
    pair_checks = test_carrier_flip_equivariance()
    test_predicate_orientation_is_extra()
    racana_assignments = test_racana_label_symmetry()
    delimiter_collisions = test_raw_delimiter_impossibility()
    test_boundary_vs_payload()
    test_order_is_semantically_observable()
    test_epsilon_models()

    print("FOUNDATION-1 binary substrate witness: PASS")
    print(f"carrier flip-equivariance pair checks: {pair_checks}")
    print("bit alphabet global 0<->1 symmetry: PASS")
    print("PredicateBit polarity requires extra semantic orientation: PASS")
    print(f"racanā2 abstract-role bijections surviving: {racana_assignments}/24")
    print(
        "racanā2 exact 2-bit assignment derived from abstract roles alone: NO"
    )
    print(
        f"raw delimiter candidates with payload collision (width 1..8): "
        f"{delimiter_collisions}"
    )
    print("fixed unescaped in-band delimiter for arbitrary words: IMPOSSIBLE")
    print("bounded-word boundary distinct from payload substring: PASS")
    print("ordered-bit sequence semantically observable in selector witness: PASS")
    print("unordered bit multiset as identity carrier: INSUFFICIENT")
    print("epsilon-including carrier model: CONSISTENT")
    print("positive-word-only carrier model: CONSISTENT")
    print("epsilon semantic admission: UNRESOLVED")
    print("NON-CONCLUSION: D1 polarity is not rejected")
    print("NON-CONCLUSION: racanā2 roles are not rejected")
    print("NON-CONCLUSION: current racanā2 code assignment is not derived here")


if __name__ == "__main__":
    main()
