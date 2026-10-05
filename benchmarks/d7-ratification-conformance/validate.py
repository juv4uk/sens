#!/usr/bin/env python3
"""#2517 historical D7 conformance witness, replayed as research under Contract 11.5.

Owner authority:
  D7 = Sound7/Sanskrit sound-related objects
     + local śloka/sūtra ordinal numbering/provenance
  D7 != general arithmetic Number

This is a semantic-domain guard, not an occupancy table.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TEXT7 = ROOT / "crates" / "sens" / "src" / "text7.rs"
WIRE_TEST = ROOT / "crates" / "sens" / "tests" / "text7_canonical_wire.rs"

MAX7 = 0b1111111


class DomainError(ValueError):
    pass


class RoleError(ValueError):
    pass


class WidthError(ValueError):
    pass


@dataclass(frozen=True)
class D7Object:
    bits: int
    role: str

    def __post_init__(self) -> None:
        if not 0 <= self.bits <= MAX7:
            raise WidthError(self.bits)
        if self.role not in {"sound-cell", "local-ordinal"}:
            raise RoleError(self.role)


@dataclass(frozen=True)
class ArithmeticNumber:
    value: int


@dataclass(frozen=True)
class D14ProvenanceLink:
    ordinal: D7Object
    d14_node: str

    def __post_init__(self) -> None:
        if self.ordinal.role != "local-ordinal":
            raise RoleError("only D7 local ordinals may form this provenance link")


def semantic_key(value: Any) -> tuple[Any, ...]:
    if isinstance(value, D7Object):
        return ("D7", value.role, value.bits)
    if isinstance(value, ArithmeticNumber):
        return ("ArithmeticNumber", value.value)
    if isinstance(value, D14ProvenanceLink):
        return (
            "D7->D14-provenance",
            semantic_key(value.ordinal),
            value.d14_node,
        )
    raise DomainError(type(value).__name__)


def arithmetic_add(left: Any, right: Any) -> ArithmeticNumber:
    if not isinstance(left, ArithmeticNumber) or not isinstance(right, ArithmeticNumber):
        raise DomainError("DOMAIN-MISMATCH")
    return ArithmeticNumber(left.value + right.value)


def arithmetic_mul(left: Any, right: Any) -> ArithmeticNumber:
    if not isinstance(left, ArithmeticNumber) or not isinstance(right, ArithmeticNumber):
        raise DomainError("DOMAIN-MISMATCH")
    return ArithmeticNumber(left.value * right.value)


def arithmetic_recip(value: Any) -> tuple[int, int]:
    if not isinstance(value, ArithmeticNumber):
        raise DomainError("DOMAIN-MISMATCH")
    if value.value == 0:
        raise ZeroDivisionError
    return (1, value.value)


def require_role(value: D7Object, role: str) -> D7Object:
    if value.role != role:
        raise RoleError("ROLE-MISMATCH")
    return value


def erase_role(value: D7Object) -> int:
    return value.bits


def interpret_erased_d7(bits: int) -> D7Object:
    # Width alone cannot decide whether a 7-bit D7 object is a sound cell or
    # a local ordinal. Fail closed instead of guessing.
    if not 0 <= bits <= MAX7:
        raise WidthError(bits)
    raise RoleError("AMBIGUOUS-WITHOUT-ROLE")


def source_contract_gate() -> None:
    text = TEXT7.read_text(encoding="utf-8")
    assert "pub const LOGICAL_WIDTH: u8 = 7;" in text
    assert 'pub const WIRE_TAG: &\'static str = "#t7:";' in text
    assert "callers must not reinterpret them" in text
    assert "as SENS Numbers" in text

    wire = WIRE_TEST.read_text(encoding="utf-8")
    assert 'Text7::from_canonical_wire_token("#q2:101010/1")' in wire
    assert "Err(Text7WireError::MissingTag)" in wire
    assert "existing_number_transport_law_is_unchanged" in wire


def main() -> None:
    source_contract_gate()

    same_bits = 0b0101010
    sound = D7Object(same_bits, "sound-cell")
    ordinal = D7Object(same_bits, "local-ordinal")
    number = ArithmeticNumber(same_bits)

    # Same seven physical bits, three distinct semantic objects.
    assert semantic_key(sound) != semantic_key(ordinal)
    assert semantic_key(ordinal) != semantic_key(number)
    assert semantic_key(sound) != semantic_key(number)

    # Roles cannot silently coerce inside D7.
    try:
        require_role(sound, "local-ordinal")
    except RoleError as exc:
        assert str(exc) == "ROLE-MISMATCH"
    else:
        raise AssertionError("sound silently became ordinal")

    try:
        require_role(ordinal, "sound-cell")
    except RoleError as exc:
        assert str(exc) == "ROLE-MISMATCH"
    else:
        raise AssertionError("ordinal silently became sound")

    # Arithmetic Number laws reject both D7 roles.
    mismatch_cases = 0
    for value in (sound, ordinal):
        for op, args in (
            (arithmetic_add, (value, ArithmeticNumber(1))),
            (arithmetic_mul, (value, ArithmeticNumber(2))),
            (arithmetic_recip, (value,)),
        ):
            try:
                op(*args)
            except DomainError as exc:
                assert str(exc) == "DOMAIN-MISMATCH"
                mismatch_cases += 1
            else:
                raise AssertionError((value, op.__name__))

    # Arithmetic works only in its own domain.
    assert arithmetic_add(number, ArithmeticNumber(1)) == ArithmeticNumber(same_bits + 1)
    assert arithmetic_mul(number, ArithmeticNumber(2)) == ArithmeticNumber(same_bits * 2)

    # Role erasure demonstrates ambiguity, not a default interpretation.
    assert erase_role(sound) == erase_role(ordinal) == same_bits
    try:
        interpret_erased_d7(same_bits)
    except RoleError as exc:
        assert str(exc) == "AMBIGUOUS-WITHOUT-ROLE"
    else:
        raise AssertionError("role-erased D7 bits were guessed")

    # Width gate is exact and fail-closed.
    for bits in (0, 1, 42, 127):
        assert D7Object(bits, "sound-cell").bits == bits
        assert D7Object(bits, "local-ordinal").bits == bits

    width_failures = 0
    for bits in (-1, 128, 255):
        try:
            D7Object(bits, "local-ordinal")
        except WidthError:
            width_failures += 1
        else:
            raise AssertionError(bits)

    # A local ordinal may point to a D14 rule node for provenance, but the
    # resulting object is a provenance link only; no D14 grammatical law is
    # imported into D7.
    provenance = D14ProvenanceLink(ordinal, "panini-node:opaque")
    assert semantic_key(provenance)[0] == "D7->D14-provenance"
    assert provenance.ordinal == ordinal

    # There is deliberately no occupancy claim: width-valid != admitted resident.
    width_valid_coordinate_count = 128

    print("D7-ROLE-BOUNDARY=PASS")
    print("D7-WIDTH=7")
    print("D7-ROLES=sound-cell,local-ordinal")
    print("SAME-BITS-SOUND-VS-ORDINAL=DISTINCT")
    print("SAME-VALUE-ORDINAL-VS-NUMBER=DISTINCT")
    print(f"ARITHMETIC-DOMAIN-MISMATCH-CASES={mismatch_cases}")
    print("ROLE-ERASURE=AMBIGUOUS-WITHOUT-ROLE")
    print(f"WIDTH-FAILURES={width_failures}")
    print("TEXT7-VS-NUMBER-WIRE=SEPARATE")
    print("D14-LINK=PROVENANCE-ONLY")
    print(f"WIDTH-VALID-COORDINATES={width_valid_coordinate_count}")
    print("OCCUPANCY-CLAIM=NONE")
    print("STATUS=PASS-D7-RESEARCH-ROLE-CONFORMANCE")
    print("AUTHORITY=HISTORICAL-OWNER-EVIDENCE;CURRENT=RESEARCH")


if __name__ == "__main__":
    main()
