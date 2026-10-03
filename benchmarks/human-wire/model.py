#!/usr/bin/env python3
"""Human-wire timing model for SENS (#2642).

Research/mechanism only.  This module compares the same binary frame through
several human-keyable encodings.  It does not assign semantic domains or claim
that a human can sustain any particular unit duration; measured trials belong
in the event-log layer described by README.md.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

MORSE_HEX = {
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
}


@dataclass(frozen=True)
class Result:
    protocol: str
    payload_bits: int
    transmitted_bits: int
    timing_units: int
    unit_ms: float
    seconds: float
    equivalent_frame_bps: float
    net_payload_bps: float
    assistance: str
    note: str


def bits_of(data: bytes) -> str:
    return "".join(f"{byte:08b}" for byte in data)


def morse_symbol_units(symbol: str) -> int:
    marks = MORSE_HEX[symbol]
    pulse_units = sum(1 if mark == "." else 3 for mark in marks)
    internal_gaps = max(0, len(marks) - 1)
    return pulse_units + internal_gaps


def morse_hex_units(data: bytes, *, character_gap: int = 3) -> int:
    text = data.hex().upper()
    if not text:
        return 0
    return (
        sum(morse_symbol_units(symbol) for symbol in text)
        + character_gap * (len(text) - 1)
    )


def duration_binary_units(
    bits: str,
    *,
    short_units: int = 1,
    long_units: int = 3,
    separator_units: int = 1,
) -> int:
    if not bits:
        return 0
    pulses = sum(short_units if bit == "0" else long_units for bit in bits)
    return pulses + separator_units * (len(bits) - 1)


def dual_key_binary_units(
    bits: str,
    *,
    pulse_units: int = 1,
    separator_units: int = 1,
) -> int:
    if not bits:
        return 0
    return pulse_units * len(bits) + separator_units * (len(bits) - 1)


def fixed_slot_units(bits: str, *, slot_units: int = 1) -> int:
    return len(bits) * slot_units


def _result(
    protocol: str,
    *,
    payload_bits: int,
    transmitted_bits: int,
    timing_units: int,
    unit_ms: float,
    assistance: str,
    note: str,
) -> Result:
    seconds = timing_units * unit_ms / 1000.0
    if seconds == 0:
        frame_bps = 0.0
        payload_bps = 0.0
    else:
        frame_bps = transmitted_bits / seconds
        payload_bps = payload_bits / seconds
    return Result(
        protocol=protocol,
        payload_bits=payload_bits,
        transmitted_bits=transmitted_bits,
        timing_units=timing_units,
        unit_ms=unit_ms,
        seconds=seconds,
        equivalent_frame_bps=frame_bps,
        net_payload_bps=payload_bps,
        assistance=assistance,
        note=note,
    )


def compare(
    frame: bytes,
    *,
    payload_bits: int | None = None,
    unit_ms: float = 60.0,
    short_units: int = 1,
    long_units: int = 3,
    separator_units: int = 1,
) -> list[Result]:
    bitstream = bits_of(frame)
    transmitted_bits = len(bitstream)
    if payload_bits is None:
        payload_bits = transmitted_bits
    if payload_bits < 0 or payload_bits > transmitted_bits:
        raise ValueError("payload_bits must be within the transmitted frame")

    return [
        _result(
            "hex-morse",
            payload_bits=payload_bits,
            transmitted_bits=transmitted_bits,
            timing_units=morse_hex_units(frame),
            unit_ms=unit_ms,
            assistance="none beyond ordinary Morse timing",
            note="frame bytes rendered as hexadecimal characters, then International Morse",
        ),
        _result(
            "duration-binary",
            payload_bits=payload_bits,
            transmitted_bits=transmitted_bits,
            timing_units=duration_binary_units(
                bitstream,
                short_units=short_units,
                long_units=long_units,
                separator_units=separator_units,
            ),
            unit_ms=unit_ms,
            assistance="single key; timing discrimination required",
            note="0=short pulse, 1=long pulse; separators are explicit timing cost",
        ),
        _result(
            "dual-key-binary",
            payload_bits=payload_bits,
            transmitted_bits=transmitted_bits,
            timing_units=dual_key_binary_units(
                bitstream,
                pulse_units=1,
                separator_units=separator_units,
            ),
            unit_ms=unit_ms,
            assistance="two distinguishable keys/channels",
            note="0 and 1 use distinct keys; equal-duration pulses avoid short/long bias",
        ),
        _result(
            "fixed-slot-binary",
            payload_bits=payload_bits,
            transmitted_bits=transmitted_bits,
            timing_units=fixed_slot_units(bitstream),
            unit_ms=unit_ms,
            assistance="external clock/metronome required",
            note="one clocked slot per bit; silence/press is meaningful only with shared timing",
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hex", required=True, help="complete transmitted frame as even-length hex")
    parser.add_argument(
        "--payload-bits",
        type=int,
        default=None,
        help="useful payload bits inside the transmitted frame; default = whole frame",
    )
    parser.add_argument(
        "--unit-ms",
        type=float,
        default=60.0,
        help="duration of one timing unit; 60 ms corresponds to 20-WPM PARIS timing",
    )
    parser.add_argument("--short-units", type=int, default=1)
    parser.add_argument("--long-units", type=int, default=3)
    parser.add_argument("--separator-units", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if len(args.hex) % 2:
        raise SystemExit("--hex must contain a whole number of bytes")
    try:
        frame = bytes.fromhex(args.hex)
        rows = compare(
            frame,
            payload_bits=args.payload_bits,
            unit_ms=args.unit_ms,
            short_units=args.short_units,
            long_units=args.long_units,
            separator_units=args.separator_units,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    if args.json:
        print(json.dumps([asdict(row) for row in rows], indent=2, sort_keys=True))
        return 0

    print("protocol\tunits\tseconds\tframe-equivalent-bps\tnet-payload-bps\tassistance")
    for row in rows:
        print(
            f"{row.protocol}\t{row.timing_units}\t{row.seconds:.3f}\t"
            f"{row.equivalent_frame_bps:.3f}\t{row.net_payload_bps:.3f}\t"
            f"{row.assistance}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
