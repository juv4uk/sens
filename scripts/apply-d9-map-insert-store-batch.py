#!/usr/bin/env python3
"""Single-writer: D9 MAP-INSERT / VEC->LIST / content-store → core4."""
from __future__ import annotations
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
core = root / "lib/core4.lisp"
batch = root / "research/d9-map-insert-store-batch-2026-10-17.lisp"
text = core.read_text(encoding="utf-8")
if "(0011 мапа-вставити" in text and "(0011 вміст-сховище-покласти" in text:
    print("ALREADY_APPLIED")
    raise SystemExit(0)
body = batch.read_text(encoding="utf-8")
body = body[body.find("(0011") :]
m = re.search(r"\(0011 sub1 відняти-1\)\n", text)
if not m:
    m = re.search(
        r"\(0011 зменшити-на-один\n  \(0010 \(x\) \(01011 x 1\)\)\)\n",
        text,
    )
if not m:
    print("ANCHOR_MISSING", file=sys.stderr)
    raise SystemExit(2)
text = text[: m.end()] + "\n" + body + "\n" + text[m.end() :]
if text.count("(") != text.count(")"):
    print("PAREN_IMBALANCE", file=sys.stderr)
    raise SystemExit(3)
core.write_text(text, encoding="utf-8")
print("APPLIED", core.stat().st_size)
