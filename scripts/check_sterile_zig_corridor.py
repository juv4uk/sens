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
F3C_ZIG = ROOT / "research" / "zig-codecs" / "f3c" / "f3c.zig"
ROOT_ZIG = ROOT / "zig_transport_root.zig"

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


def check_zig_abi_v2_live_exports(source: str) -> None:
    """Only real Zig C-ABI exports count; comments and Rust externs are not proof.

    This checks the mechanical symbol corridor, not SENS semantic admission.
    """
    live = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    for name in REQUIRED_FFI:
        declaration = re.compile(
            r"(?m)^\s*pub\s+export\s+fn\s+" + re.escape(name) + r"\s*\("
        )
        if len(declaration.findall(live)) != 1:
            raise CorridorBlocked(
                f"transport_abi.zig missing/duplicated live Zig ABI v2 export {name}"
            )
    # An ABI mismatch cannot be treated as an alternate physical profile.
    if not re.search(
        r"\bpub\s+export\s+fn\s+sens_zig_codec_abi_version"
        r"\s*\(\s*\)\s*u32\s*\{\s*return\s+2\s*;\s*\}",
        live,
    ):
        raise CorridorBlocked("transport_abi.zig ABI version must return 2")


def check_default_zig_build_gate(build: str) -> None:
    """R2: the default Rust host cannot silently return before compiling Zig.

    Inspect active Rust code, not the feature name merely appearing in a
    comment. This checks one mechanical build route, not SENS semantics.
    """
    active = re.sub(r"/\*.*?\*/|//[^\n]*", "", build, flags=re.S)
    gate = re.compile(
        r'\bif\s+env::var_os\(\s*"CARGO_FEATURE_ZIG_TRANSPORT"\s*\)'
        r'\s*\.is_none\(\)\s*\{\s*return\s*;\s*\}',
        re.S,
    )
    if len(gate.findall(active)) != 1:
        raise CorridorBlocked(
            "build.rs default Zig gate must skip only when feature is absent "
            "(CARGO_FEATURE_ZIG_TRANSPORT.is_none); no reversed or comment-only gate"
        )


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
    """Live SENS exact words -> Zig T5; no Rust physical reference fallback."""
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
    nozig = '#[cfg(not(feature = "zig-transport"))]'
    if encode.count(feature) != 1 or encode.count(nozig) != 1:
        raise CorridorBlocked("sens-trit encode missing exclusive Zig/no-Zig feature gates")
    zig, refused = encode.split(nozig, 1)
    required = "let bytes = zig_transport::encode_t5_direct(&admitted_source_words(&projection)?)?;"
    live_zig = re.sub(r"/\*.*?\*/|//[^\n]*", "", zig, flags=re.S)
    if not re.search(r"(?m)^[ \t]*" + re.escape(required) + r"[ \t]*$", live_zig):
        raise CorridorBlocked("sens-trit default encode lacks live Zig physical T5 egress")
    live_encode = re.sub(r"/\*.*?\*/|//[^\n]*", "", encode, flags=re.S)
    for bypass in ("sens::encode_binary_projection_ternary(", "sens::encode_ternary_words(",
                   "sens::decode_ternary_words(", "PhysicalT5Program::decode("):
        if bypass in live_encode:
            raise CorridorBlocked(f"sens-trit encode contains Rust physical bypass: {bypass}")
    if not re.search(
        r'let bytes\s*=\s*Err::<Vec<u8>, String>\(\s*'
        r'"RUST_ZIG_ONLY:[^"]*no Rust fallback"\.into\(\)\s*\)\s*\?;',
        re.sub(r"/\*.*?\*/|//[^\n]*", "", refused, flags=re.S),
        re.S,
    ):
        raise CorridorBlocked("sens-trit no-Zig encode must refuse, never reference-encode")
    if "verify_companion(&projection, &bytes)" not in refused:
        raise CorridorBlocked("sens-trit encode no longer verifies Zig carrier")

    companion = _route_between(source, "fn verify_companion(", "\n/// Run the explicitly")
    if companion.count(nozig) != 1 or companion.count(feature) != 1:
        raise CorridorBlocked("sens-trit companion needs exclusive fail-closed Zig gates")
    denied, zig_companion = companion.split(feature, 1)
    denied = re.sub(r"/\*.*?\*/|//[^\n]*", "", denied, flags=re.S)
    zig_companion = re.sub(r"/\*.*?\*/|//[^\n]*", "", zig_companion, flags=re.S)
    if nozig not in denied or not re.search(
        r'return Err\("RUST_ZIG_ONLY:[^"]*no Rust fallback"\.into\(\)\)',
        denied,
    ):
        raise CorridorBlocked("sens-trit companion no-Zig path must refuse before parsing")
    for bypass in ("sens::encode_binary_projection_ternary(",
                   "sens::decode_ternary_words(", "sens::encode_ternary_words("):
        if bypass in denied or bypass in zig_companion:
            raise CorridorBlocked(f"sens-trit companion contains Rust physical bypass: {bypass}")
    for required_companion in (
        "let expected_words = admitted_source_words(source)?;",
        "if decoded != expected_words",
        "zig_transport::encode_t5(&expected_words, binary)",
    ):
        if required_companion not in zig_companion:
            raise CorridorBlocked("sens-trit companion no longer checks SENS words and Zig bytes")

    # Entry gate must reject a Zig-less command BEFORE filesystem access.
    gate = _route_between(source, "fn require_zig_transport(", "\nfn execute()")
    entry = _route_between(source, "fn execute() -> Result<(), String> {", "\nfn main()")
    if ("RUST_ZIG_ONLY:" not in gate
            or 'command != "backend"' not in gate
            or "require_zig_transport(command)?;" not in entry
            or entry.index("require_zig_transport(command)?;") > entry.index("match command {")):
        raise CorridorBlocked("sens-trit Zig-less physical CLI must refuse before I/O")


