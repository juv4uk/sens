#!/usr/bin/env python3
"""#4261 current-authority binary-word witness.

Research/witness only. Semantic authority remains in lib/domains/d1.lisp..d9.lisp
and the active Contract. This script imports coordinates from those tables and
ports only representation-independent algorithms from #2077:

- exact bounded bit-sequence identity;
- width + bits, never numeric payload alone;
- prefix is a relation, not equality;
- external framing round-trip;
- semantic admission is independent from syntactic bit-word validity.

It deliberately contains no historical D3/D4 coordinate constants.
"""

from __future__ import annotations

# Поточне джерельне походження не можна засвідчити з вимкненими assert.
if not __debug__:
    raise SystemExit("CURRENT-AUTHORITY: BLOCKED — Python -O вимикає assert")

from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ROW_RE = re.compile(r"^\s*\(([01]+)\s+")
LISP_RE = re.compile(r"\(LISP\s+([^\s()]+|\(\))\)")


@dataclass(frozen=True, order=True)
class BinaryWord:
    bits: str

    def __post_init__(self) -> None:
        if not self.bits or any(ch not in "01" for ch in self.bits):
            raise ValueError("binary word must be a non-empty exact bit sequence")

    @property
    def width(self) -> int:
        return len(self.bits)

    def is_prefix_of(self, other: "BinaryWord") -> bool:
        return other.bits.startswith(self.bits)

    def packed_payload(self) -> bytes:
        size = (self.width + 7) // 8
        return int(self.bits, 2).to_bytes(size, "big")

    @staticmethod
    def from_packed(width: int, payload: bytes) -> "BinaryWord":
        if width <= 0:
            raise ValueError("width must be positive")
        expected = (width + 7) // 8
        if len(payload) != expected:
            raise ValueError("payload length does not match width")
        unused = expected * 8 - width
        if unused and (payload[0] >> (8 - unused)) != 0:
            raise ValueError("non-zero padding bits in canonical frame")
        return BinaryWord(f"{int.from_bytes(payload, 'big'):0{width}b}")


def encode_frame(word: BinaryWord) -> bytes:
    return word.width.to_bytes(4, "big") + word.packed_payload()


def decode_frame(data: bytes) -> BinaryWord:
    if len(data) < 4:
        raise ValueError("truncated frame")
    width = int.from_bytes(data[:4], "big")
    size = (width + 7) // 8
    if len(data) != 4 + size:
        raise ValueError("frame length mismatch")
    return BinaryWord.from_packed(width, data[4:])


def load_domain(width: int) -> tuple[list[BinaryWord], dict[str, BinaryWord]]:
    path = ROOT / "lib" / "domains" / f"d{width}.lisp"
    words: list[BinaryWord] = []
    by_lisp: dict[str, BinaryWord] = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        word = BinaryWord(match.group(1))
        assert word.width == width, (
            f"{path}: {word.bits} has width {word.width}, expected D{width}"
        )
        words.append(word)

        label_match = LISP_RE.search(line)
        if label_match:
            label = label_match.group(1)
            if label != "()":
                assert label not in by_lisp, f"{path}: duplicate LISP label {label}"
                by_lisp[label] = word

    assert words, f"{path}: no domain rows"
    assert len(words) == len(set(words)), f"{path}: duplicate exact binary keys"
    return words, by_lisp


def main() -> None:
    domains = {}
    lisp = {}
    for width in range(1, 10):
        domains[width], lisp[width] = load_domain(width)

    all_coordinates = []
    for width, words in domains.items():
        for word in words:
            assert decode_frame(encode_frame(word)) == word
            all_coordinates.append((width, word.bits))

    assert len(all_coordinates) == len(set(all_coordinates))

    by_payload = {}
    for width, words in domains.items():
        for word in words:
            by_payload.setdefault(int(word.bits, 2), []).append((width, word.bits))
    collisions = [
        rows for rows in by_payload.values()
        if len({width for width, _bits in rows}) > 1
    ]
    assert collisions, "current authority must expose a cross-width payload collision"
    for rows in collisions:
        identities = {(width, bits) for width, bits in rows}
        assert len(identities) == len(rows)

    car = lisp[3]["CAR"]
    cdr = lisp[3]["CDR"]
    caar = lisp[4]["CAAR"]
    cadr = lisp[4]["CADR"]
    cdar = lisp[4]["CDAR"]
    cddr = lisp[4]["CDDR"]

    assert car.is_prefix_of(caar) and caar.bits == car.bits + "0"
    assert car.is_prefix_of(cadr) and cadr.bits == car.bits + "1"
    assert cdr.is_prefix_of(cdar) and cdar.bits == cdr.bits + "0"
    assert cdr.is_prefix_of(cddr) and cddr.bits == cdr.bits + "1"
    assert len({caar, cadr, cdar, cddr}) == 4

    admitted_d7 = {word.bits for word in domains[7]}
    syntactic_d7 = {f"{value:07b}" for value in range(1 << 7)}
    d7_holes = sorted(syntactic_d7 - admitted_d7)
    assert d7_holes, "D7 witness expects current authority to retain reserved holes"
    assert admitted_d7.isdisjoint(d7_holes)

    assert domains[8]
    assert domains[9]

    print("CURRENT-AUTHORITY binary-word witness: PASS")
    print("domain-row-counts:", " ".join(
        f"D{width}={len(domains[width])}" for width in range(1, 10)
    ))
    print(f"cross-width numeric-payload collisions: {len(collisions)}")
    print("selector roots from authority:", f"CAR={car.bits}", f"CDR={cdr.bits}")
    print(
        "D4 selector descendants from authority:",
        f"CAAR={caar.bits}",
        f"CADR={cadr.bits}",
        f"CDAR={cdar.bits}",
        f"CDDR={cddr.bits}",
    )
    print("D7 reserved holes derived from authority:", " ".join(d7_holes))
    print("exact-width frame round-trip: PASS")
    print("prefix-without-identity-collapse: PASS")
    print("numeric-payload-collapse rejected: PASS")
    print("NON-CONCLUSION: framing format is witness-only")
    print("NON-CONCLUSION: D8/D9 residency does not grant callability")
    print("NON-CONCLUSION: no coordinate is ratified by this script")


if __name__ == "__main__":
    main()
