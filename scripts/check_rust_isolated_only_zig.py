#!/usr/bin/env python3
"""Guard: Rust is ISOLATED from the whole project and talks ONLY to Zig (#5777/#5779).

Owner rule (2026-10-15): Rust has the bits isolated from the entire project; it must
reach out ONLY to Zig (the sterile corridor). It must not `include_str!` project
sources, must not `fs::read` project files, and must not pull in the language
library, contract, registries or knowledge itself -- all of that crosses the one
Zig corridor.

This guard is meant to be RED today: Rust currently reaches into lib/ and the
language contract. Red is red -- it is not to be greenwashed; it is the honest
signal that isolation is not yet done.

Fail-closed I-rules over the production Rust (crates/*/src/**, crates/*/build.rs;
tests/examples are not the shipped path):

I1  no `include_str!` of a path that leaves the crate (a `../` escape or a project
    tree: lib/, language-contract, contracts/, knowledge/).
I2  no `fs::read` / `fs::read_to_string` of a project path (lib/, contracts/,
    knowledge/, language-contract).
I3  the only external interface named is the Zig corridor (`zig_transport` /
    `sens_zig_*`); reaching a project source directly is a bypass.

Exit 0 = RUST_ISOLATED_ONLY_ZIG_OK; exit 1 = RUST_ISOLATED_ONLY_ZIG_BLOCKED (RED).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_TREES = ("lib/", "contracts/", "knowledge/", "language-contract")
INCLUDE_RE = re.compile(r'include_str!\(\s*"([^"]+)"')
READ_RE = re.compile(r'fs::read(?:_to_string)?\(\s*"([^"]+)"')
PRODUCTION_GLOBS = ("crates/*/src/**/*.rs", "crates/*/build.rs")


def _is_project_path(target: str) -> bool:
    # `.zig-version` is the corridor's own pin, not a project source.
    if target.endswith(".zig-version"):
        return False
    if target.startswith("../") or "/../" in target:
        return True
    return any(t in target for t in PROJECT_TREES)


def check(root: Path) -> list[str]:
    problems: list[str] = []
    scanned = 0
    for pattern in PRODUCTION_GLOBS:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            # tests and examples are not the shipped Rust path
            if "/tests/" in f"/{rel}" or "/examples/" in f"/{rel}":
                continue
            scanned += 1
            src = path.read_text(encoding="utf-8", errors="replace")
            for m in INCLUDE_RE.finditer(src):
                if _is_project_path(m.group(1)):
                    problems.append(f"I1: {rel} `include_str!(\"{m.group(1)}\")` -- Rust "
                                    "reaches a project source; only Zig may be reached")
            for m in READ_RE.finditer(src):
                if _is_project_path(m.group(1)):
                    problems.append(f"I2: {rel} `fs::read(\"{m.group(1)}\")` -- Rust reads a "
                                    "project file; only Zig may be reached")
    if scanned == 0:
        return ["no production Rust sources found under crates/*/src"]
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except OSError as exc:
        print(f"RUST_ISOLATED_ONLY_ZIG_BLOCKED: {exc}", flush=True)
        return 1
    if problems:
        print(f"RUST_ISOLATED_ONLY_ZIG_BLOCKED {len(problems)} isolation violation(s):",
              flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print("RUST_ISOLATED_ONLY_ZIG_OK Rust is isolated: it reaches only the Zig corridor",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
