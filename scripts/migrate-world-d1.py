#!/usr/bin/env python3
"""Migrate lib/world.lisp: host (001 t) COND else → exact D1:1.

    python3 scripts/migrate-world-d1.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "lib" / "world.lisp"
OLD = "(1110 (001 t)"
NEW = "(1110 (010 (001 ()))"
NOTE = (
    ";; Migrated: (001 t) COND else → exact D1:1 (010 (001 ())). "
    "Width is identity.\n"
)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    n = text.count(OLD)
    if n == 0 and NEW in text:
        print("world: already migrated")
        return 0
    if n == 0:
        print(f"world: no host-t sites found (file may be truncated)")
        return 1
    text = text.replace(OLD, NEW)
    if NOTE not in text:
        i = text.find("\n") + 1
        text = text[:i] + NOTE + text[i:]
    PATH.write_text(text, encoding="utf-8")
    print(f"world: {n} D1 replacements, {len(text)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
