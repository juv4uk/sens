#!/usr/bin/env python3
"""Guard: the Rust<->SENS link may cross ONLY the sterile Zig corridor (#5777/#5779).

Fail-closed STRUCTURAL checker. It does not run cargo or Zig; it asserts the
invariants that make the corridor un-bypassable, so a later change cannot turn
the Rust host into a silent physical codec again:

R1  crates/sens-cli/Cargo.toml: `default` features include `zig-transport`
R2  crates/sens-cli/build.rs: gated on CARGO_FEATURE_ZIG_TRANSPORT, links Zig
R3  transport_abi.zig: physical sens_zig_* only; T5/F3C/E1 modules
R3b If E1 encode is exported, E1 decode must be exported too
R4  `.zig-version` concrete
R5  zig_transport.rs: FFI + packed_bits/BitN; E1 encode implies decode
R6  main.rs and sens-trit route physical T5 through zig_transport

Exit 0 = CORRIDOR_OK; exit 1 = CORRIDOR_BLOCKED.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CARGO = "crates/sens-cli/Cargo.toml"
BUILD = "crates/sens-cli/build.rs"
ABI = "research/zig-codecs/transport_abi.zig"
ZIGVER = ".zig-version"
ZIG_CLIENT = "crates/sens-cli/src/zig_transport.rs"
MAIN_RS = "crates/sens-cli/src/main.rs"
TRIT_RS = "crates/sens-cli/src/bin/sens-trit.rs"

ALLOWED_IMPORTS = {
    "std",
    "t5/t5.zig",
    "f3c/f3c.zig",
    "transport/e1.zig",
    "transport/e1_writer.zig",
}
REQUIRED_ABI_EXPORTS = (
    "sens_zig_t5_validate",
    "sens_zig_t5_encode_be3",
    "sens_zig_t5_decode_be3",
)



def _single_route(source: str, begin: str, end: str) -> str | None:
    """Extract exactly one physical Rust function body, not test/comment markers."""
    if source.count(begin) != 1 or source.count(end) != 1:
        return None
    start = source.index(begin) + len(begin)
    stop = source.index(end, start)
    return source[start:stop]


def _audit_main_physical_route(source: str) -> list[str]:
    """R6 source-only: actual Zig BE3 ingress -> SENS D2 -> CLI .sens dispatch."""
    problems: list[str] = []
    if '#[cfg(feature = "zig-transport")]\nmod zig_transport;' not in source:
        problems.append("R6: main lacks feature-gated Zig physical client")

    ingress = _single_route(source, "fn decode_physical_t5_words(", "\nfn eval_physical_t5(")
    evaluation = _single_route(source, "fn eval_physical_t5(", "\nfn main() {")
    dispatch = _single_route(source, "fn main() {", "\n#[cfg(test)]")
    if ingress is None or evaluation is None or dispatch is None:
        return problems + ["R6: physical CLI entrypoint missing or duplicated"]

    zig_gate = '#[cfg(feature = "zig-transport")]'
    no_zig_gate = '#[cfg(not(feature = "zig-transport"))]'
    if ingress.count(zig_gate) != 1 or ingress.count(no_zig_gate) != 1:
        problems.append("R6: physical ingress needs Zig and reference feature gates")
    else:
        zig_part, no_zig_part = ingress.split(no_zig_gate, 1)
        if not re.search(
            r'(?m)^\s*return zig_transport::decode_t5_words\(bytes\);\s*$',
            zig_part,
        ):
            problems.append("R6: live default ingress fails to return Zig BE3 words")
        if not re.search(
            r'Err\("physical \.sens requires the Zig transport corridor; '
            r'no Rust fallback"\.into\(\)\)',
            no_zig_part,
        ):
            problems.append("R6: feature-negative physical ingress must refuse Rust fallback")

    if any(token in ingress + evaluation for token in (
        "sens::decode_ternary_words(", "PhysicalT5Program::decode("
    )):
        problems.append("R6: physical CLI route contains a Rust T5 decoder")
    if "let words = decode_physical_t5_words(bytes)?;" not in evaluation:
        problems.append("R6: evaluator bypasses Zig physical ingress")
    if "sens::parse_canonical_word_sequence(&words)" not in evaluation:
        problems.append("R6: evaluator bypasses canonical SENS D2 reader")
    if ("physical_t5_request(&raw_args)" not in dispatch or
            ".and_then(|bytes| eval_physical_t5(&bytes))" not in dispatch):
        problems.append("R6: CLI .sens dispatch bypasses guarded evaluator")
    return problems


def check(root: Path) -> list[str]:
    problems: list[str] = []

    cargo = (root / CARGO).read_text(encoding="utf-8")
    build = (root / BUILD).read_text(encoding="utf-8")
    abi = (root / ABI).read_text(encoding="utf-8")
    zigver = (root / ZIGVER).read_text(encoding="utf-8").strip()

    features = re.search(r"\[features\](.*?)(?:\n\[|\Z)", cargo, re.S)
    feat_body = features.group(1) if features else ""
    default_match = re.search(r"^\s*default\s*=\s*\[([^\]]*)\]", feat_body, re.M)
    default_list = default_match.group(1) if default_match else ""
    if '"zig-transport"' not in default_list:
        problems.append(
            "R1: crates/sens-cli `default` features must include \"zig-transport\" "
            "(the Zig corridor must be ON by default)"
        )
    if not re.search(r"^\s*zig-transport\s*=", feat_body, re.M):
        problems.append("R1: `zig-transport` feature is not declared in crates/sens-cli/Cargo.toml")

    if "CARGO_FEATURE_ZIG_TRANSPORT" not in build:
        problems.append(
            "R2: build.rs does not gate on CARGO_FEATURE_ZIG_TRANSPORT "
            "(the Rust host could bypass the corridor)"
        )
    if "sens_zig_transport" not in build:
        problems.append("R2: build.rs does not link the Zig transport (`sens_zig_transport`)")
    if "transport_abi.zig" not in build:
        problems.append("R2: build.rs does not compile research/zig-codecs/transport_abi.zig")
    if ".zig-version" not in build:
        problems.append("R2: build.rs does not pin/read the repository `.zig-version`")

    exports = re.findall(r"pub export fn\s+([A-Za-z0-9_]+)", abi)
    if not exports:
        problems.append("R3: transport_abi.zig exports no `pub export fn` (no corridor ABI)")
    for name in exports:
        if not name.startswith("sens_zig_"):
            problems.append(
                f"R3: ABI export `{name}` is outside the physical `sens_zig_*` namespace"
            )
    for required in REQUIRED_ABI_EXPORTS:
        if required not in exports:
            problems.append(f"R3: corridor ABI is missing the physical op `{required}`")
    for imported in re.findall(r'@import\("([^"]+)"\)', abi):
        if imported not in ALLOWED_IMPORTS:
            problems.append(
                f"R3: ABI imports `{imported}` -- only physical modules "
                f"{sorted(ALLOWED_IMPORTS)} may cross the corridor"
            )
    if re.search(r"\bextern\b", abi):
        problems.append(
            "R3: ABI declares `extern`/host struct -- the corridor must use "
            "caller-owned triplets, no padded host structs"
        )

    if "sens_zig_e1_encode_be3" in exports and "sens_zig_e1_decode_be3" not in exports:
        problems.append(
            "R3: E1 encode is exported without sens_zig_e1_decode_be3 "
            "(Rust must not be the only E1 decoder)"
        )

    if not re.fullmatch(r"\d+\.\d+\.\d+", zigver):
        problems.append(f"R4: `.zig-version` is not a concrete version string: {zigver!r}")

    client_path = root / ZIG_CLIENT
    if not client_path.is_file() or client_path.is_symlink():
        problems.append(f"R5: missing regular sterile client {ZIG_CLIENT}")
    else:
        client = client_path.read_text(encoding="utf-8")
        for name in REQUIRED_ABI_EXPORTS:
            if name not in client:
                problems.append(f"R5: zig_transport.rs missing FFI binding for {name}")
        if "packed_bits" not in client or "BinarySourceWord::W1" not in client:
            problems.append(
                "R5: zig_transport.rs must reconstruct BinarySourceWord via "
                "packed_bits + BitN::new (W1..W9)"
            )
        banned = ("ternary_transport", "PhysicalT5Program", "from_width_bits", "TRITS_BY_BYTE")
        for token in banned:
            if token in client:
                problems.append(
                    f"R5: zig_transport.rs must not embed local codec marker `{token}`"
                )
        if "encode_e1_direct" in client and "decode_e1_words" not in client:
            problems.append(
                "R5: zig_transport.rs exports E1 encode without decode_e1_words"
            )
        if "sens_zig_e1_encode_be3" in client and "sens_zig_e1_decode_be3" not in client:
            problems.append(
                "R5: zig_transport.rs binds E1 encode FFI without decode FFI"
            )

    main_rs = root / MAIN_RS
    trit_rs = root / TRIT_RS
    if main_rs.is_file():
        main_src = main_rs.read_text(encoding="utf-8")
        if "zig_transport::decode_t5_words" not in main_src:
            problems.append(
                "R6: main.rs must decode physical .sens via zig_transport::decode_t5_words"
            )
        if "mod zig_transport" not in main_src:
            problems.append("R6: main.rs must declare the shared zig_transport module")
    else:
        problems.append(f"R6: missing {MAIN_RS}")
    if trit_rs.is_file():
        trit_src = trit_rs.read_text(encoding="utf-8")
        if "zig_transport.rs" not in trit_src:
            problems.append("R6: sens-trit.rs must path-include zig_transport.rs")
        if "zig_transport::" not in trit_src:
            problems.append("R6: sens-trit.rs must call zig_transport corridor API")
        if "fn sens_zig_t5_encode_be3" in trit_src:
            problems.append("R6: sens-trit.rs must not embed local Zig FFI (use shared client)")
    else:
        problems.append(f"R6: missing {TRIT_RS}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    problems = check(root)
    if problems:
        print("CORRIDOR_BLOCKED:", file=sys.stderr)
        for item in problems:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print(
        "CORRIDOR_OK Rust<->SENS crosses only the sterile Zig corridor "
        "(default zig-transport, no silent fallback, physical-only ABI)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
