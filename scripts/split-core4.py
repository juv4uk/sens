#!/usr/bin/env python3
"""Розбити core4.lisp на блоки й зібрати назад — без зміни поведінки.

Навіщо: core4.lisp — 7321 рядок і 1203 визначення в одному файлі (мова, Д6,
кодек T5M, Д8/Д9). Один збій зачіпає все. Блоки дають межі, за якими видно,
що саме змінюється.

ПРОСТОТА ПЕРВИННА: у мові немає include, тож core4.lisp лишається ТОЧКОЮ ВХОДУ,
а блоки — його складовими. Збірка відтворює байт-у-байт оригінал (--check).

    python3 scripts/split-core4.py --split    # core4.lisp → lib/core4-parts/*.lisp
    python3 scripts/split-core4.py --build    # блоки → lib/core4.lisp
    python3 scripts/split-core4.py --check    # звірити: блоки відтворюють core4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE4 = ROOT / "lib" / "core4.lisp"
PARTS = ROOT / "lib" / "core4-parts"

BLOCKS = [
    ("core4-language", 1, 697, "мова: тотожність, макроси та/або, список, числа, базові предикати"),
    ("core4-d6", 698, 916, "похідні Д6, партії 1-3"),
    ("core4-codec", 917, 1470, "НСД + кодек T5M + T5M3 (упаковка й декодер)"),
    ("core4-d6b", 1471, 2287, "похідні Д6, партії 4-5"),
    ("core4-d8-d9", 2288, None, "Д8/Д9: масиви, рядки, content-store"),
]
HDR = "; core4 · блок «{name}» · рядки {a}–{b} оригіналу\n; {desc}\n" \
      "; Згенеровано scripts/split-core4.py — НЕ редагувати руками; правте блок і перезберіть.\n"


def complete_form_cutoffs(lines: list[str]) -> list[int]:
    """Позиції кінця цілих форм SENS (D2), а не фіксовані рядки.

    Коментарі й екрановані рядки не змінюють структуру. Пошкоджений
    Core4 відхиляємо, а не розрізаємо посеред невизначеної форми.
    """
    depth = 0
    quoted = False
    escaped = False
    safe: list[int] = []
    for line_no, line in enumerate(lines, 1):
        for char in line:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == ";":
                break
            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    raise SystemExit(f"Core4: зайва ')' у рядку {line_no}")
        if depth == 0 and not quoted:
            safe.append(line_no)
    if depth != 0 or quoted:
        raise SystemExit("Core4: незакрита форма або рядок")

    chosen: list[int] = []
    previous = 0
    for _name, _start, end, _description in BLOCKS[:-1]:
        possible = [position for position in safe if position > previous]
        if not possible:
            raise SystemExit("Core4: немає безпечної межі частини")
        cut = min(possible, key=lambda position: (abs(position - end), position))
        chosen.append(cut)
        previous = cut
    return chosen


def expected_parts(lines: list[str]) -> list[tuple[Path, str]]:
    cuts = [0, *complete_form_cutoffs(lines), len(lines)]
    rendered = []
    for i, (name, _a, _b, desc) in enumerate(BLOCKS):
        a, b = cuts[i] + 1, cuts[i + 1]
        segment = lines[a - 1:b]
        content = HDR.format(name=name, a=a, b=b, desc=desc) + "\n".join(segment) + "\n"
        rendered.append((PARTS / f"{name}.lisp", content))
    return rendered


def split() -> int:
    lines = CORE4.read_text(encoding="utf-8").split("\n")
    PARTS.mkdir(exist_ok=True)
    for path, content in expected_parts(lines):
        path.write_text(content, encoding="utf-8")
        print(f"  {path.name}: {len(content)} символів")
    return 0


def build() -> str:
    """Точне склеювання: збираємо ВСІ рядки блоків (без 3 рядків заголовка)
    і з'єднуємо одним \n. Це відтворює оригінал байт-у-байт."""
    all_lines: list[str] = []
    for name, *_ in BLOCKS:
        p = PARTS / f"{name}.lisp"
        if not p.is_file():
            raise SystemExit(f"немає блоку {p}")
        all_lines.extend(p.read_text(encoding="utf-8").split("\n")[3:-1])
    return "\n".join(all_lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="розбити/зібрати core4")
    ap.add_argument("--split", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.split:
        return split()
    if args.build:
        CORE4.write_text(build(), encoding="utf-8")
        print("core4.lisp зібрано з блоків")
        return 0
    if args.check:
        rebuilt = build()
        orig = CORE4.read_text(encoding="utf-8")
        if rebuilt == orig:
            expected = expected_parts(orig.split("\n"))
            if all(path.is_file() and path.read_text(encoding="utf-8") == content
                   for path, content in expected):
                print("ЗБІРКА ТОЧНА: блоки й цілі форми SENS відтворюють core4")
                return 0
            print("РОЗБІЖНІСТЬ: межа розрізає SENS-форму або частини застарілі")
            return 1
        print(f"РОЗБІЖНІСТЬ: блоки дають {len(rebuilt)} символів, core4 має {len(orig)}")
        return 1
    ap.error("дай --split / --build / --check")
    return 2


if __name__ == "__main__":
    sys.exit(main())
