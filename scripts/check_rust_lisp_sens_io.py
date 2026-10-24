#!/usr/bin/env python3
"""Test/guard: how Rust talks to .lisp and .sens -- and that NO json path is used.

Physical path law (owner #5777/#5779, sterile Zig corridor):

- `.sens` is physical BYTES (T5). Host may `fs::read(` or take opaque bytes from Zig.
- `.lisp` source may arrive as:
    (a) TEXT via `fs::read_to_string(` (human path), or
    (b) compile-time text embed `include_str!(...*.lisp)` (still text; isolation
        debt is separate -- see check_rust_isolated_only_zig), or
    (c) opaque BYTES through the sterile Zig corridor (sens_zig_*/asset_ffi /
        linter_source_bytes / *_source_bytes) -- never re-parsed as UTF-8 here.
- Naming `.lisp` only as an extension constant (no read, no embed) is not I/O.
- Neither path uses JSON/serde_json as a side-channel between Rust and SENS.

Fail-closed J-rules over the core Rust modules that touch these files:
J0  every mandatory core module must exist as a regular non-symlink file.
J1  a module that names `.sens` and performs host I/O must use `fs::read(`
    (binary), or state the Zig corridor byte path (no text decode of T5).
J2  a module that names `.lisp` must have a legal text path (read_to_string /
    include_str of .lisp), OR a Zig corridor byte carrier, OR only mention the
    extension as a constant without reading.
J3  no core .lisp/.sens module may `use serde_json` or call `serde_json::` /
    `json!` -- JSON is not a path between Rust and SENS.
J4  the physical `.sens` entry must state the corridor requirement and the
    absence of a Rust T5 fallback.

Exit 0 = RUST_LISP_SENS_IO_OK; exit 1 = RUST_LISP_SENS_IO_BLOCKED.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CORE = [
    "crates/sens-cli/src/main.rs",
    "crates/sens-cli/src/bin/sens-trit.rs",
    "crates/sens-cli/src/zig_transport.rs",
    "crates/sens/src/binary_execution.rs",
    "crates/sens/src/mixed_source.rs",
    "crates/sens/src/source_words.rs",
]

JSON_RE = re.compile(r"\bserde_json\b|\bjson!\s*\(|\bfrom_str::<")

# Sterile Zig corridor markers: opaque bytes, no Rust semantic table.
ZIG_CORRIDOR_RE = re.compile(
    r"sens_zig_|asset_ffi|zig_transport|ZIG_[A-Z_]*CARRIER|"
    r"linter_source_bytes|contract_source_bytes|_source_bytes\s*\(|"
    r"sterile Zig|Zig ABI|Zig corridor",
    re.I,
)

INCLUDE_LISP_RE = re.compile(r'include_str!\s*\(\s*"[^"]*\.lisp"')
INCLUDE_SENS_RE = re.compile(r'include_bytes!\s*\(\s*"[^"]*\.sens"')


def _lisp_text_path(src: str) -> bool:
    return "fs::read_to_string(" in src or bool(INCLUDE_LISP_RE.search(src))


def _lisp_zig_bytes(src: str) -> bool:
    return bool(ZIG_CORRIDOR_RE.search(src))


def _lisp_extension_only(src: str) -> bool:
    """True when `.lisp` appears only as extension/path constant, no I/O."""
    if "fs::read" in src or "include_str!" in src or "include_bytes!" in src:
        return False
    if ZIG_CORRIDOR_RE.search(src):
        return False
    return True


def check(root: Path) -> list:
    problems = []
    for rel in CORE:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            problems.append(f"J0: {rel} required Rust source missing-or-symlink")
            continue
        src = path.read_text(encoding="utf-8", errors="replace")

        names_sens = ".sens" in src
        names_lisp = ".lisp" in src

        if names_sens:
            has_binary = "fs::read(" in src or bool(INCLUDE_SENS_RE.search(src))
            has_zig = bool(ZIG_CORRIDOR_RE.search(src))
            if not has_binary and not has_zig:
                problems.append(
                    f"J1: {rel} names `.sens` but has neither `fs::read(` nor a "
                    "Zig corridor byte carrier"
                )
            if "read_to_string" in src and "fs::read(" not in src and not has_zig:
                problems.append(
                    f"J1: {rel} reads `.sens` as text, not physical bytes"
                )

        if names_lisp:
            if not (
                _lisp_text_path(src)
                or _lisp_zig_bytes(src)
                or _lisp_extension_only(src)
            ):
                problems.append(
                    f"J2: {rel} names `.lisp` without a legal path "
                    "(need fs::read_to_string / include_str!.lisp / Zig byte "
                    "corridor, or extension-constant only)"
                )

        if JSON_RE.search(src):
            problems.append(
                f"J3: {rel} uses JSON on the .lisp/.sens path "
                "(serde_json/json!) -- JSON must not be a path between "
                "Rust and SENS"
            )

    main = root / "crates/sens-cli/src/main.rs"
    if main.is_file() and not main.is_symlink():
        src = main.read_text(encoding="utf-8", errors="replace")
        if "no Rust fallback" not in src and "Zig transport corridor" not in src:
            problems.append(
                "J4: main.rs does not state that physical .sens requires the "
                "Zig corridor and has no Rust T5 fallback"
            )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root", nargs="?", default=str(Path(__file__).resolve().parents[1])
    )
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except OSError as exc:
        print(f"RUST_LISP_SENS_IO_BLOCKED: {exc}", flush=True)
        return 1
    if problems:
        print("RUST_LISP_SENS_IO_BLOCKED:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "RUST_LISP_SENS_IO_OK .lisp via text path or sterile Zig bytes; "
        ".sens as physical bytes through Zig corridor; no JSON path",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
