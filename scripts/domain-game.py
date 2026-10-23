#!/usr/bin/env python3
"""Гра «Драбина»: охоронець не лише блокує — він запрошує й винагороджує.

Охоронець карає за дубль. Ця гра робить протилежне: показує РІВНІ (домени),
ПРОГРЕС (скільки мовних законів уже написано) і НАСТУПНИЙ КВЕСТ — що саме
дописати. Мета — щоб писати лісп було цікаво, а не лише «не заборонено».

    python3 scripts/domain-game.py            # показати рівні, прогрес, квест
    python3 scripts/domain-game.py --brief    # один рядок
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LEVELS = [
    ("D1", "основа: тотожність, атом, хибне/істинне"),
    ("D2", "порожнє/пропуск"),
    ("D3", "списки: перше, решта, сполучити"),
    ("D4", "керування: за-умовою, функція, визначити"),
    ("D5", "числа"),
    ("D6", "селектори й похідні"),
    ("D7", "клавіатура/проєкція"),
    ("D8", "рядки, масиви, властивості"),
    ("D9", "сховище, файли"),
    ("D10", "бібліотеки й сімейства"),
    ("D11", "НОВІ сімейства (селекторні похідні, кандидати)"),
]


def tracked(pattern: str) -> list[str]:
    out = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", pattern],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def progress() -> Counter:
    """Скільки законів/мутантів на кожен домен (за префіксом імені файлу)."""
    c: Counter = Counter()
    for p in tracked("tests/semantic/*.lisp"):
        name = Path(p).stem.lower()
        m = re.match(r"d(\d+)", name)
        if m:
            c[f"D{m.group(1)}"] += 1
    return c


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="гра «Драбина»")
    ap.add_argument("--brief", action="store_true")
    args = ap.parse_args(argv)
    prog = progress()
    total = sum(prog.values())
    if args.brief:
        print(f"ДРАБИНА: рівнів {len(LEVELS)}, законів {total}, "
              f"найповніший {max(prog, key=prog.get) if prog else '—'}")
        return 0

    print("═══ ГРА «ДРАБИНА» ═══")
    print("Охоронець карає за дубль. Гра винагороджує за нове.\n")
    print(f"{'рівень':<6} {'законів':>7}  опис")
    for dom, desc in LEVELS:
        n = prog.get(dom, 0)
        bar = "█" * min(n // 5, 20)
        print(f"{dom:<6} {n:>7}  {bar} {desc}")
    print(f"\nУсього мовних законів: {total}")
    print("\nНАСТУПНИЙ КВЕСТ:")
    print("  • обери рівень із найменшим числом законів вище;")
    print("  • створи пару: python3 scripts/new-program.py <назва> (він сам шукає наявне);")
    print("  • напиши закон ліспом у tests/semantic/ (закон → D1:1, мутант → D1:0);")
    print("  • охоронець перевірить, кодек перетворить у SENS.")
    print("\nПриклад: D3 «списки» — напиши закон про перше/решта/сполучити.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
