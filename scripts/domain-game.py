#!/usr/bin/env python3
"""Гра «Драбина»: охоронець не лише блокує — він запрошує й винагороджує.

Охоронець карає за дубль. Ця гра робить протилежне: показує РІВНІ (домени),
ПРОГРЕС (скільки семантичних сценаріїв уже написано) і НАСТУПНИЙ КВЕСТ — що саме
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
    ("D2", "структура й керування: межі, розділювачі, ліниві гілки"),
    ("D3", "списки: перше, решта, сполучити"),
    ("D4", "селектори: CAAR, CADR, CDAR, CDDR"),
    ("D5", "bootstrap: LAMBDA, DEFINE, EVAL та похідні"),
    ("D6", "селектори й похідні"),
    ("D7", "клавіатура/проєкція"),
    ("D8", "рядки, масиви, властивості"),
    ("D9", "сховище, файли"),
    ("D10", "бібліотеки й сімейства"),
    ("D11", "НОВІ сімейства (селекторні похідні, кандидати)"),
    ("D12", "початок математики: малі точні числа"),
]


def tracked(pattern: str) -> list[str]:
    out = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", pattern],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def progress() -> Counter:
    """Кількість сценаріїв, включно з законами, мутантами й негативними тестами."""
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
        print(f"ДРАБИНА: рівнів {len(LEVELS)}, сценаріїв {total}, "
              f"найповніший {max(prog, key=prog.get) if prog else '—'}")
        return 0

    print("═══ ГРА «ДРАБИНА» ═══")
    print("Охоронець карає за дубль. Гра винагороджує за нове.\n")
    print(f"{'рівень':<6} {'сценар.':>7}  опис")
    for dom, desc in LEVELS:
        n = prog.get(dom, 0)
        bar = "█" * min(n // 5, 20)
        print(f"{dom:<6} {n:>7}  {bar} {desc}")
    print(f"\nУсього семантичних сценаріїв: {total}")
    # АВТОКВЕСТ: гра сама обирає найпорожніший рівень — не треба вгадувати.
    ranked = sorted(LEVELS, key=lambda kv: prog.get(kv[0], 0))
    gaps = ranked[:3]
    print("\nНАСТУПНИЙ КВЕСТ (обрано за найменшим числом сценаріїв):")
    for dom, desc in gaps:
        n = prog.get(dom, 0)
        print(f"  ★ {dom} — лише {n} сценаріїв. {desc}")
    dom, desc = gaps[0]
    print(f"\n  Бери {dom}. Кроки:")
    print("    1) python3 scripts/new-program.py <назва>   # сам шукає наявне")
    print("    2) напиши закон ліспом: закон → D1:1, мутант → D1:0")
    print("    3) охоронець перевірить → кодек перетворить у SENS")
    print(f"\n  Обери щось із теми «{desc}» і додай наступну пару.")
    print("\nЕКСПЕРИМЕНТ КОДЕКУ — D2/п’ять тритів:")
    print("    ★ точність: 243/243 груп і неканонічні хвости")
    print("    ★ виграш: 20 D2 → 4 байти проти 5 сирих")
    print("    ★ чесна межа: у змішаному CAAR 10 серій → 10 байтів без карти позицій")
    print("    перевірка: zig test research/zig-codecs/d2_ladder_game.zig")
    return 0


if __name__ == "__main__":
    sys.exit(main())
