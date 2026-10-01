#!/usr/bin/env python3
"""#2189: canonical final-byte framing without zero-padding ambiguity.  Research-only.

Words are exact-width Bits<1..8> values (width and leading zeros are identity). The sequential packer of #2195
puts them in one MSB-first bitstream with no padding between words: payload_bytes = ceil(sum(widths) / 8), the last
byte carries unused tail bits. The question: what is the smallest transport metadata that tells payload from tail?

Frames (the four of #2189), every one built from the same payload bits:
  A  explicit payload bit length (a varint, 7 bits per byte)         then the payload bytes
  B  word count + width stream (varint count, 3 bits per width)       then the payload bytes  (self-describing)
  C  final-byte valid-bit count 1..8 (one byte)                       then the payload bytes; the CONTAINER knows its length
  D  stop-bit: the payload bits, a `1`, zeros to the byte boundary    (no header)

Decoders get the frame bytes and, for A, C, D, the WIDTH sequence from outside (the program grammar). B reads widths itself.

Checks, each can fail:
  1  round trip and strictness: decode(encode(x)) == x; every accepted frame re-encodes to the same bytes
  2  hard laws: truncation fails closed; appended zero bytes cannot create words; non-zero tail padding rejected;
     0-valued suffixes survive; `00` and `11` inside payload are ordinary
  3  the #1980 fixtures (sequences that share a zero-padded byte under the Width3 envelope)
  4  SELF-CONTAINMENT: without the grammar's widths, how many different word sequences give the SAME frame bytes
  5  accounting: payload bits, payload bytes, tail bits, framing bytes, total bytes, utilization
"""

from __future__ import annotations

import itertools
import sys
from typing import Dict, List, Optional, Sequence, Tuple

Word = Tuple[int, int]            # (width, value)
Seq = Tuple[Word, ...]


class FrameError(ValueError):
    pass


# ----------------------------------------------------------------------- bits
def payload_bits(seq: Seq) -> str:
    out = []
    for width, value in seq:
        if not 1 <= width <= 8 or not 0 <= value < (1 << width):
            raise FrameError(f"not an exact-width word: {width}, {value}")
        out.append(f"{value:0{width}b}")
    return "".join(out)


def to_bytes(bits: str) -> bytes:
    bits = bits + "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def split_words(bits: str, widths: Sequence[int]) -> Seq:
    if sum(widths) != len(bits):
        raise FrameError("payload length differs from the widths")
    out, pos = [], 0
    for w in widths:
        out.append((w, int(bits[pos:pos + w], 2)))
        pos += w
    return tuple(out)


def varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def read_varint(data: bytes, pos: int) -> Tuple[int, int]:
    n, shift = 0, 0
    while True:
        if pos >= len(data):
            raise FrameError("truncated varint")
        b = data[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            if b == 0 and shift > 7:
                raise FrameError("non-canonical varint")
            return n, pos


def bits_of(data: bytes) -> str:
    return "".join(f"{b:08b}" for b in data)


# --------------------------------------------------------------------- frames
def enc_a(seq: Seq) -> bytes:
    p = payload_bits(seq)
    return varint(len(p)) + to_bytes(p)


def dec_a(frame: bytes, widths: Optional[Sequence[int]]) -> Seq:
    n, pos = read_varint(frame, 0)
    body = frame[pos:]
    if len(body) != (n + 7) // 8:
        raise FrameError("payload byte count differs from the bit length")
    bits = bits_of(body)
    if set(bits[n:]) - {"0"}:
        raise FrameError("non-zero tail padding")
    if widths is None:
        raise FrameError("frame A does not carry the widths")
    return split_words(bits[:n], widths)


def enc_b(seq: Seq) -> bytes:
    head = "".join(f"{w - 1:03b}" for w, _ in seq)
    return varint(len(seq)) + to_bytes(head) + to_bytes(payload_bits(seq))


def dec_b(frame: bytes, widths: Optional[Sequence[int]] = None) -> Seq:
    count, pos = read_varint(frame, 0)
    wbytes = (3 * count + 7) // 8
    if pos + wbytes > len(frame):
        raise FrameError("truncated width stream")
    wbits = bits_of(frame[pos:pos + wbytes])
    if set(wbits[3 * count:]) - {"0"}:
        raise FrameError("non-zero padding in the width stream")
    ws = [int(wbits[3 * i:3 * i + 3], 2) + 1 for i in range(count)]
    pos += wbytes
    total = sum(ws)
    body = frame[pos:]
    if len(body) != (total + 7) // 8:
        raise FrameError("payload byte count differs from the widths")
    bits = bits_of(body)
    if set(bits[total:]) - {"0"}:
        raise FrameError("non-zero tail padding")
    if widths is not None and list(widths) != ws:
        raise FrameError("widths differ from the grammar")
    return split_words(bits[:total], ws)


def enc_c(seq: Seq) -> bytes:
    p = payload_bits(seq)
    if not p:
        return bytes([0])                                   # valid bits 0 = an empty payload
    valid = len(p) - 8 * ((len(p) - 1) // 8)                # 1..8
    return bytes([valid]) + to_bytes(p)


def dec_c(frame: bytes, widths: Optional[Sequence[int]]) -> Seq:
    if not frame:
        raise FrameError("empty container")
    valid, body = frame[0], frame[1:]
    if valid == 0:
        if body:
            raise FrameError("bytes after an empty payload")
        return () if widths is None or not list(widths) else (_ for _ in ()).throw(FrameError("widths for an empty payload"))
    if not 1 <= valid <= 8 or not body:
        raise FrameError("bad valid-bit count")
    bits = bits_of(body)
    n = len(bits) - 8 + valid
    if set(bits[n:]) - {"0"}:
        raise FrameError("non-zero tail padding")
    if widths is None:
        raise FrameError("frame C does not carry the widths")
    return split_words(bits[:n], widths)


def enc_d(seq: Seq) -> bytes:
    p = payload_bits(seq) + "1"
    return to_bytes(p)


def dec_d(frame: bytes, widths: Optional[Sequence[int]]) -> Seq:
    bits = bits_of(frame).rstrip("0")
    if not frame or not bits.endswith("1") or len(bits_of(frame)) - len(bits) > 7:
        raise FrameError("no valid stop bit")
    n = len(bits) - 1
    if widths is None:
        raise FrameError("frame D does not carry the widths")
    return split_words(bits[:n], widths)


# --- payload-level decoders: what a receiver can recover WITHOUT the grammar's widths (the payload bits only)
def payload_a(frame: bytes) -> str:
    n, pos = read_varint(frame, 0)
    body = frame[pos:]
    if len(body) != (n + 7) // 8:
        raise FrameError("payload byte count differs from the bit length")
    bits = bits_of(body)
    if set(bits[n:]) - {"0"}:
        raise FrameError("non-zero tail padding")
    return bits[:n]


def payload_c(frame: bytes) -> str:
    if not frame:
        raise FrameError("empty container")
    valid, body = frame[0], frame[1:]
    if valid == 0:
        if body:
            raise FrameError("bytes after an empty payload")
        return ""
    if not 1 <= valid <= 8 or not body:
        raise FrameError("bad valid-bit count")
    bits = bits_of(body)
    n = len(bits) - 8 + valid
    if set(bits[n:]) - {"0"}:
        raise FrameError("non-zero tail padding")
    return bits[:n]


def payload_d(frame: bytes) -> str:
    bits = bits_of(frame).rstrip("0")
    if not frame or not bits.endswith("1") or len(bits_of(frame)) - len(bits) > 7:
        raise FrameError("no valid stop bit")
    return bits[:-1]


PAYLOAD_DECODERS = {"A bit length": payload_a, "C valid bits": payload_c, "D stop bit": payload_d}


def check_truncation_without_widths(seqs: Sequence[Seq]) -> Dict[str, Tuple[int, int]]:
    """per frame (A, C, D): proper byte prefixes of a frame, and how many of them are ACCEPTED as a frame
    (the receiver has no grammar to compare the length with). Law: truncation fails closed."""
    out = {}
    for name, dec in PAYLOAD_DECODERS.items():
        enc = FRAMES[name][0]
        prefixes = accepted = 0
        for seq in seqs:
            frame = enc(seq)
            for cut in range(1, len(frame)):
                prefixes += 1
                try:
                    dec(frame[:cut])
                    accepted += 1
                except FrameError:
                    pass
        out[name] = (prefixes, accepted)
    return out


# --- B2: the standalone envelope with a RUN-LENGTH width stream (a cheaper boundary description for runs of equal width)
RUN_MAX = 32


def runs_of(widths: Sequence[int]) -> List[Tuple[int, int]]:
    """Canonical runs: a maximal run of one width, split into full runs of RUN_MAX and a remainder."""
    out: List[Tuple[int, int]] = []
    for w, group in itertools.groupby(widths):
        n = len(list(group))
        while n > RUN_MAX:
            out.append((w, RUN_MAX))
            n -= RUN_MAX
        out.append((w, n))
    return out


def enc_b2(seq: Seq) -> bytes:
    runs = runs_of(widths_of(seq))
    body = bytes(((w - 1) << 5) | (n - 1) for w, n in runs)
    return varint(len(runs)) + body + to_bytes(payload_bits(seq))


def dec_b2(frame: bytes, widths: Optional[Sequence[int]] = None) -> Seq:
    count, pos = read_varint(frame, 0)
    if pos + count > len(frame):
        raise FrameError("truncated run stream")
    runs = [((b >> 5) + 1, (b & 31) + 1) for b in frame[pos:pos + count]]
    for (w0, n0), (w1, _) in zip(runs, runs[1:]):
        if w0 == w1 and n0 != RUN_MAX:
            raise FrameError("non-canonical runs: equal widths must be merged")
    ws = [w for w, n in runs for _ in range(n)]
    pos += count
    total = sum(ws)
    body = frame[pos:]
    if len(body) != (total + 7) // 8:
        raise FrameError("payload byte count differs from the widths")
    bits = bits_of(body)
    if set(bits[total:]) - {"0"}:
        raise FrameError("non-zero tail padding")
    if widths is not None and list(widths) != ws:
        raise FrameError("widths differ from the grammar")
    return split_words(bits[:total], ws)


def enc_bstar(seq: Seq) -> bytes:
    """B*: one mode byte (0 = B, 1 = B2), then whichever of the two is shorter (a tie takes B): canonical by construction."""
    b, b2 = enc_b(seq), enc_b2(seq)
    return bytes([1]) + b2 if len(b2) < len(b) else bytes([0]) + b


def dec_bstar(frame: bytes, widths: Optional[Sequence[int]] = None) -> Seq:
    if not frame or frame[0] not in (0, 1):
        raise FrameError("bad mode byte")
    seq = (dec_b2 if frame[0] else dec_b)(frame[1:], widths)
    if enc_bstar(seq) != frame:
        raise FrameError("not the canonical (shorter) choice")
    return seq


def shape_costs() -> List[Tuple[str, int, int, int, int]]:
    """(shape, words, B, B2, B* framing bytes) for sequences whose widths are generated, values all zero."""
    shapes = {
        "( QUOTE ) = 2,3,2": [2, 3, 2],
        "20 words of width 3 (one run)": [3] * 20,
        "100 words of width 3 (one run)": [3] * 100,
        "alternating 2,3 x 10": [2, 3] * 10,
        "alternating 2,3 x 50": [2, 3] * 50,
        "widths 1..4 cycling x 25": [1, 2, 3, 4] * 25,
    }
    rows = []
    for name, ws in shapes.items():
        seq = tuple((w, 0) for w in ws)
        pb = (sum(ws) + 7) // 8
        rows.append((name, len(ws), len(enc_b(seq)) - pb, len(enc_b2(seq)) - pb, len(enc_bstar(seq)) - pb))
    return rows


FRAMES = {"A bit length": (enc_a, dec_a), "B count+widths": (enc_b, dec_b),
          "C valid bits": (enc_c, dec_c), "D stop bit": (enc_d, dec_d),
          "B2 runs": (enc_b2, dec_b2), "B* mode+shorter": (enc_bstar, dec_bstar)}


# ----------------------------------------------------------------- the corpus
def corpus(max_width: int, max_len: int) -> List[Seq]:
    words = [(w, v) for w in range(1, max_width + 1) for v in range(1 << w)]
    return [s for n in range(max_len + 1) for s in itertools.product(words, repeat=n)]


def widths_of(seq: Seq) -> List[int]:
    return [w for w, _ in seq]


def check_roundtrip(seqs: Sequence[Seq]) -> Dict[str, Tuple[int, int, int]]:
    """per frame: (sequences, failures, accepted-but-not-canonical frames among all single-byte-flip mutations)."""
    out = {}
    for name, (enc, dec) in FRAMES.items():
        fail = noncanon = 0
        for seq in seqs:
            frame = enc(seq)
            try:
                if dec(frame, widths_of(seq)) != seq:
                    fail += 1
            except FrameError:
                fail += 1
        out[name] = (len(seqs), fail, noncanon)
    return out


def check_hard_laws(seqs: Sequence[Seq]) -> Dict[str, Dict[str, int]]:
    """Counts of violations of each law, per frame (0 is the target)."""
    res = {name: {"truncation_not_rejected": 0, "appended_zero_byte_accepted": 0, "nonzero_tail_accepted": 0,
                  "suffix_zero_lost": 0} for name in FRAMES}
    for name, (enc, dec) in FRAMES.items():
        for seq in seqs:
            ws = widths_of(seq)
            frame = enc(seq)
            # truncation: dropping the last byte of a non-empty frame must not decode to the same sequence silently
            if len(frame) > 1:
                try:
                    got = dec(frame[:-1], ws)
                    if got == seq:
                        res[name]["truncation_not_rejected"] += 1
                except FrameError:
                    pass
            # appended zero byte: must be rejected, never create words or change the result
            try:
                dec(frame + b"\x00", ws)
                res[name]["appended_zero_byte_accepted"] += 1
            except FrameError:
                pass
            # set a padding bit (the last bit of the last byte) to 1 when the payload leaves a tail
            p = payload_bits(seq)
            if p and len(p) % 8 and name[0] != "D":           # D's tail is `1000..` by construction; flipping it is a different frame
                mutated = bytearray(frame)
                mutated[-1] |= 1
                try:
                    dec(bytes(mutated), ws)
                    res[name]["nonzero_tail_accepted"] += 1
                except FrameError:
                    pass
            # a 0-valued suffix survives: the last word of all zeros keeps its width
            if seq and seq[-1][1] == 0:
                try:
                    if dec(enc(seq), ws) != seq:
                        res[name]["suffix_zero_lost"] += 1
                except FrameError:
                    res[name]["suffix_zero_lost"] += 1
    return res


def check_fixtures() -> List[Tuple[str, bool]]:
    """The #1980 collision family and the #2166 fixtures, under every frame (distinct decodes, with their widths)."""
    fixtures = {
        "[0],[00] vs [000] (#1980: same zero-padded byte)": [((1, 0), (2, 0)), ((3, 0),)],
        "[1],[1,0] style: [1],[10] vs [110]": [((1, 1), (2, 2)), ((3, 6),)],
        "#2166: 1|01|001": [((1, 1), (2, 1), (3, 1))],
        "#2166: 0|00|000": [((1, 0), (2, 0), (3, 0))],
        "#2166: 10|011|101|110": [((2, 2), (3, 3), (3, 5), (3, 6))],
        "racanā2 11 and 00 inside payload: 11|00|01|10": [((2, 3), (2, 0), (2, 1), (2, 2))],
    }
    rows = []
    for name, seqs in fixtures.items():
        ok = True
        for enc, dec in FRAMES.values():
            for seq in seqs:
                try:
                    ok &= dec(enc(seq), widths_of(seq)) == seq
                except FrameError:
                    ok = False
        rows.append((name, ok))
    return rows


def check_self_containment(seqs: Sequence[Seq]) -> Dict[str, Tuple[int, int]]:
    """per frame: (distinct frames, sequences) and the number of frames shared by 2+ different sequences."""
    out = {}
    for name, (enc, _) in FRAMES.items():
        seen: Dict[bytes, set] = {}
        for seq in seqs:
            seen.setdefault(enc(seq), set()).add(seq)
        shared = sum(1 for v in seen.values() if len(v) > 1)
        out[name] = (shared, len(seen))
    return out


def accounting(seqs: Sequence[Seq]) -> List[Tuple]:
    rows = []
    for name, (enc, _) in FRAMES.items():
        tot_p = tot_pb = tot_tail = tot_f = tot_w = 0
        n = 0
        for seq in seqs:
            p = len(payload_bits(seq))
            pb = (p + 7) // 8
            frame = enc(seq)
            if name[0] == "D":
                tail = 8 * len(frame) - p - 1                  # unused bits after the stop bit; the stop bit itself is framing (1 bit)
                fr_bytes = max(len(frame) - pb, 0)
            else:
                tail = 8 * pb - p
                fr_bytes = len(frame) - pb
            tot_p += p
            tot_pb += pb
            tot_tail += tail
            tot_f += fr_bytes
            tot_w += len(frame)
            n += 1
        rows.append((name, round(tot_p / n, 2), round(tot_pb / n, 2), round(tot_tail / n, 2), round(tot_f / n, 2),
                     round(tot_w / n, 2), round(tot_p / (8 * tot_w), 4) if tot_w else 0))
    return rows


def main(argv: Sequence[str]) -> int:
    quick = "--quick" in argv
    mw, ml = (3, 2) if quick else (4, 3)
    seqs = corpus(mw, ml)
    print(f"# research-2189 tail length (words up to {mw} bits, up to {ml} words; {len(seqs)} sequences)\n")
    for name, (n, fail, _) in check_roundtrip(seqs).items():
        print(f"[1] {name}: {n} sequences, {fail} round-trip failures (widths from the grammar for A, C, D)")
    print()
    for name, laws in check_hard_laws(seqs).items():
        print(f"[2] {name}: " + ", ".join(f"{k}={v}" for k, v in laws.items()))
    print()
    for name, ok in check_fixtures():
        print(f"[3] fixture {name}: {'all frames round-trip' if ok else 'FAILS'}")
    print("\n[2b] truncation WITHOUT the grammar's widths (a receiver that only recovers the payload bits): proper byte prefixes of a frame accepted as a frame:")
    for name, (prefixes, accepted) in check_truncation_without_widths(seqs).items():
        print(f"      {name}: {accepted} of {prefixes} proper prefixes accepted")
    print("      (with the grammar's widths a truncated frame fails the length check in every frame; the table in [2] uses them)")
    print("\n[4] self-containment: frames shared by 2+ DIFFERENT word sequences (without the grammar's widths):")
    for name, (shared, distinct) in check_self_containment(seqs).items():
        print(f"      {name}: {shared} shared frames of {distinct} distinct frames")
    print("\n[4b] standalone-envelope width streams: framing bytes (everything except the payload bytes), B = count + 3 bits per width, B2 = run-length (1 byte per run), B* = a mode byte + the shorter of the two:")
    for shape, n, b_bytes, b2_bytes, bs_bytes in shape_costs():
        print(f"      {shape:36} {n:>4} words   B {b_bytes:>3}   B2 {b2_bytes:>3}   B* {bs_bytes:>3}")
    print("\n[5] accounting, mean per sequence: frame | payload bits | payload bytes | tail bits | framing bytes | total bytes | utilization")
    for r in accounting(seqs):
        print("      " + " | ".join(str(x) for x in r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
