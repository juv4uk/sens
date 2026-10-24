#!/usr/bin/env python3
"""Фікстури доказу мовних законів мусять існувати й бути РІЗНИМИ парами.

Першопричина: scripts/prove-lisp-language-laws.sh запускає SENS і порівнює
вироки D1 для 14 законів — це ЄДИНИЙ механізм, що доводить семантику
ВИКОНАННЯМ. Він викликається з ci.yml:419. Але якщо фікстура зникне або
закон і мутант збігаються, скрипт упаде лише під час запуску — а доти
ніхто не знає.

Ця перевірка читає список id ЗІ САМОГО скрипта (не з копії) і вимагає, щоб
кожен мав law і mutant, і щоб вони РІЗНИЛИСЬ. Це захищає доказ від тихого
розсипання. Семантику вона НЕ перевіряє — лише цілісність фікстур.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVE = ROOT / "scripts" / "prove-lisp-language-laws.sh"
SEMANTIC = ROOT / "tests" / "semantic"
# Закони з іншою схемою імені (з самого скрипта).
SPECIAL = {"d3-cond-demand", "d4-parameter-shadowing", "quote-inertness"}


def ids_from_script() -> list[str]:
    text = PROVE.read_text(encoding="utf-8")
    m = re.search(r"for id in ([^;]+); do", text)
    if not m:
        raise SystemExit("FAIL: не знайдено списку id у prove-lisp-language-laws.sh")
    return m.group(1).split()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail-closed: кожен id мусить мати різну пару law/mutant")
    args = ap.parse_args()
    ids = ids_from_script()
    bad: list[str] = []
    for i in ids:
        if i in SPECIAL:
            law = SEMANTIC / f"language-law-{i}.lisp"
            mutant = SEMANTIC / f"language-mutant-{i}.lisp"
        else:
            law = SEMANTIC / f"{i}-law.lisp"
            mutant = SEMANTIC / f"{i}-mutant.lisp"
        if not law.is_file() or not mutant.is_file():
            bad.append(f"{i}: фікстура відсутня ({law.name} / {mutant.name})")
        elif law.read_bytes() == mutant.read_bytes():
            bad.append(f"{i}: law і mutant ІДЕНТИЧНІ")
    print(f"PROVE-FIXTURES: id у скрипті={len(ids)} проблем={len(bad)}")
    for b in bad:
        print(f"  {b}")
    if bad:
        raise SystemExit("FAIL: фікстури доказу розсипались")
    if args.check:
        print("PROVE-FIXTURES: PASS кожен закон має різну пару law/mutant")
    return 0


if __name__ == "__main__":
    sys.exit(main())
