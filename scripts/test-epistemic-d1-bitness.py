#!/usr/bin/env python3
"""Перевірити епістемічний модуль та точні ширини доменів.

Перевірки:
  1. lib/epistemic.lisp не залежить від host truthiness (t / NIL / T)
  2. Викличні назви модуля є точними ратифікованими українськими проєкціями
     D9/D10, а не старими англійськими peer-зв'язуваннями
  3. Кожна lib/domains/dN.lisp має 2^N рядків із ключами рівно N бітів

Це не доводить runtime-викличність або фізичне виконання T5M. Запуск:

    python3 scripts/test-epistemic-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPI = ROOT / "lib" / "epistemic.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
REQUIRED_FNS = (
    "це-належне-посилання-на-джерело?",
    "епістеміка--посилання-на-твердження?",
    "твердження-твердження",
    "твердження-перевірка",
    "доказ-підсумок",
    "намір-ціль",
    "отримати-посилання-на-джерело-доказу",
    "отримати-джерело-спостереження",
    "спостереження-твердження",
    "отримати-посилання-доказу-на-твердження",
    "доказ-метод",
    "отримати-необхідні-можливості-наміру",
    "отримати-умови-зупинки-наміру",
    "отримати-очікувані-результати-наміру",
    "підтверджувальний-доказ",
    "усі-необхідні-можливості-наміру-забезпечені?",
)
RETIRED_ENGLISH_HEADS = (
    "make-observation",
    "make-claim",
    "make-evidence",
    "make-intent",
    "source-ref?",
    "observation?",
    "claim?",
    "evidence?",
    "intent?",
    "supporting-evidence",
    "intent-capabilities-satisfied?",
    "claim-statement",
    "claim-review",
    "evidence-outcome",
    "intent-goal",
)


def check_epistemic() -> list[str]:
    errs: list[str] = []
    if not EPI.is_file():
        return [f"missing {EPI.relative_to(ROOT)}"]
    text = EPI.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"epistemic: host truthiness {m.group()!r} at offset {m.start()}")
    for fn in REQUIRED_FNS:
        if fn not in text:
            errs.append(f"epistemic: required function surface missing: {fn}")
    for fn in RETIRED_ENGLISH_HEADS:
        if re.search(rf"(?<![\w-]){re.escape(fn)}(?![\w-])", text):
            errs.append(f"epistemic: retired English function surface remains: {fn}")
    return errs


def check_domain(n: int) -> list[str]:
    path = ROOT / "lib" / "domains" / f"d{n}.lisp"
    errs: list[str] = []
    if not path.is_file():
        return [f"D{n}: missing"]
    keys = ROW.findall(path.read_text(encoding="utf-8"))
    expect = 1 << n
    if len(keys) != expect:
        errs.append(f"D{n}: expected {expect} rows, got {len(keys)}")
    bad = [k for k in keys if len(k) != n]
    if bad:
        errs.append(f"D{n}: key width {len(bad[0])} != {n}")
    if len(set(keys)) != len(keys):
        errs.append(f"D{n}: duplicate coordinates")
    return errs


def main() -> int:
    all_errs: list[str] = []
    all_errs.extend(check_epistemic())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("EPISTEMIC+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("EPISTEMIC: PASS — no host truthiness, Ukrainian D9/D10 surface intact")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
