#!/usr/bin/env python3
"""Rust production sources must not embed SENS project bits — only Zig may bridge.

Compile-time inventory of include_str!/include_bytes! from production Rust
(crates/*/src/**/*.rs and crates/*/build.rs, excluding tests/ and examples/)
to .lisp / .sens / .fasl. Every such edge is a FORBIDDEN isolation error
(RUST_ZIG_ONLY). No grandfathered bootstrap list.

Scope matches scripts/check_rust_isolated_only_zig.py (production path only).
Physical bytes cross hosts only via the sterile Zig corridor (#5777/#5779).

R1 missing target → error
R2 untracked target → error
R3 any direct embed → EDGES_BLOCKED (RED until cutover to zero)

Exit 0 = EDGES_OK (zero production embeds); exit 1 = EDGES_BLOCKED.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA = "sens-rust-lisp-sens-edges/v1"

INCLUDE_RE = re.compile(
    r'(?P<kind>include_str|include_bytes)!\s*\(\s*"(?P<path>(?:\\.|[^"\\])*)"\s*\)',
)
# Rust expands all-literal concat! before include_str!/include_bytes!.
# A split path is still a direct embed of SENS bytes, never a Zig route.
STATIC_CONCAT_INCLUDE_RE = re.compile(
    r'(?P<kind>include_str|include_bytes)!\s*\(\s*concat!\s*\(\s*'
    r'(?P<parts>"(?:\\.|[^"\\])*"(?:\s*,\s*"(?:\\.|[^"\\])*")*\s*,?)'
    r'\s*\)\s*\)',
)
CONCAT_PART_RE = re.compile(r'"(?P<path>(?:\\.|[^"\\])*)"')

SENS_SUFFIXES = (".lisp", ".sens", ".fasl", ".lisp.fasl")
PRODUCTION_GLOBS = ("crates/*/src/**/*.rs", "crates/*/build.rs")


def git_tracked(root: Path) -> set[str]:
    out = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=False,
    )
    return {p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p}


def unescape_rust_string(raw: str) -> str:
    return (
        raw.replace("\\\\", "\\")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )


def is_sens_path(path: str) -> bool:
    lower = path.lower()
    return any(lower.endswith(suf) for suf in SENS_SUFFIXES)


def is_production_rust(rel: str) -> bool:
    if "/tests/" in f"/{rel}/" or "/examples/" in f"/{rel}/":
        return False
    if rel.endswith("build.rs"):
        return True
    return "/src/" in f"/{rel}/"


def production_rust_files(root: Path, tracked: set[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in PRODUCTION_GLOBS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel not in tracked:
                continue
            if not is_production_rust(rel):
                continue
            files.append(path)
    return files


# Production scope is a Rust cfg condition, not merely a filesystem path.
# Preserve offsets so the line in a failed receipt still points to real source.
_CFG_TEST_ITEM = re.compile(
    r"#\s*\[\s*cfg\s*\(\s*test\s*\)\s*\]\s*(?:pub\s+)?(?:mod|fn|const|static)\s+\w+\b"
)
_RAW_STRING = re.compile(r'(?:br|r)(?P<hashes>#{0,16})"')
_CHAR_LITERAL = re.compile(r"'(?:\\.|[^'\\\n])'")


def _code_shape(source: str) -> str:
    """Mask Rust comments/string/char literals, keeping braces and offsets."""
    output = list(source)
    size = len(source)

    def erase(first: int, last: int) -> None:
        for offset in range(first, last):
            if output[offset] != "\n":
                output[offset] = " "

    i = 0
    while i < size:
        start = i
        if source.startswith("//", i):
            end = source.find("\n", i + 2)
            i = size if end < 0 else end
            erase(start, i)
            continue
        if source.startswith("/*", i):
            depth = 1
            i += 2
            while i < size and depth:
                if source.startswith("/*", i):
                    depth += 1
                    i += 2
                elif source.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            erase(start, i)
            continue
        raw = _RAW_STRING.match(source, i)
        if raw:
            terminator = '"' + raw.group("hashes")
            end = source.find(terminator, raw.end())
            i = size if end < 0 else end + len(terminator)
            erase(start, i)
            continue
        if source[i] == '"':
            i += 1
            while i < size:
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            i = min(i, size)
            erase(start, i)
            continue
        char = _CHAR_LITERAL.match(source, i)
        if char:
            i = char.end()
            erase(start, i)
            continue
        i += 1
    return "".join(output)


def _production_source(source: str) -> str:
    """Exclude only proven #[cfg(test)] items; uncertain syntax stays RED."""
    shape = _code_shape(source)
    output = list(source)
    for attr in _CFG_TEST_ITEM.finditer(shape):
        start = attr.start()
        opened = shape.find("{", attr.end())
        ended = shape.find(";", attr.end())
        if opened < 0 or (ended >= 0 and ended < opened):
            if ended < 0:
                continue  # malformed or unsupported: fail closed
            stop = ended + 1
        else:
            depth = 0
            stop = -1
            for index in range(opened, len(shape)):
                if shape[index] == "{":
                    depth += 1
                elif shape[index] == "}":
                    depth -= 1
                    if depth == 0:
                        stop = index + 1
                        break
            if stop < 0:
                continue  # unmatched brace: do not silently hide source
        for index in range(start, stop):
            if output[index] != "\n":
                output[index] = " "
    return "".join(output)


