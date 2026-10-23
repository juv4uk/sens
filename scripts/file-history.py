#!/usr/bin/env python3
"""Зануритись у всю історію одного файлу: зміни, активність, визначення.

Навіщо: перед правкою гарячого файлу треба бачити, ЩО з ним робили. Тут — уся
хронологія (з --follow, тож крізь перейменування), активність по днях і коли
з'явилось кожне визначення (з індексу історії, миттєво).

Приклади:
    python3 scripts/file-history.py lib/core4.lisp
    python3 scripts/file-history.py lib/core4.lisp --limit 40
    python3 scripts/file-history.py lib/core4.lisp --defs
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "knowledge" / "guard-history-index.json"


def git(*args: str) -> str:
    return subprocess.run(["git", "-c", "core.quotepath=false", *args],
                          cwd=ROOT, capture_output=True, text=True, check=False).stdout



def important_changes(rel: str, top: int) -> list[tuple[int, int, str, str, str]]:
    """Ранжувати зміни файлу за СУТТЮ, а не за порядком.

    Важливе = великий диф (+додано/-видалено рядків) і/або зміна визначень.
    Масова міграція (309 правок одного дня) відсіюється, бо кожна правка дрібна.
    Повертає [(додано, видалено, sha, дата, тема)] за спаданням обсягу.
    """
    out = git("log", "--follow", "--numstat", "--format=@@%h|%ad|%s", "--date=short", "--", rel)
    rows: list[tuple[int, int, str, str, str]] = []
    sha = date = subj = ""
    add = dele = 0
    for line in out.splitlines():
        if line.startswith("@@"):
            if sha:
                rows.append((add, dele, sha, date, subj))
            sha, date, subj = line[2:].split("|", 2)
            add = dele = 0
        elif line.strip():
            parts = line.split("\t")
            if len(parts) >= 2:
                try:
                    add += int(parts[0]); dele += int(parts[1])
                except ValueError:
                    pass
    if sha:
        rows.append((add, dele, sha, date, subj))
    rows.sort(key=lambda r: -(r[0] + r[1]))
    return rows[:top]


def load_index() -> dict:
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="історія одного файлу")
    ap.add_argument("path", help="шлях до файлу, напр. lib/core4.lisp")
    ap.add_argument("--limit", type=int, default=25, help="скільки останніх змін показати")
    ap.add_argument("--defs", action="store_true", help="показати, коли з'явилось кожне визначення")
    ap.add_argument("--important", type=int, metavar="N", help="показати N найВАЖЛИВІШИХ змін (за обсягом), а не останні")
    args = ap.parse_args(argv)

    rel = args.path
    if not (ROOT / rel).is_file():
        print(f"немає такого файлу: {rel}", file=sys.stderr)
        return 2

    # Чесно про середовище: на shallow-клоні хронологія НЕПОВНА (це вже раз
    # давало «1 зміну» замість 634). Попереджаємо, а не брешемо мовчки.
    shallow = git("rev-parse", "--is-shallow-repository").strip() == "true"
    if shallow:
        print("УВАГА: клон SHALLOW — хронологія нижче неповна (лише останні коміти).")
        print("       Повна історія: git fetch --unshallow origin main")
        print("       Числа з ІНДЕКСУ (нижче) правильні, бо індекс будували на повній історії.\n")

    # Хронологія (з --follow — крізь перейменування)
    log = git("log", "--follow", "--format=%h|%ad|%s", "--date=short", "--", rel).splitlines()
    rows = [ln.split("|", 2) for ln in log if "|" in ln]
    if not rows:
        print(f"історії немає: {rel}")
        return 0

    days = Counter(r[1] for r in rows)
    first, last = rows[-1], rows[0]
    print(f"ФАЙЛ: {rel}")
    print(f"  Змін: {len(rows)} | активних днів: {len(days)} | "
          f"перша: {first[1]} ({first[0]}) | остання: {last[1]} ({last[0]})")
    top_days = ", ".join(f"{d}×{n}" for d, n in days.most_common(5))
    print(f"  найгарячіші дні: {top_days}")

    idx = load_index()
    f = (idx.get("files") or {}).get(rel)
    if f:
        print(f"  в індексі: створено {f.get('first_date')} ({f.get('first_sha')}), "
              f"змін {f.get('commits')}, днів {len(f.get('active_days', []))}")

    if args.defs:
        defs = [(k.split(":", 1)[1], v) for k, v in (idx.get("defs") or {}).items()
                if k.startswith(rel + ":")]
        if defs:
            print(f"\nВИЗНАЧЕННЯ ({len(defs)}) — коли з'явилось кожне:")
            for name, v in sorted(defs, key=lambda kv: kv[1]["date"]):
                print(f"  {v['date']} {v['sha']}  {name}")

    if args.important:
        imp = important_changes(rel, args.important)
        print(f"\nВАЖЛИВІ ЗМІНИ (топ-{len(imp)} за обсягом; масові міграції відсіяно):")
        for add, dele, sha, date, subj in imp:
            print(f"  +{add:<5} -{dele:<5} {date} {sha}  {subj[:76]}")

    print(f"\nХРОНОЛОГІЯ (останні {min(args.limit, len(rows))} із {len(rows)}):")
    for sha, date, subj in rows[:args.limit]:
        print(f"  {date} {sha}  {subj[:88]}")
    if len(rows) > args.limit:
        print(f"  … ще {len(rows) - args.limit} раніших змін")
    return 0


if __name__ == "__main__":
    sys.exit(main())
