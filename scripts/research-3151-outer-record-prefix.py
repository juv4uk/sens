#!/usr/bin/env python3
"""#3151 — research-only outer record prefix witness.

This file tests transport framing only. Prefixes below are NOT SENS semantic
identities. They live outside the exact semantic payload:

    0      D1..D8 word, then 3 bits width-1, then exact payload
    10     BinaryNumber, then gamma0(width), then normalized bits
    110    Local(depth,index), then gamma0(depth), gamma0(index)
    1110   Sound7, then gamma0(cell count), then 7*N payload bits
    1111   reserved

Message end is supplied by an outer exact meaningful-bit length. D2 payload
11 therefore remains dot; it is never an escape.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable


def gamma(value: int) -> str:
    if value < 1:
        raise ValueError("gamma needs positive integer")
    bits = f"{value:b}"
    return "0" * (len(bits) - 1) + bits


def gamma0(value: int) -> str:
    if value < 0:
        raise ValueError("gamma0 needs non-negative integer")
    return gamma(value + 1)


def read_gamma0(bits: str, pos: int) -> tuple[int, int]:
    zeros = 0
    while pos < len(bits) and bits[pos] == "0":
        zeros += 1
        pos += 1
    if pos >= len(bits):
        raise ValueError("truncated gamma0")
    end = pos + zeros + 1
    if end > len(bits):
        raise ValueError("truncated gamma0")
    return int(bits[pos:end], 2) - 1, end


@dataclass(frozen=True)
class Domain:
    width: int
    bits: int


@dataclass(frozen=True)
class Number:
    bits: str


@dataclass(frozen=True)
class Local:
    depth: int
    index: int


@dataclass(frozen=True)
class Sound:
    cells: tuple[int, ...]


Record = Domain | Number | Local | Sound


def encode_record(record: Record) -> str:
    if isinstance(record, Domain):
        if not 1 <= record.width <= 8:
            raise ValueError("domain width outside 1..8")
        if not 0 <= record.bits < (1 << record.width):
            raise ValueError("domain payload outside width")
        return (
            "0"
            + f"{record.width - 1:03b}"
            + f"{record.bits:0{record.width}b}"
        )

    if isinstance(record, Number):
        payload = record.bits
        if not payload or set(payload) - {"0", "1"}:
            raise ValueError("Number payload is not binary")
        if len(payload) > 1 and payload[0] == "0":
            raise ValueError("Number has non-canonical leading zero")
        return "10" + gamma0(len(payload)) + payload

    if isinstance(record, Local):
        if record.depth < 0 or record.index < 0:
            raise ValueError("negative lexical coordinate")
        return "110" + gamma0(record.depth) + gamma0(record.index)

    if isinstance(record, Sound):
        if any(not 0 <= cell < 128 for cell in record.cells):
            raise ValueError("Sound7 cell outside 7 bits")
        payload = "".join(f"{cell:07b}" for cell in record.cells)
        return "1110" + gamma0(len(record.cells)) + payload

    raise TypeError(record)


def decode_one(bits: str, pos: int) -> tuple[Record, int]:
    if pos >= len(bits):
        raise ValueError("unexpected end")

    if bits[pos] == "0":
        pos += 1
        if pos + 3 > len(bits):
            raise ValueError("truncated domain header")
        width = int(bits[pos : pos + 3], 2) + 1
        pos += 3
        end = pos + width
        if end > len(bits):
            raise ValueError("truncated domain payload")
        return Domain(width, int(bits[pos:end], 2)), end

    if bits.startswith("10", pos):
        pos += 2
        width, pos = read_gamma0(bits, pos)
        if width < 1:
            raise ValueError("zero-width Number")
        end = pos + width
        if end > len(bits):
            raise ValueError("truncated Number")
        payload = bits[pos:end]
        if width > 1 and payload[0] == "0":
            raise ValueError("non-canonical Number")
        return Number(payload), end

    if bits.startswith("110", pos):
        pos += 3
        depth, pos = read_gamma0(bits, pos)
        index, pos = read_gamma0(bits, pos)
        return Local(depth, index), pos

    if bits.startswith("1110", pos):
        pos += 4
        count, pos = read_gamma0(bits, pos)
        end = pos + 7 * count
        if end > len(bits):
            raise ValueError("truncated Sound7")
        cells = tuple(
            int(bits[offset : offset + 7], 2)
            for offset in range(pos, end, 7)
        )
        return Sound(cells), end

    if bits.startswith("1111", pos):
        raise ValueError("reserved outer extension")

    raise ValueError("truncated outer prefix")


def encode_program(records: Iterable[Record]) -> str:
    return "".join(encode_record(record) for record in records)


def decode_program(bits: str) -> tuple[Record, ...]:
    if set(bits) - {"0", "1"}:
        raise ValueError("wire contains non-bit")
    pos = 0
    out: list[Record] = []
    while pos < len(bits):
        record, pos = decode_one(bits, pos)
        out.append(record)
    if encode_program(out) != bits:
        raise ValueError("non-canonical wire")
    return tuple(out)


def canonical_numbers(max_width: int) -> list[Number]:
    out = [Number("0"), Number("1")]
    for width in range(2, max_width + 1):
        out.extend(
            Number("1" + f"{tail:0{width - 1}b}")
            for tail in range(1 << (width - 1))
        )
    return out


def all_domain_words(max_width: int) -> list[Domain]:
    return [
        Domain(width, value)
        for width in range(1, max_width + 1)
        for value in range(1 << width)
    ]


def pack_with_meaningful_length(bits: str) -> tuple[bytes, int]:
    if not bits:
        return b"", 0
    padding = (-len(bits)) % 8
    padded = bits + "0" * padding
    data = bytes(int(padded[offset : offset + 8], 2) for offset in range(0, len(padded), 8))
    return data, len(bits)


def unpack_with_meaningful_length(data: bytes, bit_len: int) -> str:
    if bit_len < 0 or bit_len > 8 * len(data):
        raise ValueError("invalid meaningful-bit length")
    all_bits = "".join(f"{byte:08b}" for byte in data)
    payload, tail = all_bits[:bit_len], all_bits[bit_len:]
    if set(tail) - {"0"}:
        raise ValueError("non-zero physical tail")
    return payload


def donor_width3_cost(width: int) -> int:
    header = 3 if width <= 7 else 3 + len(gamma(width - 7))
    return header + width


def gamma_width_cost(width: int) -> int:
    return len(gamma(width)) + width


def candidate_domain_cost(width: int) -> int:
    return 4 + width


def assert_single_roundtrips() -> int:
    records: list[Record] = []
    records.extend(all_domain_words(8))
    records.extend(canonical_numbers(8))
    records.extend(Local(depth, index) for depth in range(3) for index in range(3))
    records.append(Sound(()))
    records.extend(Sound((cell,)) for cell in range(128))

    assert len(records) == 904
    assert len(set(records)) == 904

    for record in records:
        wire = encode_record(record)
        assert decode_program(wire) == (record,)
    return len(records)


def assert_bounded_sequence_injectivity() -> int:
    records: list[Record] = []
    records.extend(all_domain_words(4))
    records.extend(canonical_numbers(4))
    records.extend(Local(depth, index) for depth in range(3) for index in range(3))
    records.append(Sound(()))
    records.extend(Sound((cell,)) for cell in range(128))

    assert len(records) == 184

    seen: dict[str, tuple[Record, ...]] = {}
    checked = 0
    for length in (1, 2):
        for sequence in product(records, repeat=length):
            checked += 1
            wire = encode_program(sequence)
            assert decode_program(wire) == sequence
            previous = seen.setdefault(wire, sequence)
            assert previous == sequence, (previous, sequence, wire)

    assert checked == 34040
    assert len(seen) == checked
    return checked


def assert_boundary_and_anti_collapse() -> None:
    assert encode_record(Domain(2, 0b11)) != encode_record(Number("11"))
    assert decode_program(encode_record(Domain(2, 0b11))) == (Domain(2, 0b11),)

    assert encode_record(Domain(1, 1)) != encode_record(Number("1"))
    assert encode_record(Domain(3, 0b001)) != encode_record(Domain(4, 0b0001))

    for sequence in [
        (Domain(2, 0b00),),
        (Domain(3, 0b000),),
        (Number("0"),),
        (Domain(2, 0b10), Domain(3, 0b001), Domain(2, 0b01)),
    ]:
        wire = encode_program(sequence)
        data, bit_len = pack_with_meaningful_length(wire)
        exact = unpack_with_meaningful_length(data, bit_len)
        assert exact == wire
        assert decode_program(exact) == sequence


def assert_malformed_rejected() -> None:
    bad = [
        "0",          # truncated domain header
        "0000",       # header says D1, missing payload
        "10",         # Number length missing
        "100",        # truncated gamma0
        "110",        # Local coordinates missing
        "1110",       # Sound count missing
        "1111",       # reserved extension
    ]
    for bits in bad:
        try:
            decode_program(bits)
        except ValueError:
            pass
        else:
            raise AssertionError(f"malformed wire accepted: {bits}")

    noncanonical_two = "10" + gamma0(2) + "01"
    try:
        decode_program(noncanonical_two)
    except ValueError:
        pass
    else:
        raise AssertionError("leading-zero Number accepted")




# Candidate S: extend the proven Width3 tree rather than prepend a class bit.
#
# 000..110 -> D1..D7
# 1110     -> D8
# 11110    -> BinaryNumber
# 111110   -> Local
# 1111110  -> Sound7
# 1111111  -> reserved
#
# This preserves the donor Width3+escape header cost for every D1..D8 word.

def encode_record_s(record: Record) -> str:
    if isinstance(record, Domain):
        if not 1 <= record.width <= 8:
            raise ValueError("domain width outside 1..8")
        if not 0 <= record.bits < (1 << record.width):
            raise ValueError("domain payload outside width")
        prefix = f"{record.width - 1:03b}" if record.width <= 7 else "1110"
        return prefix + f"{record.bits:0{record.width}b}"

    if isinstance(record, Number):
        payload = record.bits
        if not payload or set(payload) - {"0", "1"}:
            raise ValueError("Number payload is not binary")
        if len(payload) > 1 and payload[0] == "0":
            raise ValueError("Number has non-canonical leading zero")
        return "11110" + gamma0(len(payload)) + payload

    if isinstance(record, Local):
        if record.depth < 0 or record.index < 0:
            raise ValueError("negative lexical coordinate")
        return "111110" + gamma0(record.depth) + gamma0(record.index)

    if isinstance(record, Sound):
        if any(not 0 <= cell < 128 for cell in record.cells):
            raise ValueError("Sound7 cell outside 7 bits")
        payload = "".join(f"{cell:07b}" for cell in record.cells)
        return "1111110" + gamma0(len(record.cells)) + payload

    raise TypeError(record)


def decode_one_s(bits: str, pos: int) -> tuple[Record, int]:
    if pos + 3 > len(bits):
        raise ValueError("truncated candidate-S prefix")

    head = bits[pos:pos + 3]
    raw = int(head, 2)
    pos += 3

    if raw < 7:
        width = raw + 1
        end = pos + width
        if end > len(bits):
            raise ValueError("truncated domain payload")
        return Domain(width, int(bits[pos:end], 2)), end

    if pos >= len(bits):
        raise ValueError("truncated candidate-S extension")
    if bits[pos] == "0":
        pos += 1
        width = 8
        end = pos + width
        if end > len(bits):
            raise ValueError("truncated D8 payload")
        return Domain(width, int(bits[pos:end], 2)), end

    pos += 1
    if pos >= len(bits):
        raise ValueError("truncated candidate-S extension")
    if bits[pos] == "0":
        pos += 1
        width, pos = read_gamma0(bits, pos)
        if width < 1:
            raise ValueError("zero-width Number")
        end = pos + width
        if end > len(bits):
            raise ValueError("truncated Number")
        payload = bits[pos:end]
        if width > 1 and payload[0] == "0":
            raise ValueError("non-canonical Number")
        return Number(payload), end

    pos += 1
    if pos >= len(bits):
        raise ValueError("truncated candidate-S extension")
    if bits[pos] == "0":
        pos += 1
        depth, pos = read_gamma0(bits, pos)
        index, pos = read_gamma0(bits, pos)
        return Local(depth, index), pos

    pos += 1
    if pos >= len(bits):
        raise ValueError("truncated candidate-S extension")
    if bits[pos] == "0":
        pos += 1
        count, pos = read_gamma0(bits, pos)
        end = pos + 7 * count
        if end > len(bits):
            raise ValueError("truncated Sound7")
        cells = tuple(
            int(bits[offset:offset + 7], 2)
            for offset in range(pos, end, 7)
        )
        return Sound(cells), end

    raise ValueError("reserved candidate-S extension")


def encode_program_s(records: Iterable[Record]) -> str:
    return "".join(encode_record_s(record) for record in records)


def decode_program_s(bits: str) -> tuple[Record, ...]:
    if set(bits) - {"0", "1"}:
        raise ValueError("wire contains non-bit")
    pos = 0
    out: list[Record] = []
    while pos < len(bits):
        record, pos = decode_one_s(bits, pos)
        out.append(record)
    if encode_program_s(out) != bits:
        raise ValueError("non-canonical candidate-S wire")
    return tuple(out)


def candidate_s_domain_cost(width: int) -> int:
    return width + (3 if width <= 7 else 4)


def assert_candidate_s() -> tuple[int, int]:
    records: list[Record] = []
    records.extend(all_domain_words(8))
    records.extend(canonical_numbers(8))
    records.extend(Local(depth, index) for depth in range(3) for index in range(3))
    records.append(Sound(()))
    records.extend(Sound((cell,)) for cell in range(128))
    assert len(records) == 904

    for record in records:
        wire = encode_record_s(record)
        assert decode_program_s(wire) == (record,)

    bounded: list[Record] = []
    bounded.extend(all_domain_words(4))
    bounded.extend(canonical_numbers(4))
    bounded.extend(Local(depth, index) for depth in range(3) for index in range(3))
    bounded.append(Sound(()))
    bounded.extend(Sound((cell,)) for cell in range(128))
    assert len(bounded) == 184

    seen: dict[str, tuple[Record, ...]] = {}
    checked = 0
    for length in (1, 2):
        for sequence in product(bounded, repeat=length):
            checked += 1
            wire = encode_program_s(sequence)
            assert decode_program_s(wire) == sequence
            previous = seen.setdefault(wire, sequence)
            assert previous == sequence, (previous, sequence, wire)
    assert checked == 34040
    assert len(seen) == checked

    assert encode_record_s(Domain(2, 0b11)) != encode_record_s(Number("11"))
    assert decode_program_s(encode_record_s(Domain(2, 0b11))) == (Domain(2, 0b11),)
    assert encode_record_s(Domain(1, 1)) != encode_record_s(Number("1"))
    assert encode_record_s(Domain(3, 1)) != encode_record_s(Domain(4, 1))

    for width in range(1, 9):
        assert candidate_s_domain_cost(width) == donor_width3_cost(width)

    for bad in ["111", "1111", "11110", "111110", "1111110", "1111111"]:
        try:
            decode_program_s(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"candidate S accepted malformed wire: {bad}")

    noncanonical_two = "11110" + gamma0(2) + "01"
    try:
        decode_program_s(noncanonical_two)
    except ValueError:
        pass
    else:
        raise AssertionError("candidate S accepted leading-zero Number")

    return len(records), checked

def main() -> int:
    singles = assert_single_roundtrips()
    sequences = assert_bounded_sequence_injectivity()
    assert_boundary_and_anti_collapse()
    assert_malformed_rejected()
    s_singles, s_sequences = assert_candidate_s()

    print("#3151 outer-record-prefix witness")
    print(f"single_records={singles} roundtrip_failures=0")
    print(f"bounded_sequences={sequences} collisions=0 roundtrip_failures=0")
    print("d2_dot_preserved=true")
    print("domain_number_anti_collapse=true")
    print("meaningful_bit_length_tail_roundtrip=true")
    print("malformed_fail_closed=true")
    print(f"candidate_s_single_records={s_singles} roundtrip_failures=0")
    print(f"candidate_s_bounded_sequences={s_sequences} collisions=0 roundtrip_failures=0")
    print("candidate_s_preserves_donor_D1_D8_cost=true")
    print()
    print("width donor_width3 gamma_only candidate_R candidate_S")
    for width in range(1, 9):
        print(
            width,
            donor_width3_cost(width),
            gamma_width_cost(width),
            candidate_domain_cost(width),
            candidate_s_domain_cost(width),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
