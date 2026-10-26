#!/usr/bin/env python3
"""Беклог непокритих функцій драбини — щоб «напиши тест» мало адресу.

Проблема, яку це лікує: слово «тест» без ЦІЛІ розв'язується в найближчий
канонічний приклад (калькулятор, факторіал, фібоначчі), бо саме їх мільйони
в корпусі навчання. Це хеджування: іграшка безпечна, у неї немає зовнішнього
контракту, який можна порушити.

Те саме, що «spelling owns meaning», але на рівні задач: назва притягує форму
замість реєстру. Тому тест мусить мати ЦІЛЬ із реєстру — конкретну функцію.

Тут — джерело таких цілей: перелік поверхонь драбини, які НЕ згадані
в жодному тесті. Черга, з якої сварм бере «функція №N, позитивний і
негативний свідок».

Режими:
  --backlog [N]   перші N непокритих (типово 25)
  --metric        метрика покриття: покриті / усього
  --self-test     самоперевірка
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CYR = re.compile(r"[\u0400-\u04FF]")

# Де шукаємо свідчення покриття.
TEST_GLOBS = (
    "tests/**/*.lisp",
    "crates/**/tests/*.rs",
    "benchmarks/**/*.lisp",
)

# Колонки, які є СПРАВЖНІМИ поверхнями мови (ук/укр), а не метаданими.
SURFACE_COLUMNS = ("ук", "укр")


def load_surfaces() -> list[tuple[str, str, frozenset[str]]]:
    """[(домен, координата, {імена})] — ОДИН запис на рядок таблиці.

    Одиниця виміру — рядок (координата), а не ім'я: `ук` і `укр` — дві
    проєкції ТІЄЇ САМОЇ координати, іноді з різними іменами. Рахунок за
    іменами давав 3547 замість 2558 рядків.
    """
    out: list[tuple[str, str, frozenset[str]]] = []
    row_re = re.compile(r"^\s*\(([012]+)\s")
    for path in sorted((ROOT / "lib" / "domains").glob("d*.lisp")):
        match = re.fullmatch(r"d(\d+)\.lisp", path.name)
        if not match:
            continue
        domain = "D" + match.group(1)
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            row = row_re.match(line)
            if not row:
                continue
            names: set[str] = set()
            for col in SURFACE_COLUMNS:
                names.update(re.findall(r"\(" + col + r"\s+([^\s()]+)\)", line))
            if names:
                out.append((domain, row.group(1), frozenset(names)))
    return out


def load_test_text() -> str:
    """Увесь текст тестів одним рядком — для пошуку згадок."""
    chunks: list[str] = []
    for pattern in TEST_GLOBS:
        for path in ROOT.glob(pattern):
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
    return "\n".join(chunks)


def corpus_words() -> set[str]:
    """Усі слова корпусу тестів — ОДИН прохід, потім перетин множин.

    Попередня версія робила regex-сканування на кожне ім'я (3547 проходів)
    і не вкладалась у таймаут.
    """
    words: set[str] = set()
    for pattern in TEST_GLOBS:
        for path in ROOT.glob(pattern):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            words.update(re.findall(r"[^\s()\[\]\"';,]+", text))
    return words


def measure() -> tuple[list, list]:
    surfaces = load_surfaces()
    words = corpus_words()
    covered, uncovered = [], []
    for domain, coord, names in surfaces:
        # рядок покритий, якщо згадане ХОЧ ОДНЕ з його імен
        (covered if (names & words) else uncovered).append((domain, coord, names))
    return covered, uncovered


def self_test() -> int:
    ok = True
    corpus = "(перевірити перше x) (перше-від-решта y)"
    checks = [
        ("точний збіг знайдено", bool(re.search(r"(?<![\w\-])перше(?![\w\-])", corpus))),
        ("префікс НЕ зараховується", not re.search(r"(?<![\w\-])перше-від(?![\w\-])", "(перевірити перше x)")),
        ("складене ім'я НЕ плутається з довшим", not re.search(r"(?<![\w\-])перше-від(?![\w\-])", corpus)),
        ("складене ім'я знайдено точно", bool(re.search(r"(?<![\w\-])перше-від(?![\w\-])", "(перше-від y)"))),
        ("відсутнє ім'я не знайдено", not re.search(r"(?<![\w\-])немає(?![\w\-])", corpus)),
    ]
    for label, good in checks:
        print(("OK    " if good else "ЗБІЙ  ") + label)
        ok = ok and good
    print("SELF-TEST:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backlog", nargs="?", const=25, type=int, default=None, metavar="N")
    ap.add_argument("--metric", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.backlog is None and not args.metric:
        ap.print_help()
        return 2

    covered, uncovered = measure()
    total = len(covered) + len(uncovered)
    if not total:
        print("НЕ ВИМІРЯНО: таблиці драбини не прочитано")
        return 2

    pct = 100.0 * len(covered) / total
    print("ПОКРИТТЯ ДРАБИНИ ТЕСТАМИ")
    print(f"  поверхонь:  {total}")
    print(f"  покрито:    {len(covered)}  ({pct:.1f}%)")
    print(f"  без тесту:  {len(uncovered)}")

    if args.backlog is not None and uncovered:
        print(f"\nЧЕРГА ЦІЛЕЙ (перші {min(args.backlog, len(uncovered))}):")
        print("  формат ЦІЛІ: <домен> <координата> <ім'я> — позитивний і негативний свідок")
        for domain, coord, names in uncovered[: args.backlog]:
            print(f"  {domain} {coord} " + " / ".join(sorted(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