def scan_file(rs_path: Path, root: Path) -> list[dict]:
    original = rs_path.read_text(encoding="utf-8", errors="replace")
    text = _production_source(original)
    live = _code_shape(text)
    rel_rs = rs_path.relative_to(root).as_posix()
    edges: list[dict] = []
    includes = [
        (m.start(), m.group("kind"), unescape_rust_string(m.group("path")))
        for m in INCLUDE_RE.finditer(text)
    ]
    for m in STATIC_CONCAT_INCLUDE_RE.finditer(text):
        raw = "".join(
            unescape_rust_string(part.group("path"))
            for part in CONCAT_PART_RE.finditer(m.group("parts"))
        )
        includes.append((m.start(), m.group("kind"), raw))
    for position, kind, raw in sorted(includes):
        # A comment, string literal, or cfg(test) body is no production edge.
        # The live macro name must exist at the identical source offset.
        if live[position:position + len(kind)] != kind:
            continue
        if not is_sens_path(raw):
            continue
        resolved = (rs_path.parent / raw).resolve()
        try:
            rel_target = resolved.relative_to(root.resolve()).as_posix()
        except ValueError:
            rel_target = raw
        edges.append(
            {
                "rust": rel_rs,
                "kind": kind,
                "include_arg": raw,
                "target": rel_target,
                "exists": resolved.is_file(),
                "line": text.count("\n", 0, position) + 1,
                "status": "RED",
                "violation": "DIRECT_RUST_PROJECT_EMBED",
            }
        )
    return edges


def inventory(root: Path) -> dict:
    tracked = git_tracked(root)
    edges: list[dict] = []
    for rs in production_rust_files(root, tracked):
        edges.extend(scan_file(rs, root))

    missing = [e for e in edges if not e["exists"]]
    untracked = [e for e in edges if e["exists"] and e["target"] not in tracked]

    by_rust: dict[str, list[str]] = defaultdict(list)
    by_target: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e["target"] not in by_rust[e["rust"]]:
            by_rust[e["rust"]].append(e["target"])
        if e["rust"] not in by_target[e["target"]]:
            by_target[e["target"]].append(e["rust"])

    blocked = bool(edges) or bool(missing) or bool(untracked)
    return {
        "schema": SCHEMA,
        "scope": "production-rust-only",
        "edge_count": len(edges),
        "rust_files_with_edges": len(by_rust),
        "unique_targets": len(by_target),
        "edges": edges,
        "forbidden_edge_count": len(edges),
        "forbidden_edges": edges,
        "isolation_rule": "RUST_ZIG_ONLY",
        "by_rust": {k: sorted(v) for k, v in sorted(by_rust.items())},
        "by_target": {k: sorted(v) for k, v in sorted(by_target.items())},
        "missing": missing,
        "untracked_targets": untracked,
        "verdict": "EDGES_BLOCKED" if blocked else "EDGES_OK",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--by-rust", action="store_true")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    data = inventory(root)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(
            f"{data['verdict']} scope={data['scope']} edges={data['edge_count']} "
            f"rust_files={data['rust_files_with_edges']} "
            f"targets={data['unique_targets']}"
        )
        if data["missing"]:
            print("MISSING:")
            for e in data["missing"]:
                print(f"  {e['rust']}:{e['line']} -> {e['include_arg']}")
        if data["untracked_targets"]:
            print("UNTRACKED:")
            for e in data["untracked_targets"]:
                print(f"  {e['rust']} -> {e['target']}")
        if data["forbidden_edges"]:
            print(
                "RUST_ZIG_ONLY_RED: production Rust embeds of SENS sources are forbidden; "
                "only the sterile Zig corridor may bridge physical bytes"
            )
            for e in data["forbidden_edges"][:40]:
                print(
                    f"  DIRECT_RUST_PROJECT_EMBED {e['rust']}:{e['line']} "
                    f"{e['kind']}! -> {e['target']}"
                )
            if len(data["forbidden_edges"]) > 40:
                print(
                    f"  ... {len(data['forbidden_edges']) - 40} more; "
                    "run --by-rust or --json"
                )
            print("  REPRO: python3 scripts/rust_lisp_sens_edges.py --by-rust")
            print("  GOAL: zero production embeds; Rust reaches ONLY Zig")
    return 1 if data["verdict"] != "EDGES_OK" else 0


if __name__ == "__main__":
    sys.exit(main())
