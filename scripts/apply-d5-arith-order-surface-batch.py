#!/usr/bin/env python3
"""Single-writer: D5 DIFFERENCE/TIMES/LESSP/GREATERP + D6 ADD1/SUB1 aliases → core4."""
from __future__ import annotations
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
core = root / "lib/core4.lisp"
batch = root / "research/d5-arith-order-surface-batch-2026-10-17.lisp"
text = core.read_text(encoding="utf-8")
if "(0011 відняти\n  (0010 (a b) (01011 a b)))" in text:
    print("ALREADY_APPLIED")
    raise SystemExit(0)
body = batch.read_text(encoding="utf-8")
i = body.find("(0011")
body = body[i:]
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
