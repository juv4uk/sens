#!/usr/bin/env python3
"""Fail-closed: Rust\u2194SENS physical wire must use the sterile Zig corridor.

Does not run Zig. Does not admit programs. Audits source contracts only:

  1. sens-cli default features include zig-transport
  2. zig_transport.rs is FFI-only to sens_zig_* (no local T5 algorithm)
  3. transport_abi.zig exports encode_be3 + decode_be3 (ABI v2)
  4. build.rs links transport_abi when CARGO_FEATURE_ZIG_TRANSPORT is set
  5. sens-trit path-includes the corridor module
  6. typed reconstruction uses packed_bits + BitN::new (W1..W9)

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
    r"append_t5_digit|from_width_bits)\b"
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


def _route_between(source: str, begin: str, end: str) -> str:
    """Extract one mandatory CLI routine, never silently miss or duplicate it."""
    if source.count(begin) != 1 or source.count(end) != 1:
        raise CorridorBlocked(f"sens main physical route missing/duplicated: {begin}")
    start = source.index(begin) + len(begin)
    stop = source.index(end, start)
    return source[start:stop]


def check_main_t5_ingress(source: str) -> None:
    """Source-level guard only: default physical T5 MUST cross Zig ABI v2.

    A passing pattern is NOT proof of runtime behaviour or of the complete
    Rust↔SENS ecosystem; it rules out this particular CLI regression.
    """
    if '#[cfg(feature = "zig-transport")]\nmod zig_transport;' not in source:
        raise CorridorBlocked("sens main lacks default feature-gated Zig bridge")
    ingress = _route_between(source, "fn decode_physical_t5_words(", "\nfn eval_physical_t5(")
    positive = '#[cfg(feature = "zig-transport")]'
    negative = '#[cfg(not(feature = "zig-transport"))]'
    if ingress.count(positive) != 1 or ingress.count(negative) != 1:
        raise CorridorBlocked("sens main T5 ingress missing separate feature gates")
    zig, reference = ingress.split(negative, 1)
    if 'return zig_transport::decode_t5_words(bytes);' not in zig:
        raise CorridorBlocked("sens main default T5 decoder bypasses Zig BE3")
    if "sens::decode_ternary_words" in ingress or "PhysicalT5Program::decode(" in ingress:
        raise CorridorBlocked("sens main T5 ingress has Rust physical fallback")
    if 'Err("physical .sens requires the Zig transport corridor; no Rust fallback".into())' not in reference:
        raise CorridorBlocked("sens main feature-negative .sens route must refuse fallback")

    evaluation = _route_between(source, "fn eval_physical_t5(", "\nfn main()")
    if "let words = decode_physical_t5_words(bytes)?;" not in evaluation:
        raise CorridorBlocked("sens main eval bypasses Zig physical ingress")
    if "sens::parse_canonical_word_sequence(&words)" not in evaluation:
        raise CorridorBlocked("sens main physical words bypass SENS canonical D2")
    if "sens::decode_ternary_words" in evaluation or "PhysicalT5Program::decode(" in evaluation:
        raise CorridorBlocked("sens main eval embeds a Rust physical T5 decoder")
    # Prove the one-file .sens dispatch actually calls this guarded evaluator.
    entry = _route_between(source, "fn main() {", "\n#[cfg(test)]")
    if "physical_t5_request(&raw_args)" not in entry or "eval_physical_t5(&bytes)" not in entry:
        raise CorridorBlocked("sens .sens command no longer calls guarded Zig ingress")


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
    if "from_width_bits" in body or ".bits()" in body:
        raise CorridorBlocked(
            "zig_transport.rs must use packed_bits + BitN::new, not phantom APIs"
        )
    if "packed_bits" not in body or "BinarySourceWord::W1" not in body:
        raise CorridorBlocked(
            "zig_transport.rs must reconstruct BinarySourceWord via BitN::new"
        )
    notes.append("typed-w1-w9-reconstruction")

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

    if not MAIN.is_file() or MAIN.is_symlink():
        raise CorridorBlocked("missing regular crates/sens-cli/src/main.rs")
    check_main_t5_ingress(MAIN.read_text(encoding="utf-8"))
    notes.append("sens-cli-main-zig-only-ingress")
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
