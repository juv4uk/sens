#!/usr/bin/env python3
"""#1962: bounded framing witness for variable-width semantic words.

Research-only. This models an outer wire envelope; it does not change
racanā2/bīja3 identities or current runtime framing.
"""

from __future__ import annotations

from itertools import product


def gamma_positive(value: int) -> str:
    if value < 1:
        raise ValueError("gamma code needs positive integer")
    bits = f"{value:b}"
    return "0" * (len(bits) - 1) + bits


def width_header(width: int) -> str:
    if width < 1:
        raise ValueError("width must be positive")
    if width <= 7:
        return f"{width - 1:03b}"
    return "111" + gamma_positive(width - 7)


def encode_words(words: list[str]) -> str:
    out = []
    for word in words:
        if not word or any(c not in "01" for c in word):
            raise ValueError(f"not a binary word: {word!r}")
        out.append(width_header(len(word)))
        out.append(word)
    return "".join(out)


def read_gamma(bits: str, pos: int) -> tuple[int, int]:
    zeros = 0
    while pos < len(bits) and bits[pos] == "0":
        zeros += 1
        pos += 1
    if pos >= len(bits):
        raise ValueError("truncated gamma code")
    end = pos + zeros + 1
    if end > len(bits):
        raise ValueError("truncated gamma payload")
    return int(bits[pos:end], 2), end


def decode_words(bits: str) -> list[str]:
    if any(c not in "01" for c in bits):
        raise ValueError("wire must contain only bits")

    pos = 0
    out = []
    while pos < len(bits):
        if pos + 3 > len(bits):
            raise ValueError("truncated width header")
        tag = bits[pos : pos + 3]
        pos += 3
        raw = int(tag, 2)
        if raw < 7:
            width = raw + 1
        else:
            extra, pos = read_gamma(bits, pos)
            width = extra + 7

        end = pos + width
        if end > len(bits):
            raise ValueError("truncated semantic word")
        out.append(bits[pos:end])
        pos = end

    return out


def wire_cost(width: int) -> int:
    return len(width_header(width)) + width


def verify_bounded() -> None:
    all_words = []
    for width in range(1, 9):
        for n in range(1 << width):
            word = f"{n:0{width}b}"
            all_words.append(word)
            encoded = encode_words([word])
            assert decode_words(encoded) == [word]

    short = [w for w in all_words if len(w) <= 4]
    for a, b in product(short, repeat=2):
        encoded = encode_words([a, b])
        assert decode_words(encoded) == [a, b]

    example = ["10", "0001", "01"]
    encoded = encode_words(example)
    assert decode_words(encoded) == example
    assert encoded == "00110" + "0110001" + "00101"


def main() -> None:
    verify_bounded()

    print("width\theader\twire-cost")
    for width in range(1, 13):
        print(f"{width}\t{width_header(width)}\t{wire_cost(width)}")

    example = ["10", "0001", "01"]
    encoded = encode_words(example)
    print()
    print("source:  10 0001 01")
    print("tokens: ", " | ".join(example))
    print("wire:   ", encoded)
    print("decoded:", " | ".join(decode_words(encoded)))
    print()
    print("PASS: arbitrary 1..8-bit words round-trip; all ordered pairs of")
    print("1..4-bit words round-trip; internal 00/01/10/11 never act as delimiters.")


if __name__ == "__main__":
    main()