def check_trit_explain_typed_word_route(source: str) -> None:
    """The real Zig T5 ingress must feed SENS typed words, never a text reparse."""
    route = _route_between(
        source, "fn explain_t5_bytes(", "\nfn require_zig_transport("
    )
    live = re.sub(r"/\*.*?\*/|//[^\n]*", "", route, flags=re.S)
    zig_marker = '#[cfg(feature = "zig-transport")]'
    if live.count(zig_marker) != 1:
        raise CorridorBlocked("sens-trit explain missing sole Zig physical branch")
    active = live.split(zig_marker, 1)[1]
    if "zig_transport::decode_t5_words(bytes)" not in active:
        raise CorridorBlocked("sens-trit explain bypasses physical Zig T5 ingress")
    if "sens::parse_canonical_word_sequence(&words)" not in active:
        raise CorridorBlocked("sens-trit explain does not admit exact SENS words")
    for forbidden in (
        "sens::parse_canonical_binary(", "sens::render_ternary_words_vertical(",
        "sens::decode_ternary_words(", "sens::PhysicalT5Program::decode(",
    ):
        if forbidden in live:
            raise CorridorBlocked(f"sens-trit explain reinterprets T5: {forbidden}")
    if "no Rust fallback" not in live.split(zig_marker, 1)[0]:
        raise CorridorBlocked("sens-trit explain must refuse when Zig is missing")


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
                           "\nfn explain_t5_bytes(")
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


