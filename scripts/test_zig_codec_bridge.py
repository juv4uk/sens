#!/usr/bin/env python3
"""One focused real Zig 0.16 migration-bridge test; transport only.

This is not a SENS evaluator or a semantic oracle. No repository files are
rewritten. An invalid T5 octet must be rejected rather than silently decoded.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
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
          "first_difference=NONE malformed_ff=REJECTED semantic_authority=SENS")


if __name__ == "__main__":
    main()
