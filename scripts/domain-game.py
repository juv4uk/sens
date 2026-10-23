#!/usr/bin/env python3
"""Гра «Драбина»: окремі щаблі мовних законів і експериментів кодеку.

    python3 scripts/domain-game.py
    python3 scripts/domain-game.py --brief
    python3 scripts/domain-game.py --track codec
    python3 scripts/domain-game.py --track codec --verify

Мовні файли — не тотожні доведеним законам. Codec-щабель зараховується
лише після успішного нативного Zig test; Python не перевіряє семантику SENS.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENSE = Path("research/zig-codecs/d12_dense_experiment.zig")

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

# Опис квестів. Назви повинні точно збігатися з нативними Zig test.
# None = наступний квест, якому ще бракує нативного тесту/реалізації.
CODEC_LEVELS = [
    ("C1", "Межі й порядок 12-бітних слів", (
        "D12 dense fixed vector preserves boundaries and leading zeros",
        "D12 dense exact byte ordering and run lengths",
    )),
    ("C2", "Усі 4096 значень із доповняльним партнером", (
        "D12 dense exhaustive 4096 raw words with complementary partner",
    )),
    ("C3", "Відмова без часткового запису", (
        "D12 dense rejects invalid payload without modifying output",
    )),
    ("C4", "Реальні довгі й непарні цикли encode/decode/reencode", (
        "D12 dense long and odd runs preserve bytes on reencode",
    )),
    ("C5", "Явний кадр: версія, домен, довжина, цілісність", None),
]


def tracked(pattern: str) -> list[str]:
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", pattern],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def progress() -> Counter:
    """Кількість ФАЙЛІВ за префіксом домену, не число доведених законів."""
    c: Counter = Counter()
    for p in tracked("tests/semantic/*.lisp"):
        name = Path(p).stem.lower()
        m = re.match(r"d(\d+)", name)
        if m:
            c[f"D{m.group(1)}"] += 1
    return c


def visible_levels(counts: Counter) -> list[tuple[str, str]]:
    """Показати всі домени з файлами, не надаючи їм нової ратифікації."""
    known = {domain for domain, _ in LEVELS}
    extra = sorted(
        (domain for domain in counts if domain not in known),
        key=lambda domain: int(domain[1:]),
    )
    descriptions = {
        "D24": "точна математика: числові закони та негативні свідки",
    }
    return LEVELS + [
        (domain, descriptions.get(domain, "виявлені файли; звірити доменний контракт"))
        for domain in extra
    ]


def semantic_game(brief: bool) -> int:
    prog = progress()
    total = sum(prog.values())
    levels = visible_levels(prog)
    if brief:
        print(f"ДРАБИНА: рівнів {len(levels)}, файлів Lisp {total}, "
              f"найбільше {max(prog, key=prog.get) if prog else '—'}")
        return 0

    print("═══ ГРА «ДРАБИНА» / МОВА ═══")
    print("Лічильник показує файли, не результат виконання законів.\n")
    print(f"{'рівень':<6} {'файлів':>7}  опис")
    for dom, desc in levels:
        n = prog.get(dom, 0)
        bar = "█" * min(n // 5, 20)
        print(f"{dom:<6} {n:>7}  {bar} {desc}")
    print(f"\nУсього файлів Lisp із доменним префіксом: {total}")
    ranked = sorted(levels, key=lambda kv: prog.get(kv[0], 0))
    gaps = ranked[:3]
    print("\nНАСТУПНИЙ КВЕСТ (найменше файлів):")
    for dom, desc in gaps:
        print(f"  ★ {dom} — {prog.get(dom, 0)} файлів. {desc}")
    dom, desc = gaps[0]
    print(f"\n  Бери {dom}. Кроки:")
    print("    1) python3 scripts/new-program.py <назва>")
    print("    2) напиши закон ліспом: закон → D1:1, мутант → D1:0")
    print("    3) охоронець перевірить → кодек перетворить у SENS")
    print(f"\n  Обери щось із теми «{desc}» і додай наступну пару.")
    print("\nЕКСПЕРИМЕНТ КОДЕКУ — підмножина D2 без крапки (11):")
    print("    ★ перевірка: 243/243 груп, пошкоджені байти, неканонічні хвости")
    print("    ★ D2:11 (крапка) за межами цього досліду: повний D2 має 4 слова")
    print("    ★ виграш: 20 D2 → 4 байти проти 5 сирих")
    print("    ★ чесна межа: у змішаному CAAR 10 серій → 10 байтів без карти позицій")
    print("    перевірка: zig test research/zig-codecs/d2_ladder_game.zig")
    return 0


def codec_game(brief: bool, verify: bool) -> int:
    source_path = ROOT / DENSE
    source = source_path.read_text(encoding="utf-8") if source_path.is_file() else ""
    declared = set(re.findall(r'^test "([^"]+)"', source, flags=re.MULTILINE))
    present = {
        code: tests is not None and all(name in declared for name in tests)
        for code, _, tests in CODEC_LEVELS
    }
    tested = False
    return_code = 0
    zig_version = "NOT_RUN"
    if verify:
        if not source:
            print(f"НЕМАЄ ФАЙЛУ: {DENSE}", file=sys.stderr)
            return 2
        try:
            version = subprocess.run(
                ["zig", "version"], cwd=ROOT, capture_output=True, text=True,
            )
            zig_version = version.stdout.strip() or "UNKNOWN"
            result = subprocess.run(
                ["zig", "test", "-lc", str(DENSE)],
                cwd=ROOT, capture_output=True, text=True,
            )
        except FileNotFoundError:
            print("Zig недоступний: щаблі не зараховано.", file=sys.stderr)
            return 2
        # Відсутній запуск тестів не дає очок навіть при exit=0.
        output = result.stdout + result.stderr
        executed = re.search(r"All\s+[1-9]\d*\s+tests?\s+passed", output) is not None
        tested = result.returncode == 0 and executed and any(present.values())
        return_code = 0 if tested else 1
        if not tested:
            print(output, file=sys.stderr)
            print("Немає підтвердженого ненульового PASS Zig; очки не нараховано.", file=sys.stderr)
    score = sum(1 for code, _, _ in CODEC_LEVELS if tested and present[code])
    proof = "PASS" if tested else ("FAIL" if verify else "NOT_RUN")
    if brief:
        print(f"ДРАБИНА/CODEC: verified={score}/{len(CODEC_LEVELS)} "
              f"native={proof} semantics=NOT_TESTED")
        return return_code

    print("═══ ГРА «ДРАБИНА» / DENSE-D12 ═══")
    print("Фізичний 12-бітний payload; не самодостатній кадр.")
    print("Семантика чисел і SENS: NOT_TESTED.\n")
    for code, desc, tests in CODEC_LEVELS:
        status = "ДОВЕДЕНО" if tested and present[code] else (
            "Є ТЕСТ / НЕ ЗАПУЩЕНО" if present[code] else "ЩЕ НЕМАЄ"
        )
        print(f"  {code}  [{status}] {desc}")
    print(f"\nНагорода: {score}/{len(CODEC_LEVELS)} доведених щаблів; Zig={proof}")
    if verify:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
        ).stdout.strip()
        blob = subprocess.run(
            ["git", "hash-object", str(DENSE)], cwd=ROOT, capture_output=True, text=True,
        ).stdout.strip()
        print(f"Свідчення запуску: commit={sha or 'UNKNOWN'} blob={blob or 'UNKNOWN'} zig={zig_version}")
        print(f"Команда: zig test -lc {DENSE}")
    if not tested:
        print("\nНАСТУПНИЙ ХІД: zig test -lc "
              f"{DENSE}  (або --track codec --verify)")
    else:
        missing = next((code for code, _, _ in CODEC_LEVELS if not present[code]), None)
        if missing:
            print(f"\nНАСТУПНИЙ КВЕСТ: {missing} — реалізуй і перевір нативним Zig.")
        else:
            print("\nУсі описані щаблі пройшли нативну перевірку.")
    return return_code


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="гра «Драбина»")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--track", choices=("semantic", "codec"), default="semantic")
    ap.add_argument("--verify", action="store_true",
                    help="запустити нативний Zig test лише для --track codec")
    args = ap.parse_args(argv)
    if args.verify and args.track != "codec":
        ap.error("--verify дозволено лише з --track codec")
    if args.track == "codec":
        return codec_game(args.brief, args.verify)
    return semantic_game(args.brief)


if __name__ == "__main__":
    sys.exit(main())
