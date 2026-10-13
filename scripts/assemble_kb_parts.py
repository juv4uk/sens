#!/usr/bin/env python3
"""Restore lib/knowledge.lisp from gzip+b64 parts OR jsdelivr fallback.

Primary: scripts/knowledge_{a,b}.b64 if present.
Fallback: download f6f1f1b + D1 migration (same as assemble_knowledge.py).

    python3 scripts/assemble_kb_parts.py
"""
from __future__ import annotations

import base64
import gzip
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "lib" / "knowledge.lisp"
OLD = "(1110 (001 t)"
NEW = "(1110 (010 (001 ()))"
NOTE = (
    ";; Migrated: (001 t) COND else → exact D1:1 (010 (001 ())). "
    "Width is identity.\n"
)
GOOD = (
    "https://cdn.jsdelivr.net/gh/juv4uk/sens@"
    "f6f1f1b3d1c234a5fcc1b98e585f1d3a91ea553d/lib/knowledge.lisp"
)


def from_parts() -> str | None:
    a = HERE / "knowledge_a.b64"
    b = HERE / "knowledge_b.b64"
    if not (a.is_file() and b.is_file()):
        return None
    try:
        parts = [
            gzip.decompress(base64.b64decode(a.read_text().strip())),
            gzip.decompress(base64.b64decode(b.read_text().strip())),
        ]
        return b"".join(parts).decode("utf-8")
    except Exception as e:
        print(f"parts failed: {e}")
        return None


def from_cdn() -> str:
    with urllib.request.urlopen(GOOD, timeout=60) as r:
        text = r.read().decode("utf-8")
    text = text.replace(OLD, NEW)
    i = text.find("\n") + 1
    return text[:i] + NOTE + text[i:]


def main() -> int:
    text = from_parts()
    if text is None:
        print("parts missing — fetching from CDN…")
        text = from_cdn()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"restored {OUT} ({len(text)} bytes)")
    if OLD in text:
        print("WARNING: host-t still present")
        return 1
    if "PLACEHOLDER" in text or len(text) < 1000:
        print("WARNING: file still truncated")
        return 1
    print("KNOWLEDGE RESTORE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
