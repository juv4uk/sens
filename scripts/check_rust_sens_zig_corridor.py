#!/usr/bin/env python3
"""Guard: the Rust<->SENS link may cross ONLY the sterile Zig corridor (#5777/#5779).

Fail-closed STRUCTURAL checker. It does not run cargo or Zig; it asserts the
invariants that make the corridor un-bypassable, so a later change cannot turn
the Rust host into a silent physical codec again:

R1  crates/sens-cli/Cargo.toml: `default` features include `zig-transport`
    (the corridor is ON by default) and the `zig-transport` feature exists.
R2  crates/sens-cli/build.rs: the Zig transport is gated on
    CARGO_FEATURE_ZIG_TRANSPORT, links `sens_zig_transport`, compiles
    research/zig-codecs/transport_abi.zig, and pins/reads `.zig-version`.
R3  research/zig-codecs/transport_abi.zig: exports ONLY physical `sens_zig_*`
    functions (including the T5 ingress/egress), imports ONLY physical modules
    (`std`, `t5/t5.zig`, `f3c/f3c.zig`, `transport/e1.zig`, `transport/e1_writer.zig`)
    and never a registry/host/semantic module, and declares no `extern`/host struct.
R4  `.zig-version` is a concrete version string (toolchain identity, not
    semantic authority).
R5  `crates/sens-cli/src/zig_transport.rs` is the shared sterile client:
    FFI-only `sens_zig_*`, reconstructs W1..W9 via `packed_bits` + `BitN::new`,
    never a local T5 algorithm (`ternary_transport` / `from_width_bits`).
R6  `main.rs` and `sens-trit.rs` route physical T5 through `zig_transport::`
    under the default feature (no silent Rust physical codec on that path).

The Rust-only build must stay an EXPLICIT `--no-default-features` choice, never
a silent fallback. Exit 0 = CORRIDOR_OK; exit 1 = CORRIDOR_BLOCKED with reasons.
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


def check(root: Path) -> list[str]:
    problems: list[str] = []

    cargo = (root / CARGO).read_text(encoding="utf-8")
    build = (root / BUILD).read_text(encoding="utf-8")
    abi = (root / ABI).read_text(encoding="utf-8")
    zigver = (root / ZIGVER).read_text(encoding="utf-8").strip()

    # R1 -- corridor is ON by default, feature declared.
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

    # R2 -- build.rs requires the Zig corridor; no silent Rust transport.
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

    # R3 -- the corridor ABI is physical-only and semantics-free.
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

    # R4 -- pinned corridor version.
    if not re.fullmatch(r"\d+\.\d+\.\d+", zigver):
        problems.append(f"R4: `.zig-version` is not a concrete version string: {zigver!r}")

    # R5 -- shared sterile Rust client (one turnstile, no local T5 codec).
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

    # R6 -- production CLI physical path crosses the sterile client only.
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
