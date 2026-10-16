#!/usr/bin/env python3
"""Single-writer: TAKE/DROP (if missing) + ADD1/SUB1 domain-surface aliases."""
from __future__ import annotations
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
core = root / "lib/core4.lisp"
batch = root / "research/d6-take-drop-curry-batch-2026-10-17.lisp"
text = core.read_text(encoding="utf-8")
changed = False

if "(0011 взяти" not in text:
    body = batch.read_text(encoding="utf-8")
    i = body.find("(0011")
    if i < 0:
        print("BATCH_EMPTY", file=sys.stderr)
        raise SystemExit(2)
    body = body[i:]
    m = re.search(
        r"\(0011 зменшити-на-один\n  \(0010 \(x\) \(01011 x 1\)\)\)\n",
        text,
    )
    if not m:
        print("ANCHOR_MISSING", file=sys.stderr)
        raise SystemExit(2)
    text = text[: m.end()] + "\n" + body + "\n" + text[m.end() :]
    changed = True
    print("APPLIED_TAKE_DROP")
else:
    print("TAKE_DROP_PRESENT")

if "(0011 додати-1" not in text:
    aliases = (
        "\n; D6:001110/001111 domain-surface aliases (residency lib/domains/d6.lisp)\n"
        "(0011 додати-1 збільшити-на-один)\n"
        "(0011 відняти-1 зменшити-на-один)\n"
        "(0011 add1 збільшити-на-один)\n"
        "(0011 sub1 зменшити-на-один)\n"
    )
    m = re.search(
        r"\(0011 зменшити-на-один\n  \(0010 \(x\) \(01011 x 1\)\)\)\n",
        text,
    )
    if not m:
        print("ALIAS_ANCHOR_MISSING", file=sys.stderr)
        raise SystemExit(2)
    text = text[: m.end()] + aliases + text[m.end() :]
    changed = True
    print("APPLIED_ALIASES")
else:
    print("ALIASES_PRESENT")

if text.count("(") != text.count(")"):
    print("PAREN_IMBALANCE", file=sys.stderr)
    raise SystemExit(3)
if changed:
    core.write_text(text, encoding="utf-8")
    print("WROTE", core.stat().st_size)
else:
    print("NOOP")