def check_trit_f3_no_rust_fallback(source: str) -> None:
    """F3C physical ingress/egress always goes through the Zig ABI.

    Unlike an explicit offline reference test, a CLI that can read/write
    physical F3C without Zig is a second production codec implementation.
    """
    route = _route_between(source, "fn decode_f3_carrier(", "\nfn sibling_sens(")
    marker = '    #[cfg(not(feature = "zig-transport"))]'
    if route.count(marker) != 2:
        raise CorridorBlocked("sens-trit F3C must gate both missing-Zig branches")
    ingress, egress = route.split("fn encode_f3_carrier(", 1)
    if ("zig_transport::decode_f3(bytes)?" not in ingress
            or "zig_transport::decode_t5_words(&restored)?" not in ingress
            or "return zig_transport::encode_f3(bytes);" not in egress
            or "zig_transport::decode_t5_words(bytes)?" not in egress):
        raise CorridorBlocked("sens-trit F3C ingress/egress bypasses Zig ABI")
    # Remove comments before source-level evidence; inert markers are no proof.
    live = re.sub(r"/\*.*?\*/|//[^\n]*", "", route, flags=re.S)
    if "sens::frame3_small::" in live:
        raise CorridorBlocked("sens-trit F3C retains a Rust physical codec fallback")
    segments = [ingress.split(marker, 1)[1], egress.split(marker, 1)[1]]
    for part, direction in zip(segments, ("decode", "encode")):
        # The entire no-Zig arm must unconditionally reject; a string
        # mentioning "no Rust fallback" beside a success return is insufficient.
        expected = (
            r'\s*\{\s*let _ = bytes;\s*Err\("F3C physical '
            + direction
            + r' requires Zig; no Rust fallback"\.into\(\)\)\s*\}\s*\}\s*'
        )
        if re.fullmatch(expected, part) is None:
            raise CorridorBlocked(f"sens-trit F3C {direction} no-Zig path not fail-closed")


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



def check_zig_f3c_semantic_firewall(source: str) -> None:
    """Only physical D2 structure in Zig; D3 callability belongs to SENS."""
    production = source.split('\ntest "', 1)[0]
    clean = re.sub(r"//[^\n]*", "", production)
    anchor = "const Parser = struct {"
    if clean.count(anchor) != 1:
        raise CorridorBlocked("F3C_SEMANTIC_FIREWALL missing unique Zig parser")
    tail = clean.split(anchor, 1)[1]
    if "\n};" not in tail:
        raise CorridorBlocked("F3C_SEMANTIC_FIREWALL unclosed Zig parser")
    parser = tail.split("\n};", 1)[0]
    banned = (
        r"\badmittedHead\b|\bargc\b|\barity\b|\bcallable\b",
        r"\b(?:QUOTE|ATOM|CAR|CDR|COND|CONS|EQ|NIL)\b",
        r"\.\s*(?:bits|packed_bits)\b",
        r"\bsame\s*\(\s*\w+\s*,\s*(?!2\b)\d",
    )
    if any(re.search(expr, parser) for expr in banned):
        raise CorridorBlocked("F3C_SEMANTIC_FIREWALL Zig D3 semantic dispatch")
    if re.search(r"\b(?:canonicalProgram|admittedHead)\s*\(", clean):
        raise CorridorBlocked("F3C_SEMANTIC_FIREWALL old semantic gate restored")
    if ("fn canonicalStructure(words: []const Word) bool {" not in clean or
            "!canonicalStructure(words)" not in clean or
            "if (!canonicalStructure(words)) return Error.InvalidProgram;" not in clean):
        raise CorridorBlocked("F3C_SEMANTIC_FIREWALL physical-only preflight removed")
    if ("std.mem.eql(u8, original_t5, recovered)" not in clean or
            "std.mem.eql(u8, canonical_f3, carrier)" not in clean):
        raise CorridorBlocked("F3C_SEMANTIC_FIREWALL physical byte replay removed")


