#!/usr/bin/env python3
"""Restore lib/knowledge.lisp: exact D1 COND migration from known-good base.

Fetches the pre-damage version and replaces (1110 (001 t) with D1:1.
Run from repo root:

    python3 scripts/restore-knowledge-d1.py
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
        print(f"expected 4 host-t sites, found {n}")
        return 1
    text = text.replace(OLD, NEW)
    i = text.find("\n") + 1
    text = text[:i] + NOTE + text[i:]
    OUT.write_text(text, encoding="utf-8")
    print(f"restored {OUT} ({len(text)} bytes, {n} D1 replacements)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
