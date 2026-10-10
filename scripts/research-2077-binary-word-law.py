#!/usr/bin/env python3
"""#2077 Foundation-0 executable witness.

Research/shadow only. This file does not change the ratified language contract.

It tests the representation-independent candidate law:
  canonical binary word = exact bounded bit sequence
  equality = same width + same bits
  semantic admission is separate from syntactic word validity

The framing codec below is deliberately a witness mechanism, not language
semantics: 32-bit width prefix + packed payload bytes.
"""

from __future__ import annotations

# Режим Python -O прибирає assert, тому не може засвідчувати Foundation-0.
if not __debug__:
    raise SystemExit("FOUNDATION-0: BLOCKED — Python -O вимикає assert")

from dataclasses import dataclass
from itertools import product
from typing import Iterable


@dataclass(frozen=True, order=True)
class BinaryWord:
    bits: str

    def __post_init__(self) -> None:
        if any(ch not in "01" for ch in self.bits):
            raise ValueError("binary word must contain only 0/1")

    @property
    def width(self) -> int:
        return len(self.bits)

    def is_prefix_of(self, other: "BinaryWord") -> bool:
        return other.bits.startswith(self.bits)

    def to_sens8(self) -> int:
        if self.width != 8:
            raise ValueError("Sens8 projection requires exact width 8")
        return int(self.bits, 2)

    @staticmethod
    def from_sens8(value: int) -> "BinaryWord":
        if not (0 <= value <= 0xFF):
            raise ValueError("Sens8 value out of range")
        return BinaryWord(f"{value:08b}")

    def packed_payload(self) -> bytes:
        byte_len = (self.width + 7) // 8
        if self.width == 0:
            return b""
        return int(self.bits, 2).to_bytes(byte_len, "big")

    @staticmethod
    def from_packed(width: int, payload: bytes) -> "BinaryWord":
        if width < 0:
            raise ValueError("width must be non-negative")
        expected = (width + 7) // 8
        if len(payload) != expected:
            raise ValueError("payload length does not match width")

        unused = expected * 8 - width
        if unused and (payload[0] >> (8 - unused)) != 0:
            raise ValueError("non-zero padding bits in canonical frame")

        if width == 0:
            return BinaryWord("")
        value = int.from_bytes(payload, "big")
        return BinaryWord(f"{value:0{width}b}")


def encode_frame(word: BinaryWord) -> bytes:
    return word.width.to_bytes(4, "big") + word.packed_payload()


def decode_frame(data: bytes, offset: int = 0) -> tuple[BinaryWord, int]:
    if offset + 4 > len(data):
        raise ValueError("truncated width prefix")
    width = int.from_bytes(data[offset : offset + 4], "big")
    if width < 0:
        raise ValueError("negative width is invalid")
    byte_len = (width + 7) // 8
    start = offset + 4
    end = start + byte_len
    if end > len(data):
        raise ValueError("truncated payload")
    return BinaryWord.from_packed(width, data[start:end]), end


def encode_stream(words: Iterable[BinaryWord]) -> bytes:
    return b"".join(encode_frame(word) for word in words)


def decode_stream(data: bytes) -> list[BinaryWord]:
    out: list[BinaryWord] = []
    offset = 0
    while offset < len(data):
        word, offset = decode_frame(data, offset)
        out.append(word)
    return out


def expect_raises(fn, label: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(f"expected ValueError: {label}")


def exhaustive_small_roundtrip(max_width: int = 12) -> int:
    checked = 0
    for width in range(1, max_width + 1):
        for chars in product("01", repeat=width):
            word = BinaryWord("".join(chars))
            assert BinaryWord.from_packed(width, word.packed_payload()) == word
            checked += 1
    return checked


def main() -> None:
    # Exact identity and leading-zero law.
    # Epsilon is admitted only as a carrier-level test value here; this does
    # not assign it language meaning or ratify it as a callable identity.
    epsilon = BinaryWord("")
    assert decode_stream(encode_stream([epsilon])) == [epsilon]

    one = BinaryWord("1")
    zero_one = BinaryWord("01")
    zero_zero_one = BinaryWord("001")
    assert one != zero_one != zero_zero_one
    assert len({one, zero_one, zero_zero_one}) == 3
    assert int(one.bits, 2) == int(zero_one.bits, 2) == int(zero_zero_one.bits, 2)

    # Prefix is a relation, never identity collapse.
    a = BinaryWord("001")
    b = BinaryWord("0010")
    assert a != b
    assert a.is_prefix_of(b)

    # Boundaries are external to word bits and survive framing.
    words = [BinaryWord("10"), BinaryWord("001"), BinaryWord("01")]
    framed = encode_stream(words)
    assert decode_stream(framed) == words
    assert BinaryWord("1000101") not in words

    # Internal 00 is ordinary word data, not a separator.
    internal = BinaryWord("101001001")
    assert decode_stream(encode_stream([internal])) == [internal]

    # Width boundaries are mechanically irrelevant to identity validity.
    boundary_words = [
        BinaryWord("0" * 6 + "1"),   # 7
        BinaryWord("0" * 7 + "1"),   # 8
        BinaryWord("0" * 8 + "1"),   # 9
        BinaryWord("0" * 63 + "1"),  # 64
        BinaryWord("0" * 64 + "1"),  # 65
    ]
    assert decode_stream(encode_stream(boundary_words)) == boundary_words

    # Very long exact identity.
    long_bits = ("00101101" * 512)  # 4096 bits, begins with leading zeroes.
    long_word = BinaryWord(long_bits)
    assert long_word.width == 4096
    assert decode_stream(encode_stream([long_word])) == [long_word]

    # Sens8 is a checked reversible projection, not the identity universe.
    eight = BinaryWord("00000101")
    packed = eight.to_sens8()
    assert packed == 5
    assert BinaryWord.from_sens8(packed) == eight
    for invalid in (BinaryWord("101"), BinaryWord("000000101"), BinaryWord("1" * 65)):
        expect_raises(invalid.to_sens8, f"width={invalid.width}")

    # Canonical framing rejects hidden information in padding.
    expect_raises(
        lambda: BinaryWord.from_packed(3, bytes([0b11100001])),
        "non-zero high padding",
    )

    # Semantic admission is an independent relation, not inferred from width.
    admitted = {BinaryWord("101"), BinaryWord("110")}
    assert BinaryWord("101") in admitted
    assert BinaryWord("111") not in admitted
    assert BinaryWord("111").width == BinaryWord("101").width

    # Syntax validity itself creates no meaning.
    syntactically_valid_but_unknown = BinaryWord("010101010101")
    assert syntactically_valid_but_unknown not in admitted

    small_checked = exhaustive_small_roundtrip()

    print("FOUNDATION-0 binary-word witness: PASS")
    print(f"small exhaustive round-trips: {small_checked}")
    print("epsilon carrier round-trip: PASS (semantic admission unresolved)")
    print("leading-zero distinctness: PASS")
    print("prefix-without-equality-collapse: PASS")
    print("multi-word boundary round-trip: PASS")
    print("internal-00-is-data: PASS")
    print("7/8/9 and 64/65 widths: PASS")
    print("4096-bit round-trip: PASS")
    print("Sens8 checked projection: PASS")
    print("numeric-collapse-detected: PASS")
    print("semantic-admission-independent-of-width: PASS")
    print("NON-CONCLUSION: epsilon semantic admission is unresolved")
    print("NON-CONCLUSION: no new word meaning is ratified")
    print("NON-CONCLUSION: framing format is witness-only, not semantic authority")


if __name__ == "__main__":
    main()
