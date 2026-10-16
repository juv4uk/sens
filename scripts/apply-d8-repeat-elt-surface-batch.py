#!/usr/bin/env python3
"""Single-writer: D8 REPEAT/ELT + D5 QUOTIENT uk surface → core4."""
from __future__ import annotations
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
core = root / "lib/core4.lisp"
batch = root / "research/d8-repeat-elt-quotient-surface-2026-10-17.lisp"
text = core.read_text(encoding="utf-8")
if "(0011 повторити" in text and "(0011 елемент-за-індексом" in text and "(0011 частка" in text:
    print("ALREADY_APPLIED")
    raise SystemExit(0)
body = batch.read_text(encoding="utf-8")
body = body[body.find("(0011") :]
missing = []
if "(0011 елемент-за-індексом" not in text:
    missing.append("elt")
if "(0011 повторити" not in text:
    missing.append("repeat")
if "(0011 частка" not in text:
    missing.append("quotient-uk")
if not missing:
    print("ALREADY_APPLIED")
    raise SystemExit(0)
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
print("APPLIED", missing, core.stat().st_size)
