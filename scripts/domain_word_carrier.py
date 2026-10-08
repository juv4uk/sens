#!/usr/bin/env python3
"""Packed typed carrier for exact-width SENS source words.

The carrier is transport framing, not semantic authority. Each record carries
an explicit D1..D9 width descriptor followed by exactly that many payload bits.
The payload is MSB-first and packed without per-word padding. The record count
and strict zero-tail check make the byte stream self-describing and fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass

MAGIC = bytes((0xD7, 0x09, 0x01))
HEADER_BYTES = 7
MAX_WORDS = 1_000_000


class CarrierError(ValueError):
    """Noncanonical or unrecoverable typed source carrier."""


@dataclass(frozen=True)
class DomainWord:
    domain: int
    bits: str

    def __post_init__(self) -> None:
        if not 1 <= self.domain <= 9:
            raise CarrierError(f"domain must be D1..D9, found {self.domain!r}")
        if len(self.bits) != self.domain or set(self.bits) - {"0", "1"}:
            raise CarrierError(f"D{self.domain} requires exactly {self.domain} bits")


def encode(words: list[DomainWord]) -> bytes:
    if len(words) > MAX_WORDS:
        raise CarrierError("too many domain words")

    result = bytearray(MAGIC + len(words).to_bytes(4, "big"))
    accumulator = 0
    filled = 0

    def push(bit: int) -> None:
        nonlocal accumulator, filled
        accumulator = (accumulator << 1) | bit
        filled += 1
        if filled == 8:
            result.append(accumulator)
            accumulator = 0
            filled = 0

    for word in words:
        for shift in range(3, -1, -1):
            push((word.domain >> shift) & 1)
        for bit in word.bits:
            push(int(bit))

    if filled:
        result.append(accumulator << (8 - filled))

    return bytes(result)


def decode(data: bytes) -> list[DomainWord]:
    if len(data) < HEADER_BYTES or data[:3] != MAGIC:
        raise CarrierError("bad typed-source envelope magic/version")

    count = int.from_bytes(data[3:7], "big")
    if count > MAX_WORDS:
        raise CarrierError("declared word count exceeds limit")

    payload = data[HEADER_BYTES:]
    total_bits = len(payload) * 8
    position = 0

    def read(width: int) -> int:
        nonlocal position
        if position + width > total_bits:
            raise CarrierError("truncated domain descriptor or payload")
        value = 0
        for _ in range(width):
            value = (value << 1) | (
                (payload[position // 8] >> (7 - position % 8)) & 1
            )
            position += 1
        return value

    result: list[DomainWord] = []
    for _ in range(count):
        width = read(4)
        if not 1 <= width <= 9:
            raise CarrierError(f"unsupported domain width {width}")
        value = read(width)
        result.append(DomainWord(width, format(value, f"0{width}b")))

    required_bytes = (position + 7) // 8
    if len(payload) != required_bytes:
        raise CarrierError("noncanonical trailing bytes")

    if position % 8:
        tail_mask = (1 << (8 - position % 8)) - 1
        if payload[-1] & tail_mask:
            raise CarrierError("nonzero transport padding")

    if encode(result) != data:
        raise CarrierError("noncanonical typed-source envelope")

    return result
