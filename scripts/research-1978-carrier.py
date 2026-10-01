#!/usr/bin/env python3
"""#1978 research-only carrier witness.

Compares two abstract host representations for an exact bounded binary word.
This is not runtime code and does not ratify a variable-width ontology.
"""

from __future__ import annotations

from dataclasses import dataclass


def _parse_bits(text: str) -> tuple[int, int]:
    if not text or any(ch not in "01" for ch in text):
        raise ValueError(f"not a non-empty binary word: {text!r}")
    return len(text), int(text, 2)


@dataclass(frozen=True)
class Inline64:
    """Candidate A: explicit width + u64-like payload. Bounded to 64 bits."""

    width: int
    bits: int

    @classmethod
    def parse(cls, text: str) -> "Inline64":
        width, bits = _parse_bits(text)
        if width > 64:
            raise OverflowError("Inline64 imposes a 64-bit semantic ceiling")
        return cls(width, bits)

    def render(self) -> str:
        return format(self.bits, f"0{self.width}b")

    def append(self, bit: int) -> "Inline64":
        if bit not in (0, 1):
            raise ValueError("bit must be 0 or 1")
        if self.width == 64:
            raise OverflowError("Inline64 cannot append beyond 64 bits")
        return Inline64(self.width + 1, (self.bits << 1) | bit)

    def parent(self) -> "Inline64 | None":
        if self.width == 1:
            return None
        return Inline64(self.width - 1, self.bits >> 1)

    def is_prefix_of(self, other: "Inline64") -> bool:
        return self.width <= other.width and self.bits == (
            other.bits >> (other.width - self.width)
        )

    def sens8_projection(self) -> int | None:
        return self.bits if self.width == 8 else None

    def logical_payload_bytes(self) -> int:
        # Abstract field bytes only: u8 width + u64 payload. Rust padding excluded.
        return 9


@dataclass(frozen=True)
class BitBytes:
    """Candidate B: explicit bit length + minimal immutable big-endian bytes."""

    width: int
    payload: bytes

    @classmethod
    def parse(cls, text: str) -> "BitBytes":
        width, bits = _parse_bits(text)
        nbytes = (width + 7) // 8
        return cls(width, bits.to_bytes(nbytes, "big"))

    def __post_init__(self) -> None:
        if self.width < 1:
            raise ValueError("width must be positive")
        expected = (self.width + 7) // 8
        if len(self.payload) != expected:
            raise ValueError("payload length does not match bit width")
        unused = expected * 8 - self.width
        if unused and (self.payload[0] >> (8 - unused)) != 0:
            raise ValueError("unused high bits must be zero")

    def _integer(self) -> int:
        return int.from_bytes(self.payload, "big")

    def render(self) -> str:
        return format(self._integer(), f"0{self.width}b")

    def append(self, bit: int) -> "BitBytes":
        if bit not in (0, 1):
            raise ValueError("bit must be 0 or 1")
        return BitBytes.parse(self.render() + str(bit))

    def parent(self) -> "BitBytes | None":
        if self.width == 1:
            return None
        return BitBytes.parse(self.render()[:-1])

    def is_prefix_of(self, other: "BitBytes") -> bool:
        return other.render().startswith(self.render())

    def sens8_projection(self) -> int | None:
        return self._integer() if self.width == 8 else None

    def logical_payload_bytes(self) -> int:
        # Abstract payload only: u32-like explicit bit length + minimal bytes.
        return 4 + len(self.payload)


FIXTURES = [
    "000", "001", "010", "011", "100", "101", "110", "111",
    "1010", "1011", "101111",
]


def check_candidate(factory, name: str) -> None:
    words = {text: factory.parse(text) for text in FIXTURES}
    for text, word in words.items():
        assert word.render() == text, (name, text, word.render())
    assert words["001"] != factory.parse("00000001")
    assert words["101"].is_prefix_of(words["1011"])
    assert words["1011"].parent() == words["101"]
    assert words["101"].append(1) == words["1011"]
    assert factory.parse("00000001").sens8_projection() == 1
    assert words["001"].sens8_projection() is None


def exhaustive_small_domain() -> int:
    checked = 0
    for width in range(1, 13):
        for value in range(1 << width):
            text = format(value, f"0{width}b")
            a = Inline64.parse(text)
            b = BitBytes.parse(text)
            assert a.render() == text == b.render()
            assert a.sens8_projection() == b.sens8_projection()
            for bit in (0, 1):
                aa = a.append(bit)
                bb = b.append(bit)
                assert aa.render() == text + str(bit) == bb.render()
                assert a.is_prefix_of(aa)
                assert b.is_prefix_of(bb)
                assert aa.parent() == a
                assert bb.parent() == b
            checked += 1
    return checked


def main() -> None:
    check_candidate(Inline64, "Inline64")
    check_candidate(BitBytes, "BitBytes")
    checked = exhaustive_small_domain()

    limit = Inline64.parse("1" * 64)
    try:
        limit.append(0)
    except OverflowError:
        inline_ceiling_falsified = True
    else:
        inline_ceiling_falsified = False
    assert inline_ceiling_falsified

    long_word = BitBytes.parse("0" * 79 + "1")
    assert long_word.width == 80
    assert long_word.render() == "0" * 79 + "1"

    print(f"exhaustive words checked (widths 1..12): {checked}")
    print("fixture law: 001 != 00000001")
    print("fixture law: 101 prefix-of 1011")
    print("fixture law: parent(1011) = 101")
    print("fixture law: append(101,1) = 1011")
    print("fixture law: Sens8 projection succeeds iff width == 8")
    print()
    print("candidate\tunbounded\tshort-word logical payload\tappend beyond 64\tverdict")
    print(f"Inline64\tno\t{Inline64.parse('001').logical_payload_bytes()}\tno\tbounded fast representation only")
    print(f"BitBytes\tyes\t{BitBytes.parse('001').logical_payload_bytes()}\tyes\tuniversal but variable storage/copy cost")
    print()
    print("RESULT: both candidates preserve exact width/bits on the tested laws.")
    print("RESULT: Inline64 is falsified as a universal carrier by its 64-bit ceiling.")
    print("RESULT: BitBytes is universal in this model but pays variable storage/copy cost.")
    print("RECOMMENDATION: insufficient evidence for a production carrier; prototype a small-inline+spill hybrid next.")
    print("PRODUCTION IMPACT: none.")


if __name__ == "__main__":
    main()
