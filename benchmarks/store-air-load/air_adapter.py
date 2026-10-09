#!/usr/bin/env python3
"""Transport-neutral AIR adapter boundary for STORE -> AIR -> LOAD.

This module deliberately does not implement Tantu. No Tantu wire contract is
present in this repository. It defines the seam a future transport adapter must
satisfy while keeping canonical STORE/LOAD semantics outside the transport.

The reference framed adapter exists only to make framing/integrity accounting
and corruption sensitivity executable.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from typing import Protocol

HEADER_BITS = 32
DIGEST_BITS = 256
MAX_PAYLOAD_BITS = (1 << HEADER_BITS) - 1


class AirError(ValueError):
    """Base class for AIR boundary failures."""


class AirFrameError(AirError):
    """The frame is structurally invalid or inconsistent with its accounting."""


class AirIntegrityError(AirError):
    """The frame structure is valid but its integrity witness does not match."""


def require_bits(bits: str, *, name: str, allow_empty: bool = False) -> str:
    if not isinstance(bits, str):
        raise AirFrameError(f"{name} must be a bit string")
    if not allow_empty and not bits:
        raise AirFrameError(f"{name} must be non-empty")
    if any(bit not in "01" for bit in bits):
        raise AirFrameError(f"{name} must contain only 0/1")
    return bits


def digest_bits(payload_bits: str) -> str:
    """Digest exact bits without silently byte-padding the payload."""
    material = f"{len(payload_bits)}:{payload_bits}".encode("ascii")
    digest = hashlib.sha256(material).digest()
    return "".join(f"{byte:08b}" for byte in digest)


@dataclass(frozen=True)
class AirFrame:
    adapter: str
    frame_bits: str
    carrier_payload_bits: int
    framing_bits: int
    integrity_bits: int
    profile_overhead_bits: int = 0

    @property
    def total_wire_bits(self) -> int:
        return len(self.frame_bits)

    @property
    def payload_utilization(self) -> float:
        return self.carrier_payload_bits / self.total_wire_bits

    def validate_accounting(self) -> None:
        require_bits(self.frame_bits, name="frame_bits")
        counts = (
            self.carrier_payload_bits,
            self.framing_bits,
            self.integrity_bits,
            self.profile_overhead_bits,
        )
        if any(not isinstance(value, int) or value < 0 for value in counts):
            raise AirFrameError("AIR accounting fields must be non-negative integers")
        if self.carrier_payload_bits <= 0:
            raise AirFrameError("carrier_payload_bits must be positive")
        expected = sum(counts)
        if expected != self.total_wire_bits:
            raise AirFrameError(
                "total wire bits must equal carrier + framing + integrity + profile overhead"
            )


class AirAdapter(Protocol):
    """Transport/profile mechanism. It owns no language semantics."""

    name: str

    def encode(self, payload_bits: str) -> AirFrame:
        ...

    def decode(self, frame: AirFrame) -> str:
        ...


class IdentityAirAdapter:
    """Reference baseline: AIR adds no framing or integrity bits."""

    name = "identity-exact-bitstream/v1"

    def encode(self, payload_bits: str) -> AirFrame:
        payload = require_bits(payload_bits, name="payload_bits")
        frame = AirFrame(
            adapter=self.name,
            frame_bits=payload,
            carrier_payload_bits=len(payload),
            framing_bits=0,
            integrity_bits=0,
            profile_overhead_bits=0,
        )
        frame.validate_accounting()
        return frame

    def decode(self, frame: AirFrame) -> str:
        if frame.adapter != self.name:
            raise AirFrameError(f"wrong adapter: {frame.adapter}")
        frame.validate_accounting()
        if frame.framing_bits or frame.integrity_bits or frame.profile_overhead_bits:
            raise AirFrameError("identity adapter cannot consume transport overhead")
        if frame.carrier_payload_bits != frame.total_wire_bits:
            raise AirFrameError("identity carrier must be the exact payload bitstream")
        return frame.frame_bits


class ReferenceIntegrityAirAdapter:
    """Executable AIR-boundary witness, not a proposed Tantu wire format.

    Layout:
        32-bit payload length | exact payload bits | SHA-256(length:payload)

    The header is counted as framing, the digest as integrity, and no byte
    padding is inserted. This makes every accounting class independently
    observable while preserving exact-bit payload identity.
    """

    name = "reference-length-sha256-frame/v1"

    def encode(self, payload_bits: str) -> AirFrame:
        payload = require_bits(payload_bits, name="payload_bits")
        if len(payload) > MAX_PAYLOAD_BITS:
            raise AirFrameError("payload exceeds 32-bit reference length field")
        header = f"{len(payload):0{HEADER_BITS}b}"
        integrity = digest_bits(payload)
        frame = AirFrame(
            adapter=self.name,
            frame_bits=header + payload + integrity,
            carrier_payload_bits=len(payload),
            framing_bits=HEADER_BITS,
            integrity_bits=DIGEST_BITS,
            profile_overhead_bits=0,
        )
        frame.validate_accounting()
        return frame

    def decode(self, frame: AirFrame) -> str:
        if frame.adapter != self.name:
            raise AirFrameError(f"wrong adapter: {frame.adapter}")
        frame.validate_accounting()
        if frame.framing_bits != HEADER_BITS:
            raise AirFrameError("reference adapter framing_bits drift")
        if frame.integrity_bits != DIGEST_BITS:
            raise AirFrameError("reference adapter integrity_bits drift")
        if frame.profile_overhead_bits != 0:
            raise AirFrameError("reference adapter has no profile overhead")

        bits = frame.frame_bits
        if len(bits) < HEADER_BITS + DIGEST_BITS + 1:
            raise AirFrameError("reference frame is too short")

        declared = int(bits[:HEADER_BITS], 2)
        expected_total = HEADER_BITS + declared + DIGEST_BITS
        if len(bits) != expected_total:
            raise AirFrameError(
                f"declared payload length {declared} does not match frame length"
            )
        if frame.carrier_payload_bits != declared:
            raise AirFrameError("carrier_payload_bits disagrees with framed length")

        payload_start = HEADER_BITS
        payload_end = payload_start + declared
        payload = bits[payload_start:payload_end]
        observed_digest = bits[payload_end:]
        expected_digest = digest_bits(payload)
        if observed_digest != expected_digest:
            raise AirIntegrityError("AIR integrity witness rejected the frame")
        return payload


def flip_bit(bits: str, index: int) -> str:
    require_bits(bits, name="bits")
    if not 0 <= index < len(bits):
        raise IndexError(index)
    flipped = "1" if bits[index] == "0" else "0"
    return bits[:index] + flipped + bits[index + 1 :]


def with_frame_bits(frame: AirFrame, bits: str) -> AirFrame:
    return AirFrame(
        adapter=frame.adapter,
        frame_bits=bits,
        carrier_payload_bits=frame.carrier_payload_bits,
        framing_bits=frame.framing_bits,
        integrity_bits=frame.integrity_bits,
        profile_overhead_bits=frame.profile_overhead_bits,
    )


def self_test() -> None:
    payloads = (
        "1",
        "10",
        "0010110",
        "00101101",
        "101001011011",
        "1010010110110010110101101011",
    )
    identity = IdentityAirAdapter()
    reference = ReferenceIntegrityAirAdapter()

    for payload in payloads:
        plain = identity.encode(payload)
        assert identity.decode(plain) == payload
        assert plain.total_wire_bits == len(payload)
        assert plain.payload_utilization == 1.0

        framed = reference.encode(payload)
        assert reference.decode(framed) == payload
        assert framed.carrier_payload_bits == len(payload)
        assert framed.framing_bits == HEADER_BITS
        assert framed.integrity_bits == DIGEST_BITS
        assert framed.total_wire_bits == len(payload) + HEADER_BITS + DIGEST_BITS
        assert framed.payload_utilization == len(payload) / framed.total_wire_bits

        payload_bit = HEADER_BITS + len(payload) // 2
        corrupted_payload = with_frame_bits(
            framed, flip_bit(framed.frame_bits, payload_bit)
        )
        try:
            reference.decode(corrupted_payload)
        except AirIntegrityError:
            pass
        else:
            raise AssertionError("payload corruption escaped AIR integrity witness")

        corrupted_header = with_frame_bits(
            framed, flip_bit(framed.frame_bits, 0)
        )
        try:
            reference.decode(corrupted_header)
        except AirFrameError:
            pass
        else:
            raise AssertionError("header corruption escaped AIR framing checks")

        truncated = with_frame_bits(framed, framed.frame_bits[:-1])
        try:
            reference.decode(truncated)
        except AirFrameError:
            pass
        else:
            raise AssertionError("truncation escaped AIR framing checks")

    print("AIR-BOUNDARY=PASS")
    print(f"IDENTITY-ADAPTER={identity.name}")
    print(f"REFERENCE-ADAPTER={reference.name}")
    print("TANTU=UNBOUND-NO-REPOSITORY-WIRE-CONTRACT")
    print("SEMANTIC-AUTHORITY=NONE")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run AIR round-trip/accounting/corruption witnesses",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.self_test:
        raise SystemExit("use --self-test; this module is an adapter contract witness")
    self_test()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
