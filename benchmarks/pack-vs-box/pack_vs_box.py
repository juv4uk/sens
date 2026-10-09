#!/usr/bin/env python3
"""#2190 — density vs cost for Bits-like words: u8 box vs sequential pack.

Research-only. Models mechanism cost in pure Python; does not own SENS
semantic roles. MSB-first sequential packing matches the #2188 law shape:

  payload_bits  = sum(word widths)
  payload_bytes = ceil(payload_bits / 8)

Candidates:
  A box     — one physical byte per word (width tracked out-of-band)
  C pack    — mixed-width sequential bit reservoir

  python3 benchmarks/pack-vs-box/pack_vs_box.py [--out DIR]
"""

from __future__ import annotations

import argparse
import csv
import random
import time
from pathlib import Path

KINDS = ("D1", "D2", "D3", "mixed123", "Bit8")
SIZES = (8, 64, 1024, 8192)


def workload(kind: str, n: int, seed: int = 1) -> tuple[list[int], list[int]]:
    rng = random.Random(seed ^ (n * 1009) ^ hash(kind) & 0xFFFFFFFF)
    if kind == "D1":
        widths = [1] * n
    elif kind == "D2":
        widths = [2] * n
    elif kind == "D3":
        widths = [3] * n
    elif kind == "mixed123":
        widths = [1 + (i % 3) for i in range(n)]
    elif kind == "Bit8":
        widths = [8] * n
    else:
        raise ValueError(kind)
    values = [rng.randint(0, (1 << w) - 1) for w in widths]
    return widths, values


def pack_words(widths: list[int], values: list[int]) -> tuple[bytes, int]:
    bits: list[int] = []
    for w, v in zip(widths, values):
        for i in range(w - 1, -1, -1):
            bits.append((v >> i) & 1)
    bit_len = len(bits)
    out = bytearray((bit_len + 7) // 8)
    for i, b in enumerate(bits):
        if b:
            out[i // 8] |= 1 << (7 - (i % 8))
    return bytes(out), bit_len


def unpack_words(data: bytes, widths: list[int], bit_len: int) -> list[int]:
    values: list[int] = []
    pos = 0
    for w in widths:
        v = 0
        for _ in range(w):
            byte = data[pos // 8]
            bit = (byte >> (7 - (pos % 8))) & 1
            v = (v << 1) | bit
            pos += 1
        values.append(v)
    if pos != bit_len:
        raise AssertionError("bit cursor mismatch")
    return values


def median_us(fn, reps: int) -> float:
    samples = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1e6)
    samples.sort()
    return samples[len(samples) // 2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("benchmarks/pack-vs-box/results"))
    ap.add_argument("--reps", type=int, default=21)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = []
    for kind in KINDS:
        for n in SIZES:
            widths, values = workload(kind, n, args.seed)
            sem_bits = sum(widths)
            box_bytes = n
            packed, bit_len = pack_words(widths, values)
            assert unpack_words(packed, widths, bit_len) == values
            pack_bytes = len(packed)
            util = (100.0 * sem_bits / (pack_bytes * 8)) if pack_bytes else 0.0
            density_gain = box_bytes / pack_bytes if pack_bytes else 0.0

            pack_us = median_us(lambda: pack_words(widths, values), args.reps)
            unpack_us = median_us(
                lambda: unpack_words(packed, widths, bit_len), args.reps
            )

            rows.append(
                {
                    "kind": kind,
                    "n": n,
                    "semantic_bits": sem_bits,
                    "box_bytes": box_bytes,
                    "pack_bytes": pack_bytes,
                    "utilization_pct": f"{util:.2f}",
                    "density_gain_box_over_pack": f"{density_gain:.3f}",
                    "pack_us_median": f"{pack_us:.2f}",
                    "unpack_us_median": f"{unpack_us:.2f}",
                    "metric": "python_wall_diagnostic",
                    "notes": "not_cachegrind; mechanism model only",
                }
            )
            print(
                f"{kind:9} n={n:5} box={box_bytes:5} pack={pack_bytes:5} "
                f"util={util:5.1f}% gain×{density_gain:.2f} "
                f"pack={pack_us:.0f}µs unpack={unpack_us:.0f}µs"
            )

    tsv = args.out / "pack_vs_box.tsv"
    with tsv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
