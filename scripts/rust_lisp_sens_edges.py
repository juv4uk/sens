#!/usr/bin/env python3
"""Rust must not embed SENS project sources: only the Zig ABI may bridge hosts.

Mechanical compile-time inventory of include_str!/include_bytes! from tracked
crates/**/*.rs to .lisp/.sens/.fasl. These are FORBIDDEN direct edges, not
required dependencies. They remain red until the actual source references
are migrated away. Do not silently allowlist historical bootstrap files.

R1: missing targets are errors; R2: untracked targets are errors;
R3: EVERY direct Rust -> .lisp/.sens/.fasl embed is a blocking isolation error.
This does not establish runtime / semantic isolation; audit those separately.

Exit 0 = EDGES_OK (zero direct embeds); exit 1 = EDGES_BLOCKED.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA = "sens-rust-lisp-sens-edges/v2"

INCLUDE_RE = re.compile(
    r"""(?P<kind>include_str|include_bytes)!\s*\(\s*\"(?P<path>(?:\\.|[^\"\\])*)\"\s*\)""",
)
# Rust raw strings (r"...", r#"..."#, r###"..."###) are real source embeds.
# The hash delimiter must match on both ends, not just look like a quote.
INCLUDE_RAW_RE = re.compile(
    r'''(?P<kind>include_str|include_bytes)!\s*\(\s*r(?P<hash>#{0,})"(?P<path>[^"]+)"(?P=hash)\s*\)''',
)
SENS_SUFFIXES = (".lisp", ".sens", ".fasl", ".lisp.fasl")

# No critical embed is grandfathered: even core4 / guard / contract is red.

def git_tracked(root: Path) -> set[str]:
    out = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=False,
    )
    return {p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p}


def unescape_rust_string(raw: str) -> str:
    # Minimal: the paths we care about use ../ and plain names.
    return (
        raw.replace(r"\\", "\\")
        .replace(r"\"", '"')
        .replace(r"\n", "\n")
        .replace(r"\t", "\t")
    )


def is_sens_path(path: str) -> bool:
    lower = path.lower()
    return any(lower.endswith(suf) for suf in SENS_SUFFIXES)


def scan_file(rs_path: Path, root: Path) -> list[dict]:
    text = rs_path.read_text(encoding="utf-8", errors="replace")
    rel_rs = rs_path.relative_to(root).as_posix()
    edges: list[dict] = []
    matches = sorted(
        [*INCLUDE_RE.finditer(text), *INCLUDE_RAW_RE.finditer(text)],
        key=lambda match: match.start(),
    )
    for m in matches:
        kind = m.group("kind")
        raw = unescape_rust_string(m.group("path"))
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
                "status": "RED",
                "violation": "DIRECT_RUST_PROJECT_EMBED",
                "line": text.count("\n", 0, m.start()) + 1,
            }
        )
    return edges


def inventory(root: Path) -> dict:
    tracked = git_tracked(root)
    rust_files = sorted(
        p for p in root.glob("crates/**/*.rs") if p.is_file()
    )
    edges: list[dict] = []
    for rs in rust_files:
        rel = rs.relative_to(root).as_posix()
        if rel not in tracked:
            continue
        edges.extend(scan_file(rs, root))

    missing = [e for e in edges if not e["exists"]]
    untracked = [
        e for e in edges if e["exists"] and e["target"] not in tracked
    ]

    by_rust: dict[str, list[str]] = defaultdict(list)
    by_target: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e["target"] not in by_rust[e["rust"]]:
            by_rust[e["rust"]].append(e["target"])
        if e["rust"] not in by_target[e["target"]]:
            by_target[e["target"]].append(e["rust"])

    # Zero is the ONLY acceptable direct-embed count. Historical embeds do not pass.
    blocked = bool(edges or missing or untracked)

    return {
        "schema": SCHEMA,
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
    ap.add_argument("--by-rust", action="store_true", help="print Rust → targets map")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    data = inventory(root)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(
            f"{data['verdict']} edges={data['edge_count']} "
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
            print("RUST_ZIG_ONLY_RED: direct Rust embeds of SENS sources are forbidden")
            for e in data["forbidden_edges"][:30]:
                print(
                    f"  DIRECT_RUST_PROJECT_EMBED id=rust-zig-only "
                    f"layer=transport {e['rust']}:{e['line']} "
                    f"{e['kind']}! -> {e['target']}"
                )
            if len(data["forbidden_edges"]) > 30:
                print(f"  ... {len(data['forbidden_edges']) - 30} additional forbidden edges; "
                      "run --by-rust or --json for the complete inventory")
            print("  REPRO: python3 scripts/rust_lisp_sens_edges.py --by-rust")
        if args.by_rust:
            for rust, targets in data["by_rust"].items():
                print(f"{rust}")
                for t in targets:
                    print(f"  {t}")
    return 1 if data["verdict"] != "EDGES_OK" else 0


if __name__ == "__main__":
    sys.exit(main())
