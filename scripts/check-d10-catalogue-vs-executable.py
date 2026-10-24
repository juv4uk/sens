#!/usr/bin/env python3
"""D10: відокремити 1024 ратифіковані ПОЗИЦІЇ від фізично ВИКОНУВАНИХ функцій.

Першопричина: проєкт ЗАВЖДИ стверджував розділення («Увесь словник Д10
ратифікований власником; допуск до виконання окремий» — lib/domains/d10.lisp:6;
domain_words.rs:209-211; environment.rs:973; compiler_bootstrap.rs:378), і
тести його охороняли. Але ПЕРЕЛІЧЕНОГО реєстру не існувало — лише межі
(≤314, ≥3). Через це «1024» легко читалося як «1024 виконувані функції».

Цей чекер будує реєстр із ДЕРЕВА й падає закрито, якщо шари розходяться.

Шари (кожен перевірений вручну):
  каталог  1024  lib/domains/d10.lisp            — ратифіковані позиції
  bindings  311  d10_definition_bindings_generated.rs — конкретні DEFINE/аліаси
  selectors 256  eval/selector_law.rs (топ-3 біти 011|100) — закон селекторів
  host        1  crates/sens/src/lib.rs (D10-константа) — явний механізм

  виконувані = bindings ∪ host;  carrier-only = каталог − виконувані.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "lib/domains/d10.lisp"
BINDINGS = ROOT / "crates/sens/src/d10_definition_bindings_generated.rs"
LIB = ROOT / "crates/sens/src/lib.rs"
LEDGER = ROOT / "knowledge/d10-catalogue-vs-executable.tsv"

CATALOGUE_ROW = re.compile(r"(?m)^\s*\(([01]{10})\s")
BINDING_ROW = re.compile(r"bits:\s*0b([01]{10})")
# Явна D10-константа механізму в lib.rs (10 бітів), поза файлом bindings.
HOST_CONST = re.compile(r"_D10:\s*u16\s*=\s*0b([01]{10})")
SELECTOR_PREFIXES = ("011", "100")


def catalogue() -> set[str]:
    return set(CATALOGUE_ROW.findall(CATALOGUE.read_text(encoding="utf-8")))


def bindings() -> set[str]:
    return set(BINDING_ROW.findall(BINDINGS.read_text(encoding="utf-8")))


def host_mechanisms() -> set[str]:
    return set(HOST_CONST.findall(LIB.read_text(encoding="utf-8")))


def selectors(cat: set[str]) -> set[str]:
    return {row for row in cat if row[:3] in SELECTOR_PREFIXES}


def build() -> dict[str, object]:
    cat = catalogue()
    bind = bindings()
    host = host_mechanisms()
    sel = selectors(cat)
    if len(cat) != 1024:
        raise SystemExit(f"FAIL: каталог D10 має {len(cat)} позицій, очікувано 1024")
    if not bind <= cat:
        raise SystemExit(f"FAIL: bindings поза каталогом: {sorted(bind - cat)[:3]}")
    if not sel <= bind:
        raise SystemExit(f"FAIL: селектори поза bindings: {sorted(sel - bind)[:3]}")
    if not host <= cat:
        raise SystemExit(f"FAIL: host-механізми поза каталогом: {sorted(host - cat)[:3]}")
    executable = bind | host
    return {"catalogue": cat, "bindings": bind, "selectors": sel,
            "host": host, "executable": executable}


def render(state: dict[str, object]) -> str:
    cat: set[str] = state["catalogue"]  # type: ignore[assignment]
    ex: set[str] = state["executable"]  # type: ignore[assignment]
    bind: set[str] = state["bindings"]  # type: ignore[assignment]
    sel: set[str] = state["selectors"]  # type: ignore[assignment]
    host: set[str] = state["host"]  # type: ignore[assignment]
    lines = ["# D10: ратифікована позиція | виконуваність | джерело",
             "# ratified-position\tadmitted\torigin"]
    for row in sorted(cat):
        if row in sel:
            origin = "selector-law"
        elif row in bind:
            origin = "binding"
        elif row in host:
            origin = "host-mechanism"
        else:
            origin = "carrier-only"
        lines.append(f"{row}\t{'так' if row in ex else 'ні'}\t{origin}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="звірити наявний реєстр із деревом (fail-closed)")
    ap.add_argument("--write", action="store_true", help="перезаписати реєстр")
    args = ap.parse_args()
    state = build()
    text = render(state)
    n = lambda k: len(state[k])  # noqa: E731
    print(f"D10-SEPARATION: каталог={n('catalogue')} виконувані={n('executable')} "
          f"(bindings={n('bindings')} ∪ host={n('host')}; селектори={n('selectors')}) "
          f"carrier-only={n('catalogue') - n('executable')}")
    if args.write:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(text, encoding="utf-8")
        print(f"D10-SEPARATION: реєстр записано → {LEDGER.relative_to(ROOT)}")
        return 0
    if args.check:
        if not LEDGER.is_file():
            raise SystemExit("FAIL: реєстр відсутній — виконай --write")
        if LEDGER.read_text(encoding="utf-8") != text:
            raise SystemExit("FAIL: реєстр розійшовся з деревом")
        print("D10-SEPARATION: PASS реєстр збігається з деревом")
        return 0
    print("D10-SEPARATION: PASS (без --check/--write нічого не змінено)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
