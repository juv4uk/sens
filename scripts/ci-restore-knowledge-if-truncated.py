#!/usr/bin/env python3
"""CI gate: restore lib/knowledge.lisp when truncated/placeholder.

If knowledge.lisp is < 1000 bytes or contains PLACEHOLDER, rewrite from
known-good commit f6f1f1b with exact D1 COND migration.
Exit 0 after restore (so local can commit); exit 1 if still broken.
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


def needs_restore(text: str) -> bool:
    if len(text) < 1000:
        return True
    if "PLACEHOLDER" in text:
        return True
    if OLD in text:
        return True
    return False


def restore() -> str:
    with urllib.request.urlopen(GOOD, timeout=60) as r:
        text = r.read().decode("utf-8")
    n = text.count(OLD)
    text = text.replace(OLD, NEW)
    i = text.find("\n") + 1
    text = text[:i] + NOTE + text[i:]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    return f"restored {len(text)} bytes, {n} D1 sites"


def main() -> int:
    text = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
    if not needs_restore(text):
        print("knowledge: OK (no restore needed)")
        return 0
    msg = restore()
    print(f"knowledge: {msg}")
    text2 = OUT.read_text(encoding="utf-8")
    if needs_restore(text2):
        print("knowledge: still broken after restore", flush=True)
        return 1
    print("knowledge: PASS after restore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
