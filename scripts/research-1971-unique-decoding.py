#!/usr/bin/env python3
"""#1971: executable unique decodability for variable-width word transports.  Research-only.

Words are already-bounded binary words (racanā2, bīja3, longer ones): a word is (width, bits), `001` and
`0010` differ. A transport turns a sequence of words into a raw bitstream. Nothing here changes any
semantic identity; it only measures whether a wire can be read back uniquely.

Candidates (outer envelopes only):
  A  Width3 + escape      3-bit header for widths 1..7, `111` + gamma(width-7) beyond (the #1962 witness)
  B  gamma-only           header = Elias gamma of the width (no special short case)

Checks (each can fail; failures are reported, not hidden):
  1  every sequence of up to K words (widths 1..W) round-trips, and no two sequences share a wire
  2  strict decoding: if the decoder accepts a wire, re-encoding the result gives the same bits
  3  END OF STREAM: a wire is packed into bytes, so zero bits follow the last word.  Plain padding is
     compared with two ways to mark the end (stop-bit padding, and a gamma length prefix)
  4  full wire cost A vs B on the same word-width profile
  5  the racanā2 words 00 01 10 11 (including `11`, the dot) are ordinary words and survive
"""

from __future__ import annotations

import itertools
import sys
from typing import Callable, List, Optional, Sequence, Tuple

Word = str
Wire = str


# ---------------------------------------------------------------- primitives
def gamma(value: int) -> str:
    if value < 1:
        raise ValueError("gamma needs a positive integer")
    bits = f"{value:b}"
    return "0" * (len(bits) - 1) + bits


def read_gamma(bits: str, pos: int) -> Tuple[int, int]:
    zeros = 0
    while pos < len(bits) and bits[pos] == "0":
        zeros += 1
        pos += 1
    end = pos + zeros + 1
    if pos >= len(bits) or end > len(bits):
        raise ValueError("truncated gamma")
    return int(bits[pos:end], 2), end


def check_word(word: str) -> None:
    if not word or set(word) - {"0", "1"}:
        raise ValueError(f"not a binary word: {word!r}")


# ------------------------------------------------------------ candidate A, B
def header_a(width: int) -> str:
    if width <= 7:
        return f"{width - 1:03b}"
    return "111" + gamma(width - 7)


def read_header_a(bits: str, pos: int) -> Tuple[int, int]:
    if pos + 3 > len(bits):
        raise ValueError("truncated header")
    raw = int(bits[pos:pos + 3], 2)
    pos += 3
    if raw < 7:
        return raw + 1, pos
    extra, pos = read_gamma(bits, pos)
    return extra + 7, pos


def header_b(width: int) -> str:
    return gamma(width)


def read_header_b(bits: str, pos: int) -> Tuple[int, int]:
    return read_gamma(bits, pos)


class Envelope:
    def __init__(self, name: str, header: Callable[[int], str], read: Callable[[str, int], Tuple[int, int]]):
        self.name, self.header, self.read = name, header, read

    def encode(self, words: Sequence[Word]) -> Wire:
        out = []
        for word in words:
            check_word(word)
            out.append(self.header(len(word)))
            out.append(word)
        return "".join(out)

    def decode(self, wire: Wire, *, strict: bool = True, lazy: bool = False) -> List[Word]:
        """Read words until the wire is exhausted; a partial word raises. `strict` also demands canonical form.

        `lazy`: an INCOMPLETE tail that is only zero bits is taken as padding and ignored (the receiver of a
        zero-padded byte stream). A tail that completes a word is a word, even if it is all zeros.
        """
        if set(wire) - {"0", "1"}:
            raise ValueError("wire must be bits")
        pos, out = 0, []
        while pos < len(wire):
            try:
                width, after = self.read(wire, pos)
                end = after + width
                if end > len(wire):
                    raise ValueError("truncated word")
            except ValueError:
                if lazy and set(wire[pos:]) <= {"0"}:
                    break
                raise
            out.append(wire[after:end])
            pos = end
        if strict and not lazy and self.encode(out) != wire:
            raise ValueError("not the canonical wire of its words")
        return out


A = Envelope("A width3+escape", header_a, read_header_a)
B = Envelope("B gamma-only", header_b, read_header_b)


# ------------------------------------------------------------- end of stream
def pad_zero(wire: Wire) -> Wire:
    """Plain byte padding: zeros up to a multiple of 8 (the naive packing)."""
    return wire + "0" * (-len(wire) % 8)


def pad_stop(wire: Wire) -> Wire:
    """Stop-bit padding: a `1`, then zeros to the byte boundary (always at least the `1`)."""
    wire = wire + "1"
    return wire + "0" * (-len(wire) % 8)


def unpad_stop(packed: Wire) -> Wire:
    stripped = packed.rstrip("0")
    if not stripped or not stripped.endswith("1") or len(packed) % 8 or len(packed) - len(stripped) > 7:
        raise ValueError("no valid stop bit")
    return stripped[:-1]


def pack_length(env: Envelope, words: Sequence[Word]) -> Wire:
    """A gamma length prefix (number of wire bits + 1), then the wire, then zero padding."""
    wire = env.encode(words)
    return pad_zero(gamma(len(wire) + 1) + wire)


def unpack_length(env: Envelope, packed: Wire) -> List[Word]:
    n_plus_1, pos = read_gamma(packed, 0)
    n = n_plus_1 - 1
    wire, rest = packed[pos:pos + n], packed[pos + n:]
    if len(wire) != n or set(rest) - {"0"} or len(rest) > 7:
        raise ValueError("bad length-prefixed packing")
    return env.decode(wire)


