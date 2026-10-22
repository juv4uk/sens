#!/usr/bin/env python3
"""Guard: non-REPL production Rust is isolated and reaches SENS only via Zig.

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

I1  no include_str! OR include_bytes! of .lisp/.sens/.fasl, even inside a crate,
    and no compile-time embedding of project paths beyond the crate.
I2  no literal fs::read / fs::read_to_string of project paths or
    .lisp/.sens/.fasl files.
A source-pattern guard cannot prove dynamic path flow, Cargo dependency
boundaries, or semantic callability; those need separate tests. The interactive
Rust REPL and its projection catalog are explicitly outside this isolation
boundary: they are the human-facing input/output surface.

Exit 0 = RUST_ISOLATED_ONLY_ZIG_OK; exit 1 = RUST_ISOLATED_ONLY_ZIG_BLOCKED (RED).
"""
from __future__ import annotations

import argparse
import runpy
import re
import sys
import tomllib
from pathlib import Path

PROJECT_TREES = ("lib/", "contracts/", "knowledge/", "language-contract")
INCLUDE_RE = re.compile(r'(?P<kind>include_str|include_bytes)!\s*\(\s*"(?P<path>[^"]+)"')
READ_RE = re.compile(r'(?:std::)?fs::read(?:_to_string)?\s*\(\s*"(?P<path>[^"]+)"')
# The interactive Rust REPL is the projection-facing exception, not the
# binary-runtime isolation surface. Keep its sources out of this guard while
# continuing to scan every other production module in the same crate.
REPL_SOURCE_ROOT = "crates/sens-cli/src/repl"

# The two production-isolation checks must share the SAME lexical Rust scope.
# Mask only provably test-only items; ambiguous cfg remains live, fail closed.
# runpy loads the sibling checker by its absolute path even when this module
# is imported by unittest via spec_from_file_location (no sys.path mutation).
_LEXICAL = runpy.run_path(str(Path(__file__).with_name("rust_lisp_sens_edges.py")))
_PRODUCTION_SOURCE = _LEXICAL["_production_source"]
_CODE_SHAPE = _LEXICAL["_code_shape"]


def _live_at(shape: str, position: int, token: str) -> bool:
    """Reject comment/string ghosts while leaving live Rust edges untouched."""
    return shape[position:position + len(token)] == token



def _is_project_path(target: str) -> bool:
    # `.zig-version` is the corridor's own pin, not a project source.
    if target.endswith(".zig-version"):
        return False
    if target.lower().endswith((".lisp", ".sens", ".fasl")):
        return True
    if target.startswith("../") or "/../" in target:
        return True
    return any(t in target for t in PROJECT_TREES)


def _workspace_sources(root: Path) -> list[Path]:
    manifest = root / "Cargo.toml"
    with manifest.open("rb") as stream:
        config = tomllib.load(stream)
    members = config.get("workspace", {}).get("members")
    if not isinstance(members, list) or not all(isinstance(item, str) for item in members):
        raise ValueError("Cargo.toml must declare workspace.members as string paths")
    sources: set[Path] = set()
    for pattern in members:
        for member in root.glob(pattern):
            if not member.is_dir() or member.is_symlink():
                continue
            sources.update(path for path in member.glob("src/**/*.rs") if path.is_file())
            build_script = member / "build.rs"
            if build_script.is_file():
                sources.add(build_script)
    return sorted(sources)


def check(root: Path) -> list[str]:
    problems: list[str] = []
    try:
        production_sources = _workspace_sources(root)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        return [f"cannot establish Cargo production sources: {type(exc).__name__}: {exc}"]
    scanned = 0
    for path in production_sources:
        rel = path.relative_to(root).as_posix()
        # Tests/examples and uncompiled staging copies are not shipped Rust.
        if ("/tests/" in f"/{rel}" or "/examples/" in f"/{rel}"
                or "/staged-out/" in f"/{rel}"):
            continue
        if rel == f"{REPL_SOURCE_ROOT}.rs" or rel.startswith(f"{REPL_SOURCE_ROOT}/"):
            continue
        scanned += 1
        raw = path.read_text(encoding="utf-8", errors="replace")
        src = _PRODUCTION_SOURCE(raw)
        shape = _CODE_SHAPE(src)
        for m in INCLUDE_RE.finditer(src):
            if (_live_at(shape, m.start(), m.group("kind")) and
                    _is_project_path(m.group('path'))):
                problems.append(f"I1: {rel} `{m.group('kind')}!(\"{m.group('path')}\")` -- Rust "
                                "reaches a project source; only Zig may be reached")
        for m in READ_RE.finditer(src):
            caller = m.group(0).split("(", 1)[0].strip()
            if (_live_at(shape, m.start(), caller) and
                    _is_project_path(m.group('path'))):
                problems.append(f"I2: {rel} `fs::read(\"{m.group('path')}\")` -- Rust reads a "
                                "project file; only Zig may be reached")
    if scanned == 0:
        return ["no production Rust sources found in Cargo workspace members"]
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
    print("RUST_ISOLATED_ONLY_ZIG_OK no literal project-source edges found; dynamic paths require further proof",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
