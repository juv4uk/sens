#!/usr/bin/env python3
"""#2112 CONSTRAINT-0 foundation witness.

Research-only.

Separates primitive fact status from relation extension and proof theory.

For a bounded candidate possibility space Omega, each candidate has one status:
  ADMITTED
  REFUTED
  UNKNOWN

This is not PredicateBit. It is meta-semantic evidence status.

Questions:
- in a complete world, are admitted/refuted complements?
- in an open world, what information is lost by storing only positive or only
  negative extension?
- is the status structure invariant under renaming of candidate fact tokens?
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    ADMITTED = "admitted"
    REFUTED = "refuted"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ConstraintModel:
    omega: frozenset[str]
    status: tuple[tuple[str, Status], ...]

    def __post_init__(self):
        keys = {k for k, _ in self.status}
        assert keys == set(self.omega)
        assert len(keys) == len(self.status)

    def as_map(self):
        return dict(self.status)

    def admitted(self):
        m = self.as_map()
        return frozenset(k for k in self.omega if m[k] is Status.ADMITTED)

    def refuted(self):
        m = self.as_map()
        return frozenset(k for k in self.omega if m[k] is Status.REFUTED)

    def unknown(self):
        m = self.as_map()
        return frozenset(k for k in self.omega if m[k] is Status.UNKNOWN)

    def complete(self):
        return not self.unknown()


def rename(model: ConstraintModel, mapping: dict[str, str]) -> ConstraintModel:
    assert set(mapping) == set(model.omega)
    assert len(set(mapping.values())) == len(mapping)
    return ConstraintModel(
        frozenset(mapping[x] for x in model.omega),
        tuple(sorted((mapping[k], v) for k, v in model.status)),
    )


def same_up_to_renaming(a: ConstraintModel, b: ConstraintModel, mapping: dict[str, str]) -> bool:
    return rename(a, mapping) == b


def positive_projection(model: ConstraintModel):
    """Ordinary extensional positive relation view."""
    return model.admitted()


def negative_projection(model: ConstraintModel):
    """Ordinary extensional forbidden/refuted view."""
    return model.refuted()


def complete_world_duality():
    omega = frozenset({"p", "q", "r", "s"})
    m = ConstraintModel(
        omega,
        (
            ("p", Status.ADMITTED),
            ("q", Status.REFUTED),
            ("r", Status.ADMITTED),
            ("s", Status.REFUTED),
        ),
    )
    assert m.complete()
    assert m.admitted() == omega - m.refuted()
    assert m.refuted() == omega - m.admitted()
    return m


def open_world_loss():
    omega = frozenset({"p", "q", "r"})

    # Same positive relation extension, different epistemic-semantic content.
    a = ConstraintModel(
        omega,
        (
            ("p", Status.ADMITTED),
            ("q", Status.REFUTED),
            ("r", Status.UNKNOWN),
        ),
    )
    b = ConstraintModel(
        omega,
        (
            ("p", Status.ADMITTED),
            ("q", Status.UNKNOWN),
            ("r", Status.REFUTED),
        ),
    )

    assert positive_projection(a) == positive_projection(b) == frozenset({"p"})
    assert a != b
    assert a.refuted() != b.refuted()
    assert a.unknown() != b.unknown()

    # Same negative projection, different positive/unknown content.
    c = ConstraintModel(
        omega,
        (
            ("p", Status.ADMITTED),
            ("q", Status.REFUTED),
            ("r", Status.UNKNOWN),
        ),
    )
    d = ConstraintModel(
        omega,
        (
            ("p", Status.UNKNOWN),
            ("q", Status.REFUTED),
            ("r", Status.ADMITTED),
        ),
    )

    assert negative_projection(c) == negative_projection(d) == frozenset({"q"})
    assert c != d
    assert c.admitted() != d.admitted()
    assert c.unknown() != d.unknown()

    return a, b, c, d


def closed_world_assumption(model: ConstraintModel) -> ConstraintModel:
    """Extra policy: every UNKNOWN is forced to REFUTED.

    This is intentionally a separate transformation, not a theorem.
    """
    return ConstraintModel(
        model.omega,
        tuple(
            (k, Status.REFUTED if v is Status.UNKNOWN else v)
            for k, v in model.status
        ),
    )


def renaming_witness():
    a = ConstraintModel(
        frozenset({"p", "q", "r"}),
        (
            ("p", Status.ADMITTED),
            ("q", Status.REFUTED),
            ("r", Status.UNKNOWN),
        ),
    )
    f = {"p": "alpha", "q": "gamma", "r": "beta"}
    b = ConstraintModel(
        frozenset(f.values()),
        tuple(sorted((f[k], v) for k, v in a.status)),
    )
    assert a != b
    assert same_up_to_renaming(a, b, f)
    return a, b


def main():
    complete = complete_world_duality()
    a, b, c, d = open_world_loss()
    ra, rb = renaming_witness()

    closed = closed_world_assumption(a)
    assert closed.unknown() == frozenset()
    assert closed.refuted() == frozenset({"q", "r"})
    assert a.refuted() == frozenset({"q"})
    assert a.unknown() == frozenset({"r"})

    print("COMPLETE WORLD")
    print("Omega:", sorted(complete.omega))
    print("ADMITTED:", sorted(complete.admitted()))
    print("REFUTED:", sorted(complete.refuted()))
    print("UNKNOWN:", sorted(complete.unknown()))
    print("admitted = Omega \\ refuted:", complete.admitted() == complete.omega - complete.refuted())
    print("refuted = Omega \\ admitted:", complete.refuted() == complete.omega - complete.admitted())
    print()

    print("OPEN WORLD — POSITIVE EXTENSION LOSS")
    print("A positive:", sorted(positive_projection(a)))
    print("B positive:", sorted(positive_projection(b)))
    print("same positive projection:", positive_projection(a) == positive_projection(b))
    print("but A statuses != B statuses:", a != b)
    print()

    print("OPEN WORLD — NEGATIVE EXTENSION LOSS")
    print("C negative:", sorted(negative_projection(c)))
    print("D negative:", sorted(negative_projection(d)))
    print("same negative projection:", negative_projection(c) == negative_projection(d))
    print("but C statuses != D statuses:", c != d)
    print()

    print("CLOSED-WORLD POLICY")
    print("before: refuted", sorted(a.refuted()), "unknown", sorted(a.unknown()))
    print("after:  refuted", sorted(closed.refuted()), "unknown", sorted(closed.unknown()))
    print("result: UNKNOWN->REFUTED is an extra policy transformation, not identity of meanings")
    print()

    print("RENAMING")
    print("host tokens differ:", ra != rb)
    print("status structure preserved up to bijection: YES")
    print()

    print("FOUNDATIONAL CLASSIFICATION")
    print("positive relation extension = ADMITTED slice only")
    print("negative/falsifier extension = REFUTED slice only")
    print("UNKNOWN is independent information in an open world")
    print("absence from positive relation != refutation")
    print("absence from negative relation != admission")
    print("closed-world assumption is additional law/policy")
    print()
    print("PASS: relation extension alone is not a sufficient primitive fact model under unknown!=false.")


if __name__ == "__main__":
    main()
