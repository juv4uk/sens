#!/usr/bin/env python3
"""One focused real Zig 0.16 migration-bridge test; transport only.

This is not a SENS evaluator or a semantic oracle. No repository files are
rewritten. An invalid T5 octet must be rejected rather than silently decoded.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile

from zig_codec_bridge import ZigCodecError, build_transport, verify_t5

GOLDEN_T5 = bytes.fromhex("638906a1")  # Known canonical T5 bytes for QUOTE.


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="sens-zig-migration-smoke-") as temp:
        executable = build_transport(Path(temp))
        evidence = verify_t5(executable, GOLDEN_T5)
        expected = hashlib.sha256(GOLDEN_T5).hexdigest()
        if evidence["physical_sha256"] != expected or evidence["zig_version"] != "0.16.0":
            raise AssertionError(
                f"ZIG_BRIDGE_MISMATCH id=zig-migration-bridge-t5-exact-physical "
                f"layer=transport expected_sha256={expected} actual={evidence}"
            )
        # Exact ten-bit D10 zero coordinate: TWO 0x00 bytes. This is not an
        # executable D1..D9 word, but migration must preserve its physical bits.
        d10 = bytes([0x00, 0x00])
        proof = verify_t5(executable, d10)
        if proof["physical_sha256"] != hashlib.sha256(d10).hexdigest() or (
            proof["profile"] != "D1-D10_COORDINATES_NOT_EXECUTION"
        ):
            raise AssertionError("D10_COORDINATES_NOT_PRESERVED")
        d10_path = Path(temp) / "d10.sens"
        d10_path.write_bytes(d10)
        runnable = subprocess.run(
            [str(executable), "t5-check", str(d10_path)],
            capture_output=True, text=True, check=False
        )
        if runnable.returncode == 0:
            raise AssertionError(
                "D10_WRONG_EXECUTION_ADMISSION expected=reject actual=accepted"
            )
        try:
            verify_t5(executable, bytes([0, 0, 0]))  # Unsupported D15.
        except ZigCodecError as exc:
            if "ZIG_CODEC_FAILURE" not in str(exc):
                raise
        else:
            raise AssertionError(
                "OVERWIDTH_COORDINATE_ACCEPTED expected=reject actual=accepted"
            )
        try:
            verify_t5(executable, bytes([255]))  # Outside base-3 T5 byte range.
        except ZigCodecError as exc:
            if "ZIG_CODEC_FAILURE" not in str(exc):
                raise
        else:
            raise AssertionError(
                "ZIG_BRIDGE_INVALID_ACCEPTED id=zig-migration-bridge-t5-exact-physical "
                "layer=transport expected=reject-ff actual=accepted"
            )
    print(f"ZIG_BRIDGE_PASS id=zig-migration-bridge-t5-exact-physical "
          f"layer=transport zig=0.16.0 physical_sha256={expected} "
          "first_difference=NONE malformed_ff=REJECTED d10_transport=ACCEPTED "
          "d10_executable=REJECTED overwidth_d15=REJECTED "
          "semantic_authority=SENS")


if __name__ == "__main__":
    main()
