#!/usr/bin/env python3
"""Fail-closed: Rust\u2194SENS physical wire must use the sterile Zig corridor.

Does not run Zig. Does not admit programs. Audits source contracts only:

  1. sens-cli default features include zig-transport
  2. zig_transport.rs is FFI-only to sens_zig_* (no local T5 algorithm)
  3. transport_abi.zig exports encode_be3 + decode_be3 (ABI v2)
  4. build.rs links transport_abi when CARGO_FEATURE_ZIG_TRANSPORT is set
  5. sens-trit path-includes the corridor module

Owner law: Zig = turnstile, SENS = meaning, Rust = opaque bytes / host.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI_TOML = ROOT / "crates" / "sens-cli" / "Cargo.toml"
CORRIDOR = ROOT / "crates" / "sens-cli" / "src" / "zig_transport.rs"
TRIT = ROOT / "crates" / "sens-cli" / "src" / "bin" / "sens-trit.rs"
MAIN = ROOT / "crates" / "sens-cli" / "src" / "main.rs"
ABI = ROOT / "research" / "zig-codecs" / "transport_abi.zig"
BUILD = ROOT / "crates" / "sens-cli" / "build.rs"

BANNED_IN_CORRIDOR = re.compile(
    r"(?i)\b(ternary_transport|PhysicalT5Program|TRITS_BY_BYTE|"
    r"append_t5_digit)\b"
)
REQUIRED_FFI = (
    "sens_zig_codec_abi_version",
    "sens_zig_t5_validate",
    "sens_zig_t5_encode_be3",
    "sens_zig_t5_decode_be3",
    "sens_zig_f3c_pack",
    "sens_zig_f3c_unpack",
)


class CorridorBlocked(ValueError):
    pass


def check() -> list[str]:
    notes: list[str] = []
    toml = CLI_TOML.read_text(encoding="utf-8")
    if 'default = ["zig-transport"]' not in toml and "default = ['zig-transport']" not in toml:
        raise CorridorBlocked("sens-cli default features must enable zig-transport")
    notes.append("default=zig-transport")

    if not CORRIDOR.is_file() or CORRIDOR.is_symlink():
        raise CorridorBlocked("missing regular crates/sens-cli/src/zig_transport.rs")
    body = CORRIDOR.read_text(encoding="utf-8")
    if BANNED_IN_CORRIDOR.search(body):
        raise CorridorBlocked("zig_transport.rs contains local T5 algorithm markers")
    for name in REQUIRED_FFI:
        if name not in body:
            raise CorridorBlocked(f"zig_transport.rs missing FFI {name}")
    if 'extern "C"' not in body:
        raise CorridorBlocked("zig_transport.rs missing C ABI extern block")
    notes.append("corridor-ffi-only")

    abi = ABI.read_text(encoding="utf-8")
    for name in ("sens_zig_t5_encode_be3", "sens_zig_t5_decode_be3"):
        if f"pub export fn {name}" not in abi:
            raise CorridorBlocked(f"transport_abi.zig missing export {name}")
    notes.append("abi-v2-encode-decode")

    build = BUILD.read_text(encoding="utf-8")
    if "transport_abi.zig" not in build:
        raise CorridorBlocked("build.rs does not compile transport_abi.zig")
    if "CARGO_FEATURE_ZIG_TRANSPORT" not in build:
        raise CorridorBlocked("build.rs does not gate on zig-transport feature")
    notes.append("build-links-zig")

    trit = TRIT.read_text(encoding="utf-8")
    if "zig_transport.rs" not in trit:
        raise CorridorBlocked("sens-trit.rs must path-include zig_transport.rs")
    if trit.count("fn sens_zig_t5_encode_be3") > 0:
        raise CorridorBlocked("sens-trit.rs still embeds local Zig FFI")
    if trit.count("zig_transport::") < 1:
        raise CorridorBlocked("sens-trit.rs does not call zig_transport corridor API")
    notes.append("sens-trit-uses-corridor")

    if MAIN.is_file() and "zig_transport" in MAIN.read_text(encoding="utf-8"):
        notes.append("sens-cli-main-aware")
    return notes


def main() -> int:
    try:
        notes = check()
    except CorridorBlocked as err:
        print(f"STERILE_ZIG_CORRIDOR_BLOCKED: {err}", file=sys.stderr)
        return 1
    print("STERILE_ZIG_CORRIDOR_PASS " + " ".join(notes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
