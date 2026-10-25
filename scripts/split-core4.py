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

# Межі визначено стабільними SENS-якорями, не номерами рядків.
# Унікальні топ-рівневі DEFINE-якорі замість фіксованих ліній:
# старе розбиття розривало SENS-форми після вставлення нових визначень.
BLOCKS = [
    ("core4-language", None, "мова: тотожність, макроси та/або, список, числа, базові предикати"),
    ("core4-d6", "(" + "визначити значення-у-списку?-ядро", "похідні Д5/Д6, партії 1-3"),
    ("core4-codec", "(" + "визначити п-р-п-р", "структурні селектори, НСД + кодек T5M + T5M3"),
    ("core4-d6b", "(" + "визначити т5-додати-слово", "похідні Д6, партії 4-5 та кодек"),
    ("core4-d8-d9", "(" + "визначити перше-від-решта-від-решта-від-решта-від-перше-від-решта", "Д8/Д9: масиви, рядки, content-store"),
]
HDR = "; core4 · блок «{name}» · рядки {a}–{b} оригіналу\n; {desc}\n; Згенеровано scripts/split-core4.py — НЕ редагувати руками; правте блок і перезберіть.\n"


def require_complete_forms(fragment: str, label: str) -> None:
    """Механічна межа: жодна SENS-форма не повинна перетинати блоки.

    Не оцінює Lisp, не тлумачить домени та не підмінює native SENS.
    Враховує рядкові літерали, escape і коментарі до кінця рядка.
    """
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for ch in fragment:
        if comment:
            if ch == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == ";":
            comment = True
        elif ch == '"':
            quoted = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise SystemExit(f"CORE4_FRAGMENT_UNBALANCED part={label} unexpected=close")
    if depth or quoted:
        raise SystemExit(
            f"CORE4_FRAGMENT_UNBALANCED part={label} unclosed={depth} string={quoted}"
        )


def bounds(source: str) -> list[int]:
    cuts = [0]
    for name, marker, _ in BLOCKS[1:]:
        needle = "\n" + marker + "\n"
        if source.count(needle) != 1:
            raise SystemExit(f"межа {name}: очікувався рівно один точний DEFINE {marker}")
        cuts.append(source.index(needle) + 1)
    cuts.append(len(source))
    if cuts != sorted(set(cuts)):
        raise SystemExit("межі Core4 не є строго впорядкованими")
    for i, (name, _, _) in enumerate(BLOCKS):
        require_complete_forms(source[cuts[i]:cuts[i + 1]], name)
    return cuts


def split() -> int:
    source = CORE4.read_text(encoding="utf-8")
    cuts = bounds(source)
    PARTS.mkdir(exist_ok=True)
    for i, (name, marker, desc) in enumerate(BLOCKS):
        start, stop = cuts[i:i + 2]
        first_line = source.count("\n", 0, start) + 1
        last_line = source.count("\n", 0, stop)
        fragment = source[start:stop]
        (PARTS / f"{name}.lisp").write_text(
            HDR.format(name=name, a=first_line, b=last_line, desc=desc) + fragment,
            encoding="utf-8",
        )
        print(f"  {name}: {first_line}-{last_line}")
    return 0


def build() -> str:
    """Точна конкатенація без втрати/додавання LF і розриву SENS-форм."""
    fragments: list[str] = []
    for name, *_ in BLOCKS:
        file = PARTS / f"{name}.lisp"
        if not file.is_file():
            raise SystemExit(f"немає блоку {file}")
        header_and_fragment = file.read_text(encoding="utf-8").split("\n", 3)
        if len(header_and_fragment) != 4:
            raise SystemExit(f"пошкоджений заголовок {file}")
        fragment = header_and_fragment[3]
        require_complete_forms(fragment, name)
        fragments.append(fragment)
    return "".join(fragments)


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
            print("ЗБІРКА ТОЧНА: блоки відтворюють core4.lisp байт-у-байт")
            return 0
        print(f"РОЗБІЖНІСТЬ: блоки дають {len(rebuilt)} символів, core4 має {len(orig)}")
        return 1
    ap.error("дай --split / --build / --check")
    return 2


if __name__ == "__main__":
    sys.exit(main())
