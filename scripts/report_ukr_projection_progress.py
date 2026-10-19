#!/usr/bin/env python3
"""Підрахунок повністю українських файлів .lisp у репозиторії SENS.

Файл зараховується лише тоді, коли КОЖЕН символ його вмісту можна
надрукувати українською клавіатурою: у коді, коментарях, рядках,
цитованих даних і поза ними. Пробіл, Tab і Enter дозволені.
Не зараховуються порожні файли, файли лише з пробільних символів,
пошкоджений UTF-8 і символічні посилання.

Враховуються всі .lisp у дереві, включно з історичними джерелами,
таблицями доменів і тестами. Викличні голови та пари ук/укр НЕ
впливають на цей показник. Це перевірка символів, не семантики SENS.

Використання:
  python3 scripts/report_ukr_projection_progress.py
  python3 scripts/report_ukr_projection_progress.py --list --top 10
  python3 scripts/report_ukr_projection_progress.py --json ukr-files.json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ратифікований у репозиторії набір символів української розкладки
# (Microsoft Ukrainian Enhanced). Додатково дозволені клавіші
# Enter і Tab; CR/LF підтримують обидва поширені формати рядків.
UKRAINIAN_KEYBOARD_OUTPUTS = frozenset(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
    "\t\r\n"
)


@dataclass(frozen=True)
class IncompleteFile:
    path: str
    reason: str


@dataclass(frozen=True)
class Progress:
    total_lisp_files: int
    fully_ukrainian_files: int
    pending: tuple[IncompleteFile, ...] = field(default_factory=tuple)

    @property
    def percent(self) -> float:
        return round(
            100 * self.fully_ukrainian_files / self.total_lisp_files, 1
        ) if self.total_lisp_files else 0.0

    def to_dict(self) -> dict:
        # JSON містить ЛИШЕ замовлену метрику й її знаменник.
        return {
            "fully_ukrainian_files": self.fully_ukrainian_files,
            "total_lisp_files": self.total_lisp_files,
            "percent": self.percent,
        }


def iter_lisp_files(root: Path) -> list[Path]:
    """Усі .lisp незалежно від призначення; .git — не код репозиторію."""
    return sorted(
        path for path in root.rglob("*.lisp")
        if ".git" not in path.relative_to(root).parts
    )


def inspect_file(path: Path, root: Path) -> IncompleteFile | None:
    rel = path.relative_to(root).as_posix()
    if path.is_symlink():
        return IncompleteFile(rel, "символічне посилання")
    try:
        # Читаємо байти без заміни або ігнорування пошкоджених символів.
        # Це зберігає і CRLF, і точні Unicode-символи.
        source = path.read_bytes().decode("utf-8", errors="strict")
    except (UnicodeError, OSError):
        return IncompleteFile(rel, "нечитабельний файл або некоректний UTF-8")
    if not source.strip():
        return IncompleteFile(rel, "порожній файл")

    for line, text_line in enumerate(source.splitlines(keepends=True), 1):
        for column, char in enumerate(text_line, 1):
            if char not in UKRAINIAN_KEYBOARD_OUTPUTS:
                return IncompleteFile(
                    rel, f"{line}:{column} недоступний символ U+{ord(char):04X}"
                )
    return None


def measure(root: Path) -> Progress:
    root = root.resolve()
    paths = iter_lisp_files(root)
    pending = tuple(
        finding
        for path in paths
        if (finding := inspect_file(path, root)) is not None
    )
    return Progress(
        total_lisp_files=len(paths),
        fully_ukrainian_files=len(paths) - len(pending),
        pending=pending,
    )


def render(progress: Progress) -> str:
    return (
        f"УКР-ПРОЄКЦІЯ: повністю українські файли .lisp — "
        f"{progress.fully_ukrainian_files}/{progress.total_lisp_files} "
        f"({progress.percent:.1f}%)"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT, help="корінь дерева файлів")
    ap.add_argument("--json", type=Path, help="записати лише підсумкову метрику")
    ap.add_argument("--list", action="store_true",
                    help="додатково перелічити файли, які ще не відповідають вимозі")
    ap.add_argument("--top", type=int, default=0,
                    help="обмеження --list; 0 означає всі")
    # Старі запуски CI передають цей параметр; звіт тепер не створює анотацій.
    ap.add_argument("--no-annotation", action="store_true",
                    help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if args.top < 0 or not args.root.is_dir():
        ap.error("неправильний --top або відсутній каталог --root")

    result = measure(args.root)
    print(render(result))

    if args.list:
        selected = result.pending[:args.top] if args.top else result.pending
        for item in selected:
            print(f"{item.path}: {item.reason}")

    if args.json is not None:
        args.json.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
