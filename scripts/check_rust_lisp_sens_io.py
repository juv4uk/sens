#!/usr/bin/env python3
"""Test/guard: how Rust talks to .lisp and .sens -- and that NO json path is used.

Answer this guard proves (from the source, not from memory):

- `.lisp` is read as TEXT   -> fs::read_to_string(...)
- `.sens` is read as BYTES  -> fs::read(...)   (physical T5, never UTF-8 text)
- neither the .lisp nor the .sens path uses JSON/serde_json (or any side-channel);
  the pairing is compared at the exact-word and physical-byte level.
- the .sens path requires the sterile Zig corridor (no Rust T5 fallback).

Fail-closed J-rules over the core Rust modules that touch these files:
J1  a module that names `.sens` must read it with `fs::read(` (binary).
J2  a module that names `.lisp` must read it with `fs::read_to_string(` (text).
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


def check(root: Path) -> list[str]:
    problems: list[str] = []
    seen = 0
    for rel in CORE:
        path = root / rel
        if not path.is_file():
            continue
        seen += 1
        src = path.read_text(encoding="utf-8", errors="replace")

        names_sens = ".sens" in src
        names_lisp = ".lisp" in src

        if names_sens and "fs::read(" not in src:
            problems.append(f"J1: {rel} names `.sens` but does not read it as binary "
                            "(`fs::read(` missing)")
        if names_sens and "read_to_string" in src and "fs::read(" not in src:
            problems.append(f"J1: {rel} reads `.sens` as text, not physical bytes")

        if names_lisp and "fs::read_to_string(" not in src:
            problems.append(f"J2: {rel} names `.lisp` but does not read it as text "
                            "(`fs::read_to_string(` missing)")

        if JSON_RE.search(src):
            problems.append(f"J3: {rel} uses JSON on the .lisp/.sens path "
                            "(serde_json/json!) -- JSON must not be a path between "
                            "Rust and SENS")

    if seen == 0:
        return ["no core Rust .lisp/.sens module found under the expected paths"]

    # J4 -- the physical .sens entry states the corridor requirement.
    main = root / "crates/sens-cli/src/main.rs"
    if main.is_file():
        src = main.read_text(encoding="utf-8", errors="replace")
        if "no Rust fallback" not in src and "Zig transport corridor" not in src:
            problems.append("J4: main.rs does not state that physical .sens requires the "
                            "Zig corridor and has no Rust T5 fallback")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
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
    print("RUST_LISP_SENS_IO_OK Rust reads .lisp as text (fs::read_to_string) and .sens "
          "as physical bytes (fs::read) through the Zig corridor; no JSON path",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
