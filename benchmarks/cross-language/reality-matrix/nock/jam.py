"""Minimal spec-faithful Nock noun jam encoder for #3685.

Independent implementation from the published Urbit serialization rules. It is
self-tested against the official examples before any benchmark row is emitted.

Noun representation:
- atom: non-negative Python int
- cell: 2-tuple (head, tail)
"""

from __future__ import annotations

from typing import TypeAlias

Noun: TypeAlias = int | tuple["Noun", "Noun"]


OFFICIAL_VECTORS: tuple[tuple[Noun, int], ...] = (
    (0, 2),
    (1, 12),
    ((0, 0), 41),
    ((0, 1), 201),
    ((1, 0), 177),
    (7, 248),
    ((0, (1, 2)), 74521),
)


def is_cell(noun: Noun) -> bool:
    return isinstance(noun, tuple)


def jam_stream(noun: Noun) -> list[int]:
    out: list[int] = []
    refs: dict[Noun, int] = {}

    def emit(bit: int) -> None:
        out.append(1 if bit else 0)

    def emit_bits(value: int, count: int) -> None:
        for index in range(count):
            emit(1 if value & (1 << index) else 0)

    def mat(value: int) -> None:
        if value < 0:
            raise ValueError("Nock atoms are non-negative")
        if value == 0:
            emit(1)
            return

        width = value.bit_length()
        width_width = width.bit_length()
        emit_bits(1 << width_width, width_width + 1)
        emit_bits(width & ((1 << (width_width - 1)) - 1), width_width - 1)
        emit_bits(value, width)

    def backref(cursor: int) -> None:
        emit(1)
        emit(1)
        mat(cursor)

    def encode(value: Noun) -> None:
        cursor = refs.get(value)

        if is_cell(value):
            assert isinstance(value, tuple)
            if cursor:
                backref(cursor)
                return

            refs[value] = len(out)
            emit(1)
            emit(0)
            encode(value[0])
            encode(value[1])
            return

        assert isinstance(value, int)
        if cursor:
            if value.bit_length() < cursor.bit_length():
                emit(0)
                mat(value)
            else:
                backref(cursor)
            return

        refs[value] = len(out)
        emit(0)
        mat(value)

    encode(noun)
    return out


def jam(noun: Noun) -> int:
    bits = jam_stream(noun)
    return sum(bit << index for index, bit in enumerate(bits))


def jam_bit_length(noun: Noun) -> int:
    return len(jam_stream(noun))


def jam_byte_length(noun: Noun) -> int:
    return (jam_bit_length(noun) + 7) // 8


def verify_official_vectors() -> None:
    for noun, expected in OFFICIAL_VECTORS:
        observed = jam(noun)
        if observed != expected:
            raise RuntimeError(
                f"official jam vector mismatch: noun={noun!r} expected={expected} observed={observed}"
            )


if __name__ == "__main__":
    verify_official_vectors()
    print("official jam vectors: PASS")
