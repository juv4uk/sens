#!/usr/bin/env python3
"""Experimental typed file carrier for exact-width D1-D9 words.

NOT a new SENS semantic contract. The 4-bit domain descriptor is file framing,
not resident payload. Format v1: D7 09 01 | uint32 count, big endian |
MSB-first compact records [4-bit domain width 1..9][exact n-bit payload].
No per-word byte padding. EOS is the record count; trailing zero-padding must
be the minimal tail. Based on #4430 / #2189 / #2833; not release authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys

MAGIC = bytes((0xD7, 0x09, 0x01))
HEADER_BYTES = 7
MAX_WORDS = 1_000_000


class CarrierError(ValueError):
    """Noncanonical or unrecoverable domain-word sequence."""


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
    """Preserve each typed word; never concatenate naked bit strings."""
    if len(words) > MAX_WORDS:
        raise CarrierError("too many words")
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
        if not isinstance(word, DomainWord):
            raise CarrierError("input must contain typed DomainWord entries")
        for shift in range(3, -1, -1):
            push((word.domain >> shift) & 1)
        for ch in word.bits:
            push(int(ch))
    if filled:
        result.append(accumulator << (8 - filled))
    return bytes(result)


def decode(data: bytes) -> list[DomainWord]:
    if len(data) < HEADER_BYTES or data[:3] != MAGIC:
        raise CarrierError("bad domain-word envelope magic/version")
    count = int.from_bytes(data[3:7], "big")
    if count > MAX_WORDS:
        raise CarrierError("declared word count exceeds limit")
    payload = data[HEADER_BYTES:]
    total_bits = len(payload) * 8
    position = 0

    def read(width: int) -> int:
        nonlocal position
        if position + width > total_bits:
            raise CarrierError("truncated domain descriptor or exact-width payload")
        n = 0
        for _ in range(width):
            n = (n << 1) | ((payload[position // 8] >> (7 - position % 8)) & 1)
            position += 1
        return n

    result = []
    for _ in range(count):
        width = read(4)
        if not 1 <= width <= 9:
            raise CarrierError(f"unsupported D{width} record")
        value = read(width)
        result.append(DomainWord(width, format(value, f"0{width}b")))
    if len(payload) != (position + 7) // 8:
        raise CarrierError("noncanonical trailing bytes")
    if position % 8 and (payload[-1] & ((1 << (8 - position % 8)) - 1)):
        raise CarrierError("nonzero transport padding")
    if encode(result) != data:
        raise CarrierError("noncanonical encoded bytes")
    return result


def display(words: list[DomainWord]) -> str:
    """Human diagnostic; must never become canonical file content."""
    return " ".join(f"D{w.domain}:{w.bits}" for w in words)


def parse_display(text: str) -> list[DomainWord]:
    """Explicit typed test/debug input, not a Ukrainian program encoder."""
    result = []
    for token in text.split():
        if not token.startswith("D") or ":" not in token:
            raise CarrierError(f"typed word required, got {token!r}")
        prefix, bits = token[1:].split(":", 1)
        if not prefix.isascii() or not prefix.isdecimal() or str(int(prefix)) != prefix:
            raise CarrierError("noncanonical width label")
        result.append(DomainWord(int(prefix), bits))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("encode-debug", "decode-debug", "check"))
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "encode-debug":
            if args.output is None:
                parser.error("encode-debug requires --output")
            args.output.write_bytes(
                encode(parse_display(args.input.read_text(encoding="utf-8")))
            )
        else:
            words = decode(args.input.read_bytes())
            if args.mode == "decode-debug":
                if args.output:
                    parser.error("debug view is terminal-only; omit --output")
                print(display(words))
            else:
                print(f"PASS: {len(words)} typed words, canonical envelope")
    except (CarrierError, OSError, UnicodeError) as exc:
        print(f"domain-word-carrier: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
