#!/usr/bin/env python3
"""Ядро і його фізична пара мусять змінюватися РАЗОМ.

Першопричина: `lib/core4.lisp` змінили, а `lib/core4.sens` — ні. Закомічена пара
лишилась застарілою, bootstrap-перевірка це помітила (`actual=outdated-physical`,
`release=NO-GO`), а профіль `core4` виконав сім свідків ПРОТИ ЗАСТАРІЛОГО ЯДРА —
і всі сім упали: d10-clips-* (4) і d6-let* (3).

`remint-drifted-pairs.yml:142-148` **навмисно** пропускає Core4 (щоб чужий push не
пере-карбовував ядро). Виключення доречне, але беззахисне: ніщо не змушує того,
хто змінює ДЖЕРЕЛО, пере-карбувати ПАРУ. Ця перевірка це зобов'язує.

Працює без бінарника: дивиться лише на перелік змінених шляхів.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Джерело -> фізична пара, яку воно зобов'язує.
PAIRS = {"lib/core4.lisp": "lib/core4.sens"}
# Джерела, свідомо виключені з автопере-карбування. Їх перевіряємо ЛИШЕ якщо
# пара ФАКТИЧНО існує: lib/core2, lib/core-math і lib/yantra мають лише .lisp
# (це описи профілю, не машині програми) — вимагати для них пару було б хибним
# спрацюванням. Перевірено: lib/core4.sens Є; core2/core-math/yantra .sens — НЕМАЄ.
EXEMPT_FROM_AUTOREMINT = {"lib/core2.lisp", "lib/core-math.lisp", "lib/yantra.lisp"}


def changed_paths(base: str, head: str) -> set[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", base, head],
        capture_output=True, text=True, check=True).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("base", help="базовий коміт (напр. BEFORE_SHA)")
    ap.add_argument("head", nargs="?", default="HEAD")
    args = ap.parse_args(argv)

    changed = changed_paths(args.base, args.head)
    bad: list[str] = []
    for source, pair in PAIRS.items():
        if source in changed and pair not in changed:
            bad.append(f"{source} змінено, а {pair} — НІ")
    # Виключені з автопере-карбування: вимагаємо пару ЛИШЕ якщо вона існує.
    # Інакше — хибне спрацювання на джерелах без фізичної пари.
    root = Path(__file__).resolve().parents[1]
    for source in sorted(EXEMPT_FROM_AUTOREMINT):
        pair = source[:-len(".lisp")] + ".sens"
        if not (root / pair).is_file():
            continue                      # пари немає — вимога не застосовна
        if source in changed and pair not in changed:
            bad.append(f"{source} змінено, а {pair} — НІ (виключений з автопере-карбування)")

    print(f"CORE4_PAIR: змінених шляхів={len(changed)} проблем={len(bad)}")
    for b in bad:
        print(f"::error title=CORE4_PAIR_DRIFT::REGRESSION id=core4-pair-together "
              f"layer=pairing expected=source-and-pair-together actual=source-only {b}")
    if bad:
        print("CORE4_PAIR: FAIL — джерело і фізична пара мусять змінюватися разом")
        return 1
    print("CORE4_PAIR: PASS — кожне змінене джерело має свою пару в тому ж дифі")
    return 0


if __name__ == "__main__":
    sys.exit(main())
