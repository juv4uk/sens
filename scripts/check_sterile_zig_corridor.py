#!/usr/bin/env python3
"""Fail-closed: Rust↔SENS physical wire must use the sterile Zig corridor.

Does not run Zig. Does not admit programs. Audits source contracts only.
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
    "sens_zig_e1_encode_be3",
    "sens_zig_e1_decode_be3",
    "sens_zig_f3c_pack",
    "sens_zig_f3c_unpack",
)


class CorridorBlocked(ValueError):
    pass


def _production_source(source: str) -> str:
    """Drop #[cfg(test)] modules so string literals in tests cannot fake routes."""
    marker = "\n#[cfg(test)]"
    if marker in source:
        return source.split(marker, 1)[0]
    return source


def _route_between(source: str, begin: str, end: str) -> str:
    """Extract one mandatory CLI routine, never silently miss or duplicate it."""
    prod = _production_source(source)
    if begin not in prod or prod.count(begin) != 1:
        raise CorridorBlocked(f"sens main physical route missing/duplicated: {begin}")
    start = prod.index(begin) + len(begin)
    if end == "\n#[cfg(test)]":
        if not source[len(prod):].startswith(end):
            raise CorridorBlocked(f"sens main production/test boundary missing: {begin}")
        return prod[start:]
    if end not in prod[start:]:
        raise CorridorBlocked(f"sens main physical route missing/duplicated: {begin}")
    stop = prod.index(end, start)
    return prod[start:stop]


def check_main_t5_ingress(source: str) -> None:
    """Source-level guard only: default physical T5 MUST cross Zig ABI v2."""
    if '#[cfg(feature = "zig-transport")]\nmod zig_transport;' not in source:
        raise CorridorBlocked("sens main lacks default feature-gated Zig bridge")
    ingress = _route_between(source, "fn decode_physical_t5_words(", "\nfn eval_physical_t5(")
    positive = '#[cfg(feature = "zig-transport")]'
    negative = '#[cfg(not(feature = "zig-transport"))]'
    if ingress.count(positive) != 1 or ingress.count(negative) != 1:
        raise CorridorBlocked("sens main T5 ingress missing separate feature gates")
    zig, reference = ingress.split(negative, 1)
    # A symbol mentioned only in a Rust comment does not cross Zig.
    # Require the real return call on the default-feature ingress path.
    active_zig = re.sub(r"/\*.*?\*/|//[^\n]*", "", zig, flags=re.S)
    if not re.search(
        r"(?m)^\s*return\s+zig_transport::decode_t5_words\s*\(\s*bytes\s*\)\s*;",
        active_zig,
    ):
        raise CorridorBlocked("sens main default physical .sens lacks live Zig return")
    if "sens::decode_ternary_words" in ingress or "PhysicalT5Program::decode(" in ingress:
        raise CorridorBlocked("sens main T5 ingress has Rust physical fallback")
    if "no Rust fallback" not in reference and "requires the Zig transport" not in reference:
        raise CorridorBlocked("sens main must refuse physical .sens without Zig")
    eval_route = _route_between(source, "fn eval_physical_t5(", "\nfn main() {")
    if "decode_physical_t5_words(bytes)?" not in eval_route:
        raise CorridorBlocked("sens main eval bypasses Zig physical ingress")
    if "sens::parse_canonical_word_sequence(&words)" not in eval_route:
        raise CorridorBlocked("sens main eval must admit exact words via SENS D2")
    entry = _route_between(source, "fn main() {", "\n#[cfg(test)]")
    if "physical_t5_request" not in entry or "eval_physical_t5" not in entry:
        raise CorridorBlocked("sens main must dispatch physical .sens before Lisp")


