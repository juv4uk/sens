#!/usr/bin/env python3
"""Кількість .lisp, які ПОВНІСТЮ набираються українською розкладкою.

Перевіряється весь вміст кожного файла без винятків: код, коментарі, текстові
рядки, пробіли та розділові знаки. Латинська літера навіть у коментарі означає,
що файл не відповідає вимозі. Порожні, непрочитані файли та символьні посилання
не зараховуються до завершених.

Це суто звіт (без блокування міграції та перевірки виконання SENS).

    python3 scripts/report_ukr_projection_progress.py
    python3 scripts/report_ukr_projection_progress.py --list --top 20
    python3 scripts/report_ukr_projection_progress.py --json /tmp/ukr-files.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Фізично доступні символи української розкладки Ukrainian (Enhanced).
# Узгоджено з UKRAINIAN_KEYBOARD_OUTPUTS у check_ukr_callsite_migration.py.
UKRAINIAN_KEYBOARD_OUTPUTS = set(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
    "\t\r\n"
)


def iter_lisp_files(root: Path) -> list[Path]:
    """Усі .lisp у дереві, незалежно від каталогу й призначення файла."""
    return sorted(
        (p for p in root.rglob("*.lisp")
         if ".git" not in p.relative_to(root).parts),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def check_file(path: Path) -> dict | None:
    """None — весь непорожній файл відповідає клавіатурі; dict — перша вада."""
    if path.is_symlink():
        return {"reason": "символьне посилання (вміст не перевірено)"}
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeError, OSError) as exc:
        return {"reason": "неможливо прочитати UTF-8", "detail": type(exc).__name__}

    if not source.strip():
        return {"reason": "порожній файл"}

    for offset, ch in enumerate(source):
        if ch not in UKRAINIAN_KEYBOARD_OUTPUTS:
            last_newline = source.rfind("\n", 0, offset)
            return {
                "reason": "символ поза українською розкладкою",
                "line": source.count("\n", 0, offset) + 1,
                "column": offset - last_newline,
                "character": ch,
                "unicode": f"U+{ord(ch):04X}",
            }
    return None


def measure(root: Path) -> dict:
    """Один пофайловий показник з детермінованим списком невідповідностей."""
    root = root.resolve()
    files = iter_lisp_files(root)
    pending = []
    for path in files:
        issue = check_file(path)
        if issue is not None:
            pending.append({"path": path.relative_to(root).as_posix(), **issue})
    total = len(files)
    fully_ukrainian = total - len(pending)
    return {
        "files_total": total,
        "files_fully_ukrainian": fully_ukrainian,
        "files_remaining": len(pending),
        "pct": round(100.0 * fully_ukrainian / total, 1) if total else 0.0,
        "pending_files": pending,
    }


def render(report: dict) -> str:
    return (f"ПОВНІСТЮ УКРАЇНСЬКІ .lisp: "
            f"{report['files_fully_ukrainian']}/{report['files_total']} "
            f"({report['pct']:.1f}%); "
            f"залишилося {report['files_remaining']} файлів")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(ROOT), help="корінь репозиторію")
    parser.add_argument("--json", metavar="PATH", help="зберегти цей самий звіт у JSON")
    parser.add_argument("--list", action="store_true", help="перелічити файли, що не відповідають")
    parser.add_argument("--top", type=int, default=0,
                        help="показати перші N невідповідностей (0 = усі)")
    parser.add_argument("--no-annotation", action="store_true",
                        help="не створювати інформаційну анотацію GitHub Actions")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir() or args.top < 0:
        print("::error::недійсний --root або --top", file=sys.stderr)
        return 2

    result = measure(root)
    line = render(result)
    print(line)
    if not args.no_annotation:
        print(f"::notice::{line}")

    if args.list:
        shown = result["pending_files"][:args.top] if args.top else result["pending_files"]
        for item in shown:
            location = (f":{item['line']}:{item['column']}"
                        if "line" in item else "")
            char = (f" {item['unicode']} {item['character']!r}"
                    if "unicode" in item else "")
            print(f"  {item['path']}{location}: {item['reason']}{char}")
        if len(shown) < result["files_remaining"]:
            print(f"  … ще {result['files_remaining'] - len(shown)}")

    if args.json:
        try:
            Path(args.json).write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            print(f"::error::не вдалося записати JSON: {exc}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
