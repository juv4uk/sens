#!/usr/bin/env python3
"""Fail-closed hardware ROM parity to immutable D3 source; no semantics invented."""
from __future__ import annotations
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[3]
CODEC = ROOT / "scripts/sens_t5_codec.py"
spec = importlib.util.spec_from_file_location("silicon_t5_codec", CODEC)
assert spec and spec.loader
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

ORIGINAL = ROOT / "examples/binary/d3-primitives-program.bits"
ROM = ROOT / "hardware/sens-silicon/tb/d3-primitives.t5.hex"
CASES = ((0, 5), (5, 11), (11, 22), (22, 39), (39, 56), (56, 63))


def verify() -> list[int]:
    words = ORIGINAL.read_text(encoding="ascii").split()
    if len(words) != 63:
        raise ValueError("original D3 source must have exactly 63 words")
    groups = []
    for i, (start, end) in enumerate(CASES):
        current = words[start:end]
        if i == 1:
            if current != "10 010 00 10 01 01".split():
                raise ValueError("old D2 open-close empty witness changed")
            current = "10 010 00 000 01".split()
        payload = codec.encode_words(current)
        if codec.decode_bytes(payload) != current:
            raise ValueError("T5 byte/width roundtrip drift")
        groups.append(payload)

    expected = b"".join(groups)
    if len(expected) != 38:
        raise ValueError("expected six canonical D3 programs occupy 38 T5 bytes")
    rom = bytes(int(token, 16) for line in ROM.read_text(encoding="ascii").splitlines()
                for token in line.split("//", 1)[0].split())
    if rom != expected:
        raise ValueError("HDL memory init differs from original SENS physical T5 bytes")
    return [len(part) for part in groups]


if __name__ == "__main__":
    try:
        lengths = verify()
    except (OSError, ValueError, codec.SensT5Error) as exc:
        print(f"SILICON_VECTOR_BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(f"SILICON_VECTOR_PASS bytes={sum(lengths)} lengths={lengths} source=immutable exact words")
