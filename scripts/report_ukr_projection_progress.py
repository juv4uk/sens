#!/usr/bin/env python3
"""Єдиний показник міграції: повністю українські файли .lisp.

Файл зараховується, якщо КОЖЕН символ його повного вмісту можна набрати
українською розкладкою клавіатури. Коментарі, літерали, цитовані дані,
пробіли та переводи рядків перевіряються так само, як виконуваний код.
Жодні каталоги (зокрема історичні) не вилучаються зі знаменника.
Неправильний UTF-8, недоступний файл і символ поза розкладкою не
зараховуються. Порожній файл формально задовольняє вимогу «кожен символ».
Ця метрика не стверджує семантичної правильності чи працездатності SENS.

Використання:
    python3 scripts/report_ukr_projection_progress.py
    python3 scripts/report_ukr_projection_progress.py --list --top 20
    python3 scripts/report_ukr_projection_progress.py --json результат.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Ті самі символи Microsoft Ukrainian Enhanced, що й у чинних правилах
# проєкції доменів. Enter, Tab і CR/LF дозволені як клавіші керування.
UKRAINIAN_KEYBOARD_OUTPUTS = set(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
)
KEYBOARD_WHITESPACE = set("\t\r\n")
ALLOWED = UKRAINIAN_KEYBOARD_OUTPUTS | KEYBOARD_WHITESPACE


@dataclass(frozen=True)
class Unfinished:
    path: str
    reason: str


@dataclass(frozen=True)
class Progress:
    total_lisp_files: int
    full_ukr_files: int
    unfinished: tuple[Unfinished, ...]

    @property
    def percentage(self) -> float:
        return round(self.full_ukr_files * 100 / self.total_lisp_files, 1) if self.total_lisp_files else 0.0

    def to_dict(self) -> dict:
        return {
            "total_lisp_files": self.total_lisp_files,
            "full_ukr_files": self.full_ukr_files,
            "percentage": self.percentage,
        }


def iter_lisp_files(root: Path) -> list[Path]:
    """Усі файли .lisp в усьому дереві; без спеціальних винятків."""
    return sorted(
        (path for path in root.rglob("*.lisp") if ".git" not in path.relative_to(root).parts),
        key=lambda path: path.relative_to(root).as_posix(),
    )


def examine_file(path: Path) -> str | None:
    """None — усі символи доступні; інакше діагноз першої проблеми."""
    if path.is_symlink():
        return "символічне посилання (не є самостійним вмістом файла)"
    try:
        source = path.read_bytes().decode("utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        return f"непрочитаний файл або неправильний UTF-8: {type(exc).__name__}"
    for offset, char in enumerate(source):
        if char not in ALLOWED:
            line = source.count("\n", 0, offset) + 1
            column = offset - source.rfind("\n", 0, offset)
            return f"{line}:{column}: U+{ord(char):04X} {char!r}"
    return None


def measure(root: Path) -> Progress:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    files = iter_lisp_files(root)
    unfinished = []
    for path in files:
        reason = examine_file(path)
        if reason is not None:
            unfinished.append(Unfinished(path.relative_to(root).as_posix(), reason))
    return Progress(
        total_lisp_files=len(files),
        full_ukr_files=len(files) - len(unfinished),
        unfinished=tuple(unfinished),
    )


def render(progress: Progress) -> str:
    return (f"УКР-ПРОЄКЦІЯ .lisp: повністю українські файли "
            f"{progress.full_ukr_files}/{progress.total_lisp_files} "
            f"({progress.percentage:.1f}%)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="коренева тека всіх .lisp")
    parser.add_argument("--json", type=Path, default=None,
                        help="записати лише три показники у JSON")
    parser.add_argument("--list", action="store_true",
                        help="перелічити файли з недоступними символами")
    parser.add_argument("--top", type=int, default=0,
                        help="кількість рядків у --list, 0 означає всі")
    parser.add_argument("--no-annotation", action="store_true",
                        help="не створювати інформаційну позначку GitHub")
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"::error::--root не є текою: {args.root}", file=sys.stderr)
        return 2
    if args.top < 0:
        parser.error("--top має бути невід'ємним")

    progress = measure(args.root)
    message = render(progress)
    print(message)
    if not args.no_annotation and os.getenv("GITHUB_ACTIONS") == "true":
        print(f"::notice::{message}")

    if args.list:
        pending = progress.unfinished
        shown = pending[:args.top] if args.top else pending
        for item in shown:
            print(f"{item.path}: {item.reason}")
        if args.top and len(pending) > args.top:
            print(f"… ще {len(pending) - args.top}")

    if args.json is not None:
        args.json.write_text(
            json.dumps(progress.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
