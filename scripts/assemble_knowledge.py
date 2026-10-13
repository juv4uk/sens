#!/usr/bin/env python3
"""Restore lib/knowledge.lisp: download known-good + exact D1 COND migration.

Swarm-unblocking restore. Source: commit f6f1f1b (pre-placeholder).
Replaces (1110 (001 t) with (1110 (010 (001 ())) = D1:1.

    python3 scripts/assemble_knowledge.py
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

GOOD = (
    "https://cdn.jsdelivr.net/gh/juv4uk/sens@"
    "f6f1f1b3d1c234a5fcc1b98e585f1d3a91ea553d/lib/knowledge.lisp"
)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "lib" / "knowledge.lisp"
OLD = "(1110 (001 t)"
NEW = "(1110 (010 (001 ()))"
NOTE = (
    ";; Migrated: (001 t) COND else → exact D1:1 (010 (001 ())). "
    "Width is identity.\n"
)


def main() -> int:
    with urllib.request.urlopen(GOOD, timeout=60) as r:
        text = r.read().decode("utf-8")
    n = text.count(OLD)
    if n != 4:
        print(f"warning: expected 4 host-t sites, found {n}")
    text = text.replace(OLD, NEW)
    i = text.find("\n") + 1
    text = text[:i] + NOTE + text[i:]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"restored {OUT} ({len(text)} bytes, {n} D1 replacements)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