def check_trit_t5_egress(source: str) -> None:
    """Default CLI source egress must be SENS exact words -> Zig T5, not Rust T5."""
    helper = _route_between(source, "fn admitted_source_words(", "\nfn read_sens(")
    if ("sens::parse_binary_source_words(source)" not in helper
            or "sens::parse_canonical_word_sequence(&words)" not in helper):
        raise CorridorBlocked("sens-trit source admission bypasses SENS exact D2 reader")
    if ("sens::encode_binary_projection_ternary(" in helper
            or "sens::decode_ternary_words(" in helper):
        raise CorridorBlocked("sens-trit exact source helper creates Rust physical T5")

    encode = _route_between(
        source, '\n        "encode" => {\n', '\n        "open" | "view" => {\n'
    )
    feature = '#[cfg(feature = "zig-transport")]'
    reference = '#[cfg(not(feature = "zig-transport"))]'
    if encode.count(feature) != 1 or encode.count(reference) != 1:
        raise CorridorBlocked("sens-trit encode missing exclusive Zig/reference feature gates")
    zig, rust = encode.split(reference, 1)
    required = "let bytes = zig_transport::encode_t5_direct(&admitted_source_words(&projection)?)?;"
    # Comments are NOT executable Rust; an inactive breadcrumb must not prove
    # that a real Zig ABI v2 call produced the bytes sent to the SENS CLI.
    active_zig = re.sub(r"/\\*.*?\\*/|//[^\\n]*", "", zig, flags=re.S)
    if not re.search(r"(?m)^[ \\t]*" + re.escape(required) + r"[ \\t]*$", active_zig):
        raise CorridorBlocked("sens-trit default encode lacks live Zig physical T5 egress")
    for bypass in ("sens::encode_binary_projection_ternary(", "sens::encode_ternary_words(",
                   "sens::decode_ternary_words(", "PhysicalT5Program::decode("):
        if bypass in zig:
            raise CorridorBlocked(f"sens-trit default encode calls Rust codec: {bypass}")
    if "let bytes = sens::encode_binary_projection_ternary(&projection)" not in rust:
        raise CorridorBlocked("sens-trit explicit Rust reference encoding lost its feature gate")
    if "verify_companion(&projection, &bytes)" not in rust:
        raise CorridorBlocked("sens-trit encode no longer verifies Zig carrier")

    companion = _route_between(source, "fn verify_companion(", "\n/// Run the explicitly")
    required_companion = (
        'let expected_words = admitted_source_words(source)?;',
        'if decoded != expected_words',
        'zig_transport::encode_t5(&expected_words, binary)',
    )
    if any(fragment not in companion for fragment in required_companion):
        raise CorridorBlocked("sens-trit companion no longer replays Zig bytes and SENS words")
    if companion.count(reference) < 1:
        raise CorridorBlocked("sens-trit companion must isolate Rust reference mode")
    companion_zig, companion_reference = companion.split(reference, 1)
    if ('let expected_words = admitted_source_words(source)?;' not in companion_zig
            or "sens::encode_binary_projection_ternary(" in companion_zig):
        raise CorridorBlocked("sens-trit default companion uses Rust physical T5 instead of SENS")
    if "let reference = sens::encode_binary_projection_ternary(source)" not in companion_reference:
        raise CorridorBlocked("sens-trit companion Rust reference is not explicitly isolated")


def check_trit_e1_egress(source: str) -> None:
    """One E1 physical export MUST be Zig->SENS-owned admission->Zig."""
    route = _route_between(source, "\nfn encode_e1_from_t5(", "\nfn eval_e1_bytes(")
    negative = '#[cfg(not(feature = "zig-transport"))]'
    positive = '#[cfg(feature = "zig-transport")]'
    if route.count(negative) != 1 or route.count(positive) != 1:
        raise CorridorBlocked("sens-trit E1 physical export lacks exact Zig feature gates")
    fail, active = route.split(positive, 1)
    if negative not in fail or "no Rust fallback" not in fail:
        raise CorridorBlocked("sens-trit E1 feature-negative must refuse before decoding")
    if "decode_canonical_t5_words(physical_t5)" in fail:
        raise CorridorBlocked("sens-trit E1 decodes in Rust before refusing missing Zig")
    if ("decode_canonical_t5_words(physical_t5)" not in active
            or "zig_transport::encode_e1_direct(&words)" not in active):
        raise CorridorBlocked("sens-trit E1 missing Zig ingress or physical egress")
    if "sens::envelope_e1::encode(" in route or "sens::decode_ternary_words(" in route:
        raise CorridorBlocked("sens-trit E1 uses direct Rust physical codec")
    arm = _route_between(source, '\n        "encode-e1" => {\n',
                         '\n        "eval-e1" => {\n')
    if "encode_e1_from_t5(&bytes)?" not in arm:
        raise CorridorBlocked("sens-trit encode-e1 command bypasses guarded Zig helper")