# -------------------------------------------------------------------- checks
def all_words(max_width: int) -> List[Word]:
    return [f"{n:0{w}b}" for w in range(1, max_width + 1) for n in range(1 << w)]


def check_injective_roundtrip(env: Envelope, max_width: int, max_len: int) -> Tuple[int, int]:
    """(sequences checked, failures): round trip + no two sequences share a wire."""
    words = all_words(max_width)
    seen, failures, count = {}, 0, 0
    for n in range(0, max_len + 1):
        for seq in itertools.product(words, repeat=n):
            count += 1
            wire = env.encode(seq)
            try:
                back = env.decode(wire)
            except ValueError:
                failures += 1
                continue
            if tuple(back) != seq or (wire in seen and seen[wire] != seq):
                failures += 1
            seen[wire] = seq
    return count, failures


def check_strict(env: Envelope, max_bits: int) -> Tuple[int, int, int]:
    """Every bit string up to `max_bits`: (checked, accepted, accepted-but-not-canonical)."""
    checked = accepted = bad = 0
    for n in range(0, max_bits + 1):
        for bits in itertools.product("01", repeat=n):
            wire = "".join(bits)
            checked += 1
            try:
                words = env.decode(wire, strict=False)
            except ValueError:
                continue
            accepted += 1
            if env.encode(words) != wire:
                bad += 1
    return checked, accepted, bad


def check_end_of_stream(env: Envelope, max_width: int, max_len: int) -> dict:
    """What happens after byte packing. Counts sequences whose packed form is misread."""
    words = all_words(max_width)
    out = {"sequences": 0, "plain_zero_padding_strict_reader_error": 0, "plain_zero_padding_lazy_reader_wrong_sequence": 0,
           "stop_bit_misread": 0, "length_prefix_misread": 0}
    seen_plain = {}
    for n in range(0, max_len + 1):
        for seq in itertools.product(words, repeat=n):
            out["sequences"] += 1
            wire = env.encode(seq)
            # plain zero padding: the receiver sees only the padded bits
            padded = pad_zero(wire)
            try:
                got = tuple(env.decode(padded, strict=False))
            except ValueError:
                got = None
            if got != seq:
                out["plain_zero_padding_strict_reader_error"] += 1
            try:
                lazy = tuple(env.decode(padded, strict=False, lazy=True))
            except ValueError:
                lazy = None
            if lazy != seq:
                out["plain_zero_padding_lazy_reader_wrong_sequence"] += 1
            seen_plain.setdefault(padded, set()).add(seq)
            try:
                if tuple(env.decode(unpad_stop(pad_stop(wire)))) != seq:
                    out["stop_bit_misread"] += 1
            except ValueError:
                out["stop_bit_misread"] += 1
            try:
                if tuple(unpack_length(env, pack_length(env, seq))) != seq:
                    out["length_prefix_misread"] += 1
            except ValueError:
                out["length_prefix_misread"] += 1
    shared = [(w, sorted(s)) for w, s in seen_plain.items() if len(s) > 1]
    out["padded_wires_shared_by_two_or_more_sequences"] = len(shared)
    out["example_shared_padded_wire"] = shared[:2]
    return out


def cost_table(profile: Sequence[int]) -> List[Tuple[int, int, int]]:
    """Wire cost of a sequence of words of the given widths: (semantic width, A, B)."""
    rows = []
    for w in range(1, 13):
        ws = [w] * len(profile)
        rows.append((w, sum(len(header_a(x)) + x for x in ws), sum(len(header_b(x)) + x for x in ws)))
    return rows


def check_racana2() -> bool:
    structural = ["00", "01", "10", "11"]
    for env in (A, B):
        for seq in itertools.product(structural, repeat=3):
            if tuple(env.decode(env.encode(seq))) != seq:
                return False
        if env.decode(env.encode(["11"])) != ["11"]:       # the dot stays a word
            return False
    return True


def main(argv: Sequence[str]) -> int:
    quick = "--quick" in argv
    max_width, max_len = (4, 2) if quick else (4, 3)
    print(f"# research-1971 unique decoding (words up to {max_width} bits, up to {max_len} words per sequence)\n")
    for env in (A, B):
        n, fail = check_injective_roundtrip(env, max_width, max_len)
        print(f"[1] {env.name}: {n} sequences, {fail} failures (round trip + injectivity)")
    for env in (A, B):
        checked, accepted, bad = check_strict(env, 14 if quick else 16)
        print(f"[2] {env.name}: {checked} bit strings up to {14 if quick else 16} bits, {accepted} accepted, "
              f"{bad} accepted but not canonical (non-strict decoding)")
    for env in (A, B):
        r = check_end_of_stream(env, max_width, 2 if quick else 3)
        print(f"[3] {env.name} end of stream over {r['sequences']} sequences:")
        for k in ("plain_zero_padding_strict_reader_error", "plain_zero_padding_lazy_reader_wrong_sequence",
                  "stop_bit_misread", "length_prefix_misread", "padded_wires_shared_by_two_or_more_sequences"):
            print(f"      {k}: {r[k]}")
        for wire, seqs in r["example_shared_padded_wire"]:
            print(f"      e.g. padded wire {wire} is the packing of {seqs}")
    print("\n[4] full wire cost for one word of width w (bits): w, A, B")
    for w, a, b in cost_table([1]):
        print(f"      {w:>2} {a:>3} {b:>3}")
    print(f"\n[5] racanā2 words 00 01 10 11 (the dot) survive as ordinary words: {check_racana2()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
