#!/usr/bin/env python3
"""Single-writer: D9 map/vec list projections → core4."""
from __future__ import annotations
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
core = root / "lib/core4.lisp"
batch = root / "research/d9-map-vec-list-batch-2026-10-17.lisp"
text = core.read_text(encoding="utf-8")
if all(re.search(rf"\((?:0011|визначити)\s+{name}(?=\s|\))", text) for name in ("мапа-отримати", "вектор-н-тий")):
    print("ALREADY_APPLIED")
    raise SystemExit(0)
body = batch.read_text(encoding="utf-8")
start = re.search(r"(?m)^\((?:0011|визначити)\s+мапа-порожній", body)
if start is None:
    print("BATCH_START_MISSING", file=sys.stderr)
    raise SystemExit(4)
body = body[start.start() :]
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
