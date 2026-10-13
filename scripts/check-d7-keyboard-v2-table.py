#!/usr/bin/env python3
"""Fail-closed v2 D7 keyboard table witness; no Python assert/-O bypass."""
from __future__ import annotations
import json
from pathlib import Path
from domain_tables import D7_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
NORM = ROOT / "knowledge" / "d7-keyboard-v2-ratified.json"
def run() -> None:
    doc = json.loads(NORM.read_text(encoding="utf-8"))
    if (doc.get("schema"),doc.get("status"),doc.get("width"),doc.get("occupancy")) != (
        "sens.d7.keyboard/v2","owner-ratified",7,128
    ):
        raise ValueError("D7 v2 owner authority mismatch")
    raw=doc["table"]
    actual=read_domain_table(D7_TABLE)
    if len(raw)!=128 or len(actual)!=128:
        raise ValueError("D7 v2 requires exactly 128 rows")
    for index,(source,row) in enumerate(zip(raw,actual)):
        bits=format(index,"07b")
        if source["bits"]!=bits or row.bits!=bits or row.lisp is not None:
            raise ValueError(f"D7:{bits} key/callability drift")
        unprintable=index<32 or index==127
        expected=lambda field: None if unprintable else source[field]
        if (row.uk,row.ukr,row.san,row.en,row.sym)!=(
            expected("uk"), expected("uk"), expected("san"),
            expected("ascii"), expected("uk")
        ):
            raise ValueError(f"D7:{bits} glyph drift")
    for lang in ("ascii","uk","san"):
        glyphs=[r[lang] for r in raw]
        if len(set(glyphs))!=128 or any(len(g)!=1 for g in glyphs):
            raise ValueError(f"D7 {lang} mapping must be 128 distinct scalars")
    if raw[39]["uk"]!="'" or raw[92]["uk"]!="ґ" or raw[96]["uk"]!="є":
        raise ValueError("D7 Ukrainian apostrophe/letter pins drift")
    print("D7 KEYBOARD V2: PASS — 128/128 cells, exact JSON mapping, no callable aliases")
if __name__=="__main__":
    run()
