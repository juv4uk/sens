#!/usr/bin/env python3
"""Independent #1980 review of two variable-width wire envelopes.

This implementation was written from the public issue description, not copied
from the coordinator's research script. It tests:
- raw round-trip and injectivity;
- strict canonical decoding of all bit strings up to 16 bits;
- plain zero-padding failure modes;
- stop-bit and outer gamma-length envelopes.

Research-only. No SENS semantic authority is defined here.
"""

from __future__ import annotations

from itertools import product


def gamma_positive(value: int) -> str:
    if value < 1:
        raise ValueError("gamma code requires a positive integer")
    bits = f"{value:b}"
    return "0" * (len(bits) - 1) + bits


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


def width3_header(width: int) -> str:
    if width < 1:
        raise ValueError("width must be positive")
    if width <= 7:
        return f"{width - 1:03b}"
    return "111" + gamma_positive(width - 7)


def encode_a(words: list[str]) -> str:
    return "".join(width3_header(len(word)) + word for word in words)


def decode_a(bits: str) -> list[str]:
    pos = 0
    out: list[str] = []
    while pos < len(bits):
        if pos + 3 > len(bits):
            raise ValueError("truncated width3 header")
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


def encode_b(words: list[str]) -> str:
    return "".join(gamma_positive(len(word)) + word for word in words)


def decode_b(bits: str) -> list[str]:
    pos = 0
    out: list[str] = []
    while pos < len(bits):
        width, pos = read_gamma(bits, pos)
        end = pos + width
        if end > len(bits):
            raise ValueError("truncated semantic word")
        out.append(bits[pos:end])
        pos = end
    return out


def words_upto(width: int) -> list[str]:
    out: list[str] = []
    for n in range(1, width + 1):
        out.extend("".join(p) for p in product("01", repeat=n))
    return out


def sequences_upto(words: list[str], count: int) -> list[list[str]]:
    out: list[list[str]] = [[]]
    for n in range(1, count + 1):
        out.extend([list(p) for p in product(words, repeat=n)])
    return out


def pad_zero(raw: str) -> str:
    return raw + "0" * ((-len(raw)) % 8)


def pack_stop(raw: str) -> str:
    marked = raw + "1"
    return marked + "0" * ((-len(marked)) % 8)


def unpack_stop(packed: str) -> str:
    marker = packed.rfind("1")
    if marker < 0:
        raise ValueError("missing stop marker")
    if any(bit != "0" for bit in packed[marker + 1 :]):
        raise ValueError("non-zero padding after marker")
    return packed[:marker]


def pack_length(raw: str) -> str:
    body = gamma_positive(len(raw) + 1) + raw
    return body + "0" * ((-len(body)) % 8)


def unpack_length(packed: str) -> str:
    encoded_len, pos = read_gamma(packed, 0)
    raw_len = encoded_len - 1
    end = pos + raw_len
    if end > len(packed):
        raise ValueError("truncated framed payload")
    if any(bit != "0" for bit in packed[end:]):
        raise ValueError("non-zero outer padding")
    return packed[pos:end]


def raw_stats(sequences, encode, decode):
    wires: dict[str, list[tuple[str, ...]]] = {}
    failures = 0
    for seq in sequences:
        wire = encode(seq)
        wires.setdefault(wire, []).append(tuple(seq))
        try:
            if decode(wire) != seq:
                failures += 1
        except ValueError:
            failures += 1
    collisions = sum(1 for values in wires.values() if len(values) > 1)
    return failures, collisions


def strict_stats(encode, decode, max_bits: int = 16):
    accepted = 0
    noncanonical = 0
    for width in range(max_bits + 1):
        for bits_tuple in product("01", repeat=width):
            bits = "".join(bits_tuple)
            try:
                seq = decode(bits)
            except ValueError:
                continue
            accepted += 1
            if encode(seq) != bits:
                noncanonical += 1
    return accepted, noncanonical


def zero_padding_stats(sequences, encode, decode):
    wires: dict[str, list[tuple[str, ...]]] = {}
    misreads = 0
    for seq in sequences:
        packed = pad_zero(encode(seq))
        wires.setdefault(packed, []).append(tuple(seq))
        try:
            if decode(packed) != seq:
                misreads += 1
        except ValueError:
            misreads += 1
    collisions = sum(1 for values in wires.values() if len(values) > 1)
    return misreads, collisions


def envelope_misreads(sequences, encode, decode, pack, unpack):
    failures = 0
    for seq in sequences:
        packed = pack(encode(seq))
        try:
            raw = unpack(packed)
            if decode(raw) != seq:
                failures += 1
        except ValueError:
            failures += 1
    return failures


def check(name, encode, decode, sequences):
    raw_fail, raw_collisions = raw_stats(sequences, encode, decode)
    accepted, noncanonical = strict_stats(encode, decode)
    zero_misread, zero_collisions = zero_padding_stats(sequences, encode, decode)
    stop_misread = envelope_misreads(sequences, encode, decode, pack_stop, unpack_stop)
    length_misread = envelope_misreads(sequences, encode, decode, pack_length, unpack_length)

    return {
        "candidate": name,
        "sequences": len(sequences),
        "raw_failures": raw_fail,
        "raw_collisions": raw_collisions,
        "strict_accepted_upto16": accepted,
        "strict_noncanonical": noncanonical,
        "zero_padding_misreads": zero_misread,
        "zero_padding_collisions": zero_collisions,
        "stop_bit_misreads": stop_misread,
        "gamma_length_misreads": length_misread,
    }


def main() -> None:
    words = words_upto(4)
    sequences = sequences_upto(words, 3)
    assert len(words) == 30
    assert len(sequences) == 27931

    results = [
        check("A-width3+escape", encode_a, decode_a, sequences),
        check("B-gamma-width", encode_b, decode_b, sequences),
    ]

    expected = {
        "A-width3+escape": (26390, 386),
        "B-gamma-width": (20602, 0),
    }

    fields = tuple(results[0])
    print("\t".join(fields))
    for row in results:
        print("\t".join(str(row[field]) for field in fields))
        assert row["raw_failures"] == 0
        assert row["raw_collisions"] == 0
        assert row["strict_noncanonical"] == 0
        assert (row["zero_padding_misreads"], row["zero_padding_collisions"]) == expected[row["candidate"]]
        assert row["stop_bit_misreads"] == 0
        assert row["gamma_length_misreads"] == 0

    # Concrete A collision from the independent implementation.
    assert pad_zero(encode_a(["0"])) == pad_zero(encode_a(["0", "0"])) == "00000000"

    print()
    print("PASS: independent implementation reproduces the #1980 zero-padding failure counts.")
    print("PASS: raw A/B envelopes are injective on the bounded corpus.")
    print("PASS: stop-bit and outer gamma-length envelopes have zero bounded misreads.")


if __name__ == "__main__":
    main()
