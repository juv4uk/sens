#!/usr/bin/env python3
"""Кожен `*_generated.rs` мусить або компілюватися в крейт, або бути ЯВНО
оголошеним джерелом-даними (provenance), а не виглядати кодом без споживача.

Першопричина: `numeric_domains_generated.rs` і `text7_projection_generated.rs`
не мають ні `mod`, ні `include!`, ні жодного Rust-споживача — їх тримають лише
Python-гварди. `.rs`-розширення обіцяє код; насправді це дані. Файл, який
ВИГЛЯДАЄ законом, але не компілюється, найлегше відредагувати марно.

Правило (fail-closed на НОВІ сироти, названі — як борг):
  • має `mod` у lib.rs  → компілюється (OK);
  • шапка оголошує provenance/дані → OK (дані, не код);
  • інакше → борг; НОВИЙ такий файл падає.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "crates/sens/src"

# Названі борги: перевірені вручну. НОВИЙ сирота падає — тут його немає.
KNOWN_DEBT = {"numeric_domains_generated"}
# Джерела-дані: шапка сама оголошує, що не є виконуваним/дисплейним кодом.
DATA_MARKERS = ("provenance ONLY", "No executable", "not compiled")


def consumed_stems() -> set[str]:
    """Спожиті шари — з УСІХ .rs крейту, двома способами:
      • `mod <stem>;`  — звичайне оголошення модуля;
      • `include!("<stem>.rs")` — втягування файла в інший модуль.
    Друга форма — не рідкість: d10_definition_bindings_generated,
    function_signatures_generated, semantic_registry_generated і
    d7_display_registry_generated підключені саме так (semantic_registry.rs:44,
    language_items.rs:61). Перевіряти лише `mod` означає хибно оголосити їх
    сиротами — саме на цьому я помилився двічі."""
    found: set[str] = set()
    for path in SRC.rglob("*.rs"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        found |= set(re.findall(
            r"(?m)^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+([a-z0-9_]+)\s*;", text))
        found |= set(re.findall(r'include!\("([a-z0-9_]+)\.rs"\)', text))
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail-closed на нові сироти")
    args = ap.parse_args()
    mods = consumed_stems()
    files = sorted(SRC.glob("*_generated.rs"))
    debt, data, wired = [], [], []
    for path in files:
        stem = path.stem
        if stem in mods:
            wired.append(stem)
            continue
        head = path.read_text(encoding="utf-8", errors="ignore")[:1200]
        if any(marker in head for marker in DATA_MARKERS):
            data.append(stem)
            continue
        debt.append(stem)
    print(f"GENERATED-LAYERS: усього={len(files)} компілюються={len(wired)} "
          f"дані={len(data)} борг={len(debt)}")
    for stem in wired:
        print(f"  {stem}: спожито (mod/include!)")
    for stem in data:
        print(f"  {stem}: оголошено джерелом-даними (шапка)")
    for stem in debt:
        print(f"  {stem}: БОРГ — немає ні mod, ні оголошення даних")
    new = sorted(set(debt) - KNOWN_DEBT)
    if new:
        raise SystemExit(f"FAIL: нові шари без споживача: {new}")
    if args.check:
        print("GENERATED-LAYERS: PASS нових сиріт немає (борг названо)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
