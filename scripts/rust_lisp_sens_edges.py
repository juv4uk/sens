#!/usr/bin/env python3
"""Inventory compile-time Rust → Lisp/SENS edges (include_str!/include_bytes!).

Structural only: no SENS semantic admission. Answers "which Rust files are
wired to which .lisp / .sens / .fasl sources at compile time?"

Fail-closed rules:
  R1  every include_str!/include_bytes! target ending in .lisp/.sens/.fasl
      resolves to an existing path relative to the including .rs file
  R2  every such target is git-tracked (no phantom untracked embed)
  R3  pinned critical edges stay present (bootstrap / surface / contract)

Exit 0 = EDGES_OK; exit 1 = EDGES_BLOCKED.
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
    r"""(?P<kind>include_str|include_bytes)!\s*\(\s*\"(?P<path>(?:\\.|[^\"\\])*)\"\s*\)""",
)
SENS_SUFFIXES = (".lisp", ".sens", ".fasl", ".lisp.fasl")

# Compile-time embeds that must not vanish without an explicit cutover.
CRITICAL_EDGES: tuple[tuple[str, str], ...] = (
    ("crates/wsm-guard-core/src/lib.rs", "lib/core.lisp"),
    ("crates/wsm-guard-core/src/lib.rs", "lib/unify.lisp"),
    ("crates/wsm-guard-core/src/lib.rs", "lib/guard.lisp"),
    ("crates/sens-wasm/src/lib.rs", "lib/core4.lisp.fasl"),
    ("crates/sens-wasm/src/lib.rs", "lib/unify.lisp"),
    ("crates/sens-cli/src/main.rs", "language-contract.lisp"),
    ("crates/sens-cli/src/main.rs", "lib/linter.lisp"),
    ("crates/sens-cli/src/repl.rs", "lib/unify.lisp"),
    ("crates/sens-cli/src/repl.rs", "lib/epistemic.lisp"),
    ("crates/sens/src/mixed_source.rs", "lib/core4.lisp"),
    ("crates/sens-lsp/src/guard_knowledge.rs", "knowledge/guard-reference.lisp"),
)


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
    for m in INCLUDE_RE.finditer(text):
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

    critical_missing: list[dict] = []
    edge_pairs = {(e["rust"], e["target"]) for e in edges}
    for rust, target in CRITICAL_EDGES:
        if (rust, target) not in edge_pairs:
            found = any(
                e["rust"] == rust and e["target"] == target for e in edges
            )
            if not found:
                critical_missing.append({"rust": rust, "target": target})

    blocked = bool(missing or untracked or critical_missing)
    return {
        "schema": SCHEMA,
        "edge_count": len(edges),
        "rust_files_with_edges": len(by_rust),
        "unique_targets": len(by_target),
        "edges": edges,
        "by_rust": {k: sorted(v) for k, v in sorted(by_rust.items())},
        "by_target": {k: sorted(v) for k, v in sorted(by_target.items())},
        "missing": missing,
        "untracked_targets": untracked,
        "critical_missing": critical_missing,
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
        if data["critical_missing"]:
            print("CRITICAL_MISSING:")
            for e in data["critical_missing"]:
                print(f"  {e['rust']} -> {e['target']}")
        if args.by_rust:
            for rust, targets in data["by_rust"].items():
                print(f"{rust}")
                for t in targets:
                    print(f"  {t}")
    return 1 if data["verdict"] != "EDGES_OK" else 0


if __name__ == "__main__":
    sys.exit(main())