def check_linter_zig_only(
    main_source: str, rust_corridor: str, zig_root: str, build: str,
) -> None:
    """Release regression: historical Lisp asset bytes ONLY cross Zig C ABI.

    This is a byte/provenance boundary, NOT SENS parsing, execution or domain
    admission. Inspect active code rather than comments or test-only witnesses.
    """
    def live(source: str) -> str:
        return re.sub(r"/\*.*?\*/|//[^\n]*", "", _production_source(source), flags=re.S)

    main = live(main_source)
    host = live(rust_corridor)
    root = live(zig_root)
    asset_module = ROOT / "crates/sens-cli/src/zig_transport_assets.rs"
    if not asset_module.is_file() or asset_module.is_symlink():
        raise CorridorBlocked("LINTER_ZIG_ONLY missing reviewed asset ABI module")
    asset_source = live(asset_module.read_text(encoding="utf-8"))
    if ('unsafe extern "C" {' not in asset_source or
            "pub(super) fn sens_zig_linter_bytes_copy(output: *mut u8, capacity: usize) -> isize;" not in asset_source):
        raise CorridorBlocked("LINTER_ZIG_ONLY missing declared Zig asset ABI")
    if (re.search(r'include_(?:str|bytes)!\s*\(\s*"[^"]*linter\.lisp"', main)
            or re.search(r'(?:fs|std::fs)::read(?:_to_string)?\s*\(\s*"[^"]*linter\.lisp"', main)):
        raise CorridorBlocked("LINTER_ZIG_ONLY Rust directly embeds or reads project Lisp")

    helper = _route_between(main_source, "fn linter_source_zig_only(", "\nfn contract_source_zig_only(")
    helper = live(helper)
    if (helper.count('#[cfg(feature = "zig-transport")]') != 1
            or helper.count('#[cfg(not(feature = "zig-transport"))]') != 1
            or "zig_transport::linter_source_bytes()?" not in helper
            or "String::from_utf8(bytes)" not in helper
            or "RUST_ZIG_ONLY: linter library requires Zig; no Rust project-source fallback" not in helper
            or "fs::read" in helper or "include_str!" in helper):
        raise CorridorBlocked("LINTER_ZIG_ONLY no live Zig-only source byte helper / fail-closed denial")
    if ('let linter_lib = match linter_source_zig_only()' not in main
            or "parse(&linter_lib)" not in main):
        raise CorridorBlocked("LINTER_ZIG_ONLY CLI bypassed Zig asset ingress or SENS parser")

    ffi = "sens_zig_linter_bytes_copy"
    linter_host = live(_route_between(
        rust_corridor, "pub fn linter_source_bytes(", "\n/// Exact opaque project contract"
    ))
    if (host.count(f"asset_ffi::{ffi}(") != 2
            or '#[path = "zig_transport_assets.rs"]' not in host
            or "version()?;" not in linter_host
            or "let copied = unsafe" not in linter_host
            or "if copied != required" not in linter_host
            or "Ok(bytes)" not in linter_host):
        raise CorridorBlocked("LINTER_ZIG_ONLY Rust lacks verified Zig ABI byte copy")

    if (root.count('const linter_asset = @embedFile("lib/linter.lisp");') != 1
            or f"pub export fn {ffi}(" not in root
            or "if (capacity == 0) return @intCast(linter_asset.len);" not in root
            or "if (capacity < linter_asset.len) return -2;" not in root
            or "@memcpy(dst[0..linter_asset.len], linter_asset[0..linter_asset.len]);" not in root):
        raise CorridorBlocked("LINTER_ZIG_ONLY Zig ABI must copy exact original bytes or reject before writing")
    if ('.arg("zig_transport_root.zig")' not in live(build)
            or "cargo:rerun-if-changed=../../lib/linter.lisp" not in build):
        raise CorridorBlocked("LINTER_ZIG_ONLY Cargo must build root Zig module and rebuild on source change")


