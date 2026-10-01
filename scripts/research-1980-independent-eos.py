#!/usr/bin/env python3
"""#1980 independent end-of-stream review.

Written from the public descriptions in #1971/#1980, without reading the
claimed research-1971-unique-decoding.py implementation.

Candidate A:
  widths 1..7: 3-bit header (width-1), then payload
  widths >=8:  111 + Elias-gamma(width-7), then payload

Candidate B:
  Elias-gamma(width), then payload

The bounded review enumerates every binary word of widths 1..4 and every
sequence of 0..3 words: 27,931 sequences total.
"""

from __future__ import annotations

from itertools import product


def gamma(n: int) -> str:
    assert n >= 1
    bits = f"{n:b}"
    return "0" * (len(bits) - 1) + bits


def gamma_read(bits: str, pos: int) -> tuple[int, int]:
    zeros = 0
    while pos + zeros < len(bits) and bits[pos + zeros] == "0":
        zeros += 1
    if pos + zeros >= len(bits):
        raise ValueError("truncated gamma")
    end = pos + 2 * zeros + 1
    if end > len(bits):
        raise ValueError("truncated gamma payload")
    return int(bits[pos + zeros : end], 2), end


def encode_a(words: tuple[str, ...]) -> str:
    out = []
    for word in words:
        width = len(word)
        if width <= 7:
            out.append(f"{width - 1:03b}")
        else:
            out.append("111")
            out.append(gamma(width - 7))
        out.append(word)
    return "".join(out)


def decode_a(bits: str) -> tuple[str, ...]:
    pos = 0
    out = []
    while pos < len(bits):
        if pos + 3 > len(bits):
            raise ValueError("truncated A header")
        header = int(bits[pos : pos + 3], 2)
        pos += 3
        if header < 7:
            width = header + 1
        else:
            extension, pos = gamma_read(bits, pos)
            width = 7 + extension
        if pos + width > len(bits):
            raise ValueError("truncated A payload")
        out.append(bits[pos : pos + width])
        pos += width
    return tuple(out)


def encode_b(words: tuple[str, ...]) -> str:
    return "".join(gamma(len(word)) + word for word in words)


def decode_b(bits: str) -> tuple[str, ...]:
    pos = 0
    out = []
    while pos < len(bits):
        width, pos = gamma_read(bits, pos)
        if pos + width > len(bits):
            raise ValueError("truncated B payload")
        out.append(bits[pos : pos + width])
        pos += width
    return tuple(out)


def zero_pad(bits: str) -> str:
    return bits + "0" * ((-len(bits)) % 8)


def stop_pad(bits: str) -> str:
    framed = bits + "1"
    return framed + "0" * ((-len(framed)) % 8)


def stop_unpad(bits: str) -> str:
    if len(bits) % 8:
        raise ValueError("not byte aligned")
    marker = bits.rfind("1")
    if marker < 0 or any(bit != "0" for bit in bits[marker + 1 :]):
        raise ValueError("invalid stop padding")
    return bits[:marker]


def length_pad(bits: str) -> str:
    # gamma(length+1) keeps the empty payload representable.
    framed = gamma(len(bits) + 1) + bits
    return framed + "0" * ((-len(framed)) % 8)


def length_unpad(bits: str) -> str:
    encoded_len, pos = gamma_read(bits, 0)
    payload_len = encoded_len - 1
    end = pos + payload_len
    if end > len(bits):
        raise ValueError("truncated length-framed payload")
    if any(bit != "0" for bit in bits[end:]):
        raise ValueError("non-zero byte padding")
    return bits[pos:end]


def corpus() -> list[tuple[str, ...]]:
    words = [
        "".join(bits)
        for width in range(1, 5)
        for bits in product("01", repeat=width)
    ]
    sequences: list[tuple[str, ...]] = [()]
    for size in range(1, 4):
        sequences.extend(product(words, repeat=size))
    return sequences


def strict_noncanonical_count(encode, decode) -> int:
    bad = 0
    for width in range(17):
        for bits_tuple in product("01", repeat=width):
            bits = "".join(bits_tuple)
            try:
                decoded = decode(bits)
            except ValueError:
                continue
            if encode(decoded) != bits:
                bad += 1
    return bad


def measure(name, encode, decode, sequences):
    raw_seen = {}
    padded_seen = {}
    roundtrip_fail = 0
    zero_misread = 0
    stop_misread = 0
    length_misread = 0

    for seq in sequences:
        raw = encode(seq)
        raw_seen.setdefault(raw, []).append(seq)

        try:
            if decode(raw) != seq:
                roundtrip_fail += 1
        except ValueError:
            roundtrip_fail += 1

        padded = zero_pad(raw)
        padded_seen.setdefault(padded, []).append(seq)
        try:
            if decode(padded) != seq:
                zero_misread += 1
        except ValueError:
            zero_misread += 1

        try:
            if decode(stop_unpad(stop_pad(raw))) != seq:
                stop_misread += 1
        except ValueError:
            stop_misread += 1

        try:
            if decode(length_unpad(length_pad(raw))) != seq:
                length_misread += 1
        except ValueError:
            length_misread += 1

    raw_collisions = sum(len(v) > 1 for v in raw_seen.values())
    padded_collisions = sum(len(v) > 1 for v in padded_seen.values())
    noncanonical = strict_noncanonical_count(encode, decode)

    print(name)
    print(f"  sequences={len(sequences)}")
    print(f"  roundtrip_fail={roundtrip_fail}")
    print(f"  raw_collisions={raw_collisions}")
    print(f"  strict_noncanonical_accepted={noncanonical}")
    print(f"  zero_padding_misread={zero_misread}")
    print(f"  zero_padding_shared_wires={padded_collisions}")
    print(f"  stop_bit_misread={stop_misread}")
    print(f"  gamma_length_prefix_misread={length_misread}")


def main() -> None:
    sequences = corpus()
    assert len(sequences) == 27931

    measure("A width3+escape", encode_a, decode_a, sequences)
    measure("B gamma-only", encode_b, decode_b, sequences)

    # racana2 words must remain ordinary payload words.
    racana = ("00", "01", "10", "11")
    assert decode_a(encode_a(racana)) == racana
    assert decode_b(encode_b(racana)) == racana

    print("RESULT: transport EOS metadata is independent of semantic word identity.")


if __name__ == "__main__":
    main()
