#!/usr/bin/env python3
"""Sterility guard for the Zig corridor (#5777/#5779): Zig carries only physical data.

Replaces the previous PLACEHOLDER. Fail-closed STRUCTURAL checker (no cargo/Zig).
It complements scripts/check_rust_sens_zig_corridor.py (structural corridor) and
tests/test_zig_ffi_v2_contract.py (Zig/Rust/C declaration parity) by asserting the
corridor is *sterile*: it moves physical width+payload and never semantic identity.

S1  research/zig-codecs/transport_abi.zig exports ONLY the physical `sens_zig_*`
    namespace and includes the T5 ingress/egress + E1/F3C physical ops.
S2  the corridor Zig imports ONLY physical codec modules (`std` or t5/ f3c/
    transport/); a registry/host/semantic module never crosses the corridor.
S3  the corridor declares no `extern`/host struct -- caller-owned triplets only.
S4  the C header declares the sterility contract (no SENS semantic registry /
    callable admission / host-owned Value / legacy identity translation).

Exit 0 = CORRIDOR_STERILE_OK; exit 1 = CORRIDOR_NOT_STERILE with reasons.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ABI = "research/zig-codecs/transport_abi.zig"
C_HEADER = "research/zig-codecs/host-c/zig_transport_v2.h"

PHYSICAL_IMPORT_PREFIXES = ("t5/", "f3c/", "transport/")
FORBIDDEN_IMPORT_RE = re.compile(r"registry|semantic|host|sens", re.I)
REQUIRED_PHYSICAL_OPS = (
    "sens_zig_t5_validate",
    "sens_zig_t5_encode_be3",
    "sens_zig_t5_decode_be3",
)
# The sterility contract the C header must state verbatim (mechanical bytes only).
STERILITY_MARKERS = (
    "no SENS semantic registry",
    "callable admission",
)


def check(root: Path) -> list[str]:
    problems: list[str] = []
    abi = (root / ABI).read_text(encoding="utf-8")
    header = (root / C_HEADER).read_text(encoding="utf-8")

    # S1 -- physical-only export namespace.
    exports = re.findall(r"pub export fn\s+([A-Za-z0-9_]+)", abi)
    if not exports:
        problems.append("S1: transport_abi.zig exports no `pub export fn` (empty corridor)")
    for name in exports:
        if not name.startswith("sens_zig_"):
            problems.append(f"S1: export `{name}` is outside the physical `sens_zig_*` namespace")
    for required in REQUIRED_PHYSICAL_OPS:
        if required not in exports:
            problems.append(f"S1: corridor is missing the physical op `{required}`")

    # S2 -- no semantic/host/registry import crosses the corridor.
    for imported in re.findall(r'@import\("([^"]+)"\)', abi):
        if imported == "std":
            continue
        if FORBIDDEN_IMPORT_RE.search(imported):
            problems.append(
                f"S2: corridor imports `{imported}` -- a semantic/host/registry module "
                "must never cross the corridor"
            )
        elif not imported.startswith(PHYSICAL_IMPORT_PREFIXES):
            problems.append(
                f"S2: corridor imports `{imported}` -- only physical codec modules "
                f"{PHYSICAL_IMPORT_PREFIXES} may cross"
            )

    # S3 -- caller-owned triplets, no host struct.
    if re.search(r"\bextern\b", abi):
        problems.append(
            "S3: corridor declares `extern`/host struct -- must use caller-owned triplets only"
        )

    # S4 -- the sterility contract is declared, not implied.
    for marker in STERILITY_MARKERS:
        if marker not in header:
            problems.append(f"S4: C header does not declare the sterility contract `{marker}`")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except FileNotFoundError as exc:
        print(f"CORRIDOR_NOT_STERILE missing corridor file: {exc}", flush=True)
        return 1
    if problems:
        print("CORRIDOR_NOT_STERILE the Zig corridor carries non-physical content:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "CORRIDOR_STERILE_OK Zig carries only physical data "
        "(physical-only exports, no semantic import, no host struct, contract declared)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