def check_trit_e1_ingress(source: str) -> None:
    """The live eval-e1 command must use Zig physical decoding, then SENS D2."""
    route = _route_between(source, "\nfn eval_e1_bytes(", "\nfn read_explicit_f3(")
    negative = '#[cfg(not(feature = "zig-transport"))]'
    positive = '#[cfg(feature = "zig-transport")]'
    if route.count(negative) != 1 or route.count(positive) != 1:
        raise CorridorBlocked("sens-trit E1 ingress missing exclusive feature gates")
    fail, active = route.split(positive, 1)
    if (negative not in fail or "no Rust fallback" not in fail
            or "decode_e1_words(" in fail):
        raise CorridorBlocked("sens-trit E1 feature-negative must refuse before decoding")
    if ("zig_transport::decode_e1_words(bytes)" not in active
            or "sens::PhysicalT5Program::from_exact_words(&words)" not in active
            or "program.execute(&mut session)" not in active):
        raise CorridorBlocked("sens-trit E1 bypasses Zig physical reader or SENS D2/eval")
    if "sens::eval_e1_program(" in route or "sens::envelope_e1::decode(" in route:
        raise CorridorBlocked("sens-trit E1 uses direct Rust physical decoder")
    arm = _route_between(source, '\n        "eval-e1" => {\n',
                         '\n        "encode-f3" =>')
    if "eval_e1_bytes(&e1)?" not in arm or "sens::eval_e1_program(" in arm:
        raise CorridorBlocked("live eval-e1 command bypasses guarded Zig ingress")


def check_trit_t5_execution(source: str) -> None:
    """Live eval/eval-core4 execution may only receive physical T5 from Zig."""
    route = _route_between(source, "\nfn eval_t5_bytes_core4(",
                           "\n/// Пояснити негативний результат")
    off = '#[cfg(not(feature = "zig-transport"))]'
    on = '#[cfg(feature = "zig-transport")]'
    if route.count(off) != 1 or route.count(on) != 1:
        raise CorridorBlocked("sens-trit T5 execution missing exclusive Zig gates")
    denied, active = route.split(on, 1)
    if (off not in denied or "no Rust fallback" not in denied
            or "let _ = (bytes, bootstrap_core);" not in denied):
        raise CorridorBlocked("sens-trit no-Zig T5 execution must refuse first")
    if ("zig_transport::decode_t5_words(bytes)?" not in active
            or "sens::PhysicalT5Program::from_exact_words(&words)" not in active
            or "program.execute(&mut session)" not in active):
        raise CorridorBlocked("sens-trit T5 execution bypasses Zig or SENS admission")
    if ("sens::PhysicalT5Program::decode(bytes)" in route
            or "sens::decode_ternary_words(bytes)" in route
            or "sens::eval_t5_program(" in route):
        raise CorridorBlocked("sens-trit T5 execution contains Rust physical codec")
    arm = _route_between(source, '\n        "eval" | "eval-core4" => {\n',
                         '\n        "encode-e1" => {\n')
    if ('eval_t5_bytes_core4(&bytes, true)?' not in arm
            or 'eval_t5_bytes(&bytes)?' not in arm):
        raise CorridorBlocked("live eval/eval-core4 command bypasses Zig-gated execution")


def check_f3c_validate_before_no_savings(body: str) -> None:
    """F3C no-savings must never bypass Zig physical T5 validation.

    Production encode_f3 must call validate_t5 before any length-based Ok(None).
    A carrier that is oversize but invalid must fail closed, not report None.
    """
    prod = _production_source(body)
    begin = "pub fn encode_f3("
    end = "pub fn decode_f3("
    if begin not in prod or prod.count(begin) != 1:
        raise CorridorBlocked("zig_transport.rs missing unique encode_f3")
    start = prod.index(begin) + len(begin)
    if end not in prod[start:]:
        raise CorridorBlocked("zig_transport.rs encode_f3 route not bounded")
    route = prod[start:prod.index(end, start)]
    if "validate_t5(t5)?" not in route and "validate_t5(t5)" not in route:
        raise CorridorBlocked(
            "encode_f3 must call validate_t5 before any no-savings decision"
        )
    val_at = route.find("validate_t5")
    len_at = route.find("t5.len() > 16")
    if len_at != -1 and (val_at == -1 or val_at > len_at):
        raise CorridorBlocked(
            "encode_f3 length-based Ok(None) must not precede Zig T5 validate"
        )
    if "sens_zig_f3c_pack" not in route:
        raise CorridorBlocked("encode_f3 must call Zig F3C pack FFI")
    if "ternary_transport" in route or "PhysicalT5Program" in route:
        raise CorridorBlocked("encode_f3 must not embed Rust physical T5 codec")


