#!/usr/bin/env python3
"""Гра «Драбина»: охоронець не лише блокує — він запрошує й винагороджує.

Охоронець карає за дубль. Ця гра робить протилежне: показує РІВНІ (домени),
ПРОГРЕС (скільки файлів мовних свідків уже створено) і НАСТУПНИЙ КВЕСТ — що саме
дописати. Мета — щоб писати лісп було цікаво, а не лише «не заборонено».

    python3 scripts/domain-game.py            # показати рівні, прогрес, квест
    python3 scripts/domain-game.py --brief    # один рядок
    python3 scripts/domain-game.py --codec    # квести експериментального кодеку
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
    ("D5", "оператори та мовні функції"),
    ("D6", "селектори й похідні"),
    ("D7", "клавіатура/проєкція"),
    ("D8", "рядки, масиви, властивості"),
    ("D9", "сховище, файли"),
    ("D10", "бібліотеки й сімейства"),
    ("D11", "нові сімейства й селекторні похідні"),
    ("D12", "найменший ратифікований математичний домен"),
    ("D24", "наступна математична сходинка"),
]



# Артефакти для наступних експериментів. Наявність файла — не доказ PASS.
# Семантичні пари виконуються SENS; механіка нового кодека перевіряється Zig.
CODEC_QUESTS = [
    ("C12-01", "D12: додатне й від'ємне ціле", "SENS", (
        "tests/semantic/d12-signed-width-law.lisp",
        "tests/semantic/d12-signed-width-mutant.lisp")),
    ("C12-02", "D12: крайні допустимі значення", "SENS", (
        "tests/semantic/d12-signed-boundary-law.lisp",
        "tests/semantic/d12-signed-boundary-mutant.lisp")),
    ("C12-03", "D12 → D24 без переповнення і втрати", "SENS", (
        "tests/semantic/d12-widen-to-d24-law.lisp",
        "tests/semantic/d12-widen-to-d24-mutant.lisp")),
    ("C12-04", "Точний скорочений дріб 1/3", "SENS", (
        "tests/semantic/d12-ratio-exact-law.lisp",
        "tests/semantic/d12-ratio-exact-mutant.lisp")),
    ("C12-05", "Нульовий знаменник: точна відмова", "SENS", (
        "tests/semantic/d12-ratio-zero-law.lisp",
        "tests/semantic/d12-ratio-zero-mutant.lisp")),
    ("C12-06", "Float не підміняє точний RATIO", "SENS", (
        "tests/semantic/d12-ratio-float-distinct-law.lisp",
        "tests/semantic/d12-ratio-float-distinct-mutant.lisp")),
    ("C12-07", "Експериментальний Zig-кодек: точний round-trip", "Zig", (
        "research/zig-codecs/experimental_numeric_codec.zig",)),
    ("C12-08", "Zig: відхилити неоднозначні 22/222 і хвіст", "Zig", (
        "research/zig-codecs/experimental_numeric_codec_test.zig",)),
]


def codec_progress() -> list[tuple[str, str, str, int, int, tuple[str, ...]]]:
    """Тільки присутність git-tracked артефактів; не тестовий вердикт."""
    paths = set(tracked("tests/semantic/*.lisp"))
    paths.update(tracked("research/zig-codecs/*.zig"))
    return [(qid, desc, layer, sum(path in paths for path in required),
             len(required), required)
            for qid, desc, layer, required in CODEC_QUESTS]


def codec_game(brief: bool) -> int:
    rows = codec_progress()
    ready = sum(present == needed for _, _, _, present, needed, _ in rows)
    if brief:
        print(f"ДРАБИНА-КОДЕК: артефактів-квестів {ready}/{len(rows)}; "
              "наявність файлів не означає PASS")
        return 0

    print("═══ ГРА «ДРАБИНА» · ЕКСПЕРИМЕНТАЛЬНИЙ КОДЕК ═══")
    print("Мета: D12+ без втрати точності, без JSON і без хостової семантики.\n")
    for qid, desc, layer, present, needed, _ in rows:
        print(f"{qid} [{layer}] {present}/{needed} файлів — {desc}")
    print(f"\nЗібрано комплектів артефактів: {ready}/{len(rows)}")
    unfinished = next((row for row in rows if row[3] < row[4]), None)
    if unfinished:
        qid, desc, _, _, _, required = unfinished
        present_paths = set(tracked("tests/semantic/*.lisp"))
        present_paths.update(tracked("research/zig-codecs/*.zig"))
        print(f"\nНАСТУПНИЙ КВЕСТ: {qid} — {desc}")
        for path in required:
            if path not in present_paths:
                print(f"  + {path}")
    print("\nУвага: наявність файлів не означає PASS. "
          "Лісп мусить пройти в SENS, Zig — виконати фізичний тест.")
    return 0

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
    ap.add_argument("--codec", action="store_true", help="квести експериментального числового кодеку")
    args = ap.parse_args(argv)
    if args.codec:
        return codec_game(args.brief)
    prog = progress()
    total = sum(prog.values())
    if args.brief:
        print(f"ДРАБИНА: рівнів {len(LEVELS)}, файлів-свідків {total}, "
              f"найповніший {max(prog, key=prog.get) if prog else '—'}")
        return 0

    print("═══ ГРА «ДРАБИНА» ═══")
    print("Охоронець карає за дубль. Гра винагороджує за нове.\n")
    print(f"{'рівень':<6} {'файлів':>7}  опис")
    for dom, desc in LEVELS:
        n = prog.get(dom, 0)
        bar = "█" * min(n // 5, 20)
        print(f"{dom:<6} {n:>7}  {bar} {desc}")
    print(f"\nУсього .lisp-файлів із доменним префіксом: {total}")
    # АВТОКВЕСТ: гра сама обирає найпорожніший рівень — не треба вгадувати.
    ranked = sorted(LEVELS, key=lambda kv: prog.get(kv[0], 0))
    gaps = ranked[:3]
    print("\nНАСТУПНИЙ КВЕСТ (обрано за найменшим числом файлів-свідків):")
    for dom, desc in gaps:
        n = prog.get(dom, 0)
        print(f"  ★ {dom} — лише {n} файлів. {desc}")
    dom, desc = gaps[0]
    print(f"\n  Бери {dom}. Кроки:")
    print("    1) python3 scripts/new-program.py <назва>   # сам шукає наявне")
    print("    2) напиши закон ліспом: закон → D1:1, мутант → D1:0")
    print("    3) охоронець перевірить → кодек перетворить у SENS")
    print(f"\n  Обери щось із теми «{desc}» і додай першу пару.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
