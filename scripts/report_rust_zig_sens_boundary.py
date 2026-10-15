#!/usr/bin/env python3
"""Emit the Rust <-> Zig <-> SENS boundary map with real file references (#5779).

Acceptance item: "Опублікована карта Rust↔Zig↔SENS boundary і всі залишкові bypass
із реальним file+SHA".

This scans the production Rust and classifies every Rust<->SENS contact:
  corridor  -- reaches SENS only through the sterile Zig corridor
               (zig_transport / sens_zig_* / zig_codec_bridge);
  direct    -- parses/evaluates SENS in Rust (mixed_source/source_words/
               binary_execution/eval) -- the legacy Rust semantic surface;
  filesystem-- reads/writes .lisp or .sens directly;
  bypass    -- a Rust->SENS contact with NO corridor reference in the file.

The map is a REPORT (not a semantic guard): it names remaining contacts.
`--check` fails closed for both direct and mixed Rust semantic surfaces;
a Zig token in the same file cannot erase a live direct Rust path.

Writes research/zig-codecs/rust_zig_sens_boundary.json (or --out PATH).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CORRIDOR_RE = re.compile(r"zig_transport|sens_zig_|zig_codec_bridge|zig_corridor")
DIRECT_RE = re.compile(r"mixed_source|source_words|binary_execution|\beval::|ExprKind|parse_mixed")
FS_RE = re.compile(r'\.(sens|lisp)')
GLOBS = ("crates/*/src/**/*.rs", "crates/*/build.rs")


def _sha(root: Path, rel: str) -> str:
    import hashlib
    p = root / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ""


def build_map(root: Path) -> dict:
    contacts = []
    for pattern in GLOBS:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            if "/tests/" in f"/{rel}" or "/examples/" in f"/{rel}":
                continue
            src = path.read_text(encoding="utf-8", errors="replace")
            corridor = bool(CORRIDOR_RE.search(src))
            direct = bool(DIRECT_RE.search(src))
            fs = bool(FS_RE.search(src))
            if not (corridor or direct or fs):
                continue
            if corridor and not direct:
                kind = "corridor"
            elif direct and not corridor:
                kind = "direct"
            elif direct and corridor:
                kind = "mixed"  # corridor present, but a direct semantic surface too
            else:
                kind = "filesystem"
            contacts.append({"path": rel, "kind": kind, "sha256": _sha(root, rel),
                             "corridor": corridor, "direct_semantic": direct,
                             "filesystem": fs})
    bypasses = [c["path"] for c in contacts if c["kind"] == "direct"]
    return {
        "schema": "sens-rust-zig-sens-boundary/v1",
        "owner_rule": "Rust<->SENS crosses ONLY the sterile Zig corridor (#5777/#5779)",
        "legend": {"corridor": "SENS reached only via Zig", "mixed": "corridor present but a "
                             "direct Rust semantic surface coexists",
                   "direct": "Rust parses/evaluates SENS directly -- a BYPASS",
                   "filesystem": "reads .lisp/.sens directly"},
        "contacts": contacts,
        "bypasses": bypasses,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--out", default="research/zig-codecs/rust_zig_sens_boundary.json")
    parser.add_argument("--check", action="store_true",
                        help="fail closed if any direct bypass exists")
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    data = build_map(root)
    out = root / ns.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    kinds = {}
    for c in data["contacts"]:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print(f"boundary map: {len(data['contacts'])} contact(s) {kinds}; "
          f"bypasses={len(data['bypasses'])} -> {ns.out}")
    # The published "bypasses" list is historically direct-only. Keep that
    # schema for consumers, but never grant --check success to a mixed file:
    # a Zig transport reference alongside direct Rust SENS evaluation is
    # still an unresolved bypass. A comment-only Zig token cannot hide it.
    unresolved = [
        (contact["path"], contact["kind"])
        for contact in data["contacts"]
        if contact["kind"] in ("direct", "mixed")
    ]
    if ns.check and unresolved:
        print("BOUNDARY_BYPASS_PRESENT:", flush=True)
        for path, kind in unresolved:
            print(f" - {path} kind={kind}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