def check_contract_zig_only(main_source: str, rust_corridor: str, zig_root: str, build: str) -> None:
    """Physical source bytes only; exact contract meaning remains SENS-owned."""
    def active(source: str) -> str:
        return re.sub(r"/\*.*?\*/|//[^\n]*", "", _production_source(source), flags=re.S)
    main = active(main_source)
    host = active(rust_corridor)
    root = active(zig_root)
    asset_source = active((ROOT / "crates/sens-cli/src/zig_transport_assets.rs").read_text(encoding="utf-8"))
    if ("pub(super) fn sens_zig_contract_bytes_copy(output: *mut u8, capacity: usize) -> isize;" not in asset_source):
        raise CorridorBlocked("CONTRACT_ZIG_ONLY missing declared Zig asset ABI")
    if re.search(r'include_(?:str|bytes)!\s*\(\s*"[^"]*language-contract\.lisp"', main):
        raise CorridorBlocked("CONTRACT_ZIG_ONLY direct Rust project contract embed")
    helper = active(_route_between(main_source, "fn contract_source_zig_only(", "\nfn main() {"))
    if (helper.count('#[cfg(feature = "zig-transport")]') != 1
            or helper.count('#[cfg(not(feature = "zig-transport"))]') != 1
            or "zig_transport::contract_source_bytes()?" not in helper
            or "String::from_utf8(bytes)" not in helper
            or "RUST_ZIG_ONLY: language contract requires Zig; no Rust source fallback" not in helper):
        raise CorridorBlocked("CONTRACT_ZIG_ONLY missing live Zig-only helper / fail-closed refusal")
    if ("let contract_source = match contract_source_zig_only()" not in main
            or 'let quoted = format!("(quote {contract_source})");' not in main):
        raise CorridorBlocked("CONTRACT_ZIG_ONLY main CLI bypassed Zig carrier or SENS quote")
    ffi = "sens_zig_contract_bytes_copy"
    contract_host = active(_route_between(
        rust_corridor, "pub fn contract_source_bytes(", "\nfn require_same_exact_words("
    ))
    if (host.count(f"asset_ffi::{ffi}(") != 2
            or '#[path = "zig_transport_assets.rs"]' not in host
            or "let copied = unsafe" not in contract_host
            or "if copied != required" not in contract_host
            or f"asset_ffi::{ffi}(bytes.as_mut_ptr(), bytes.len())" not in contract_host):
        raise CorridorBlocked("CONTRACT_ZIG_ONLY missing checked Rust FFI egress")
    if (root.count('const contract_asset = @embedFile("language-contract.lisp");') != 1
            or f"pub export fn {ffi}(" not in root
            or "if (capacity == 0) return @intCast(contract_asset.len);" not in root
            or "if (capacity < contract_asset.len) return -2;" not in root
            or "@memcpy(dst[0..contract_asset.len], contract_asset[0..contract_asset.len]);" not in root):
        raise CorridorBlocked("CONTRACT_ZIG_ONLY Zig source/capacity/memcpy bypass")
    if ('.arg("zig_transport_root.zig")' not in active(build)
            or "cargo:rerun-if-changed=../../language-contract.lisp" not in build):
        raise CorridorBlocked("CONTRACT_ZIG_ONLY stale Cargo ABI contract asset")


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

    if not F3C_ZIG.is_file() or F3C_ZIG.is_symlink():
        raise CorridorBlocked("F3C_SEMANTIC_FIREWALL missing regular f3c.zig")
    check_zig_f3c_semantic_firewall(F3C_ZIG.read_text(encoding="utf-8"))
    notes.append("f3c-physical-only-d2")

    abi = ABI.read_text(encoding="utf-8")
    check_zig_abi_v2_live_exports(abi)
    notes.append("abi-v2-all-live-exports")

    build = BUILD.read_text(encoding="utf-8")
    if "transport_abi.zig" not in build:
        raise CorridorBlocked("build.rs does not compile transport_abi.zig")
    check_default_zig_build_gate(build)
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
    check_trit_explain_typed_word_route(trit)
    notes.append("sens-trit-zig-typed-explain")
    check_trit_f3_no_rust_fallback(trit)
    notes.append("sens-trit-zig-only-f3c-ingress-egress")
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
    main_source = MAIN.read_text(encoding="utf-8")
    check_main_t5_ingress(main_source)
    notes.append("sens-cli-main-zig-only-ingress")
    if not ROOT_ZIG.is_file() or ROOT_ZIG.is_symlink():
        raise CorridorBlocked("LINTER_ZIG_ONLY missing regular repository-root Zig asset module")
    check_linter_zig_only(main_source, body, ROOT_ZIG.read_text(encoding="utf-8"), build)
    notes.append("linter-zig-only-byte-carrier")
    check_contract_zig_only(main_source, body, ROOT_ZIG.read_text(encoding="utf-8"), build)
    notes.append("contract-zig-only-byte-carrier")
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