def check_f3c_decode_validates_t5(body: str) -> None:
    """decode_f3 must re-enter Zig T5 validate on recovered bytes.

    Unpacked F3C is still physical T5; without validate the host could admit
    a corrupted carrier into SENS. Fail closed: validate_t5 after unpack.
    """
    prod = _production_source(body)
    begin = "pub fn decode_f3("
    if begin not in prod or prod.count(begin) != 1:
        raise CorridorBlocked("zig_transport.rs missing unique decode_f3")
    start = prod.index(begin) + len(begin)
    rest = prod[start:]
    stop = len(rest)
    for m in ("\n#[cfg(test)]", "\npub fn "):
        i = rest.find(m)
        if i != -1 and 0 < i < stop:
            stop = i
    route = rest[:stop]
    active = re.sub(r"/\*.*?\*/|//[^\n]*", "", route, flags=re.S)
    validation = re.search(
        r"(?m)^[ \t]*validate_t5[ \t]*\([ \t]*&output[ \t]*\)[ \t]*\?[ \t]*;",
        active,
    )
    unpack_at = active.find("sens_zig_f3c_unpack")
    truncate_at = active.find("output.truncate(len as usize);")
    return_at = active.find("Ok(output)")
    if (validation is None or unpack_at < 0 or truncate_at < 0 or return_at < 0
            or not (unpack_at < truncate_at < validation.start() < return_at)):
        raise CorridorBlocked(
            "decode_f3 must propagate Zig validate_t5(&output)? after unpack/truncate and before return"
        )


def check_f3c_bounds_reported_lengths(body: str) -> None:
    """encode_f3/decode_f3 must reject Zig overreported lengths before truncate.

    Positive FFI return codes larger than the caller buffer must not become
    Vec::truncate arguments. Same fail-closed pattern as E1 capacity filter.
    """
    prod = _production_source(body)
    for name, markers in (
        (
            "encode_f3",
            ("usize::try_from(len)", "n <= bytes.len()", "n < t5.len()"),
        ),
        (
            "decode_f3",
            ("usize::try_from(len)", "n <= output.len()"),
        ),
    ):
        begin = f"pub fn {name}("
        if begin not in prod or prod.count(begin) != 1:
            raise CorridorBlocked(f"zig_transport.rs missing unique {name}")
        start = prod.index(begin) + len(begin)
        rest = prod[start:]
        stop = len(rest)
        for m in ("\n#[cfg(test)]", "\npub fn "):
            i = rest.find(m)
            if i != -1 and 0 < i < stop:
                stop = i
        route = rest[:stop]
        for marker in markers:
            if marker not in route:
                raise CorridorBlocked(
                    f"{name} must bound Zig-reported length before truncate ({marker})"
                )
        if "truncate(len as usize)" not in route and "truncate(len as" not in route:
            raise CorridorBlocked(f"{name} must truncate only after capacity filter")


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

    check_f3c_validate_before_no_savings(body)
    notes.append("f3c-validate-before-no-savings")
    check_f3c_decode_validates_t5(body)
    notes.append("f3c-decode-validates-t5")
    check_f3c_bounds_reported_lengths(body)
    notes.append("f3c-bounds-reported-lengths")

    abi = ABI.read_text(encoding="utf-8")
    for name in ("sens_zig_t5_encode_be3", "sens_zig_t5_decode_be3"):
        if f"pub export fn {name}" not in abi:
            raise CorridorBlocked(f"transport_abi.zig missing export {name}")
    if "pub export fn sens_zig_e1_encode_be3" in abi and "pub export fn sens_zig_e1_decode_be3" not in abi:
        raise CorridorBlocked("transport_abi.zig exports E1 encode without decode")
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
    check_trit_t5_egress(trit)
    notes.append("sens-trit-zig-only-egress")
    check_trit_t5_execution(trit)
    notes.append("sens-trit-zig-only-t5-execution")
    check_trit_e1_egress(trit)
    notes.append("sens-trit-zig-only-e1-egress")
    check_trit_e1_ingress(trit)
    if ("sens_zig_e1_decode_be3" not in body or "pub fn decode_e1_words(" not in body
            or "pub export fn sens_zig_e1_decode_be3" not in abi):
        raise CorridorBlocked("E1 Zig ingress missing ABI export or Rust host shim")
    notes.append("sens-trit-zig-only-e1-ingress")

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
