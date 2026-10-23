#!/usr/bin/env python3
"""Визначити найВАЖЛИВІШІ файли — не найгарячіші, а ті, від яких залежить решта.

Гарячий файл часто правлять. Важливий — той, чиї визначення вживає багато інших
файлів: якщо він зламається, зламається все.

Міра проста (простота первинна):
    важливість = кількість визначень × кількість ЗОВНІШНІХ вживань

Тобто файл вагомий, якщо він багато ДАЄ (визначення) і його багато БЕРУТЬ (вживання
з інших файлів). Визначення, які ніхто не вживає, ваги не додають.

Приклади:
    python3 scripts/important-files.py
    python3 scripts/important-files.py --top 30
    python3 scripts/important-files.py --layer lib/
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEF = re.compile(r"\(" + "визначити" + r"\s+([^\s()]+)")
SKIP = ("lib/domains/", "lib/generated/", "lib/surface/", "lib/machine/")


def tracked(pattern: str) -> list[str]:
    out = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", pattern],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="найважливіші файли (визначення × вживання)")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--layer", default="lib/", help="з якого шару брати файли (типово lib/)")
    args = ap.parse_args(argv)

    files = [f for f in tracked(args.layer + "*") if f.endswith(".lisp")
             and not any(f.startswith(p) for p in SKIP)]
    defs: dict[str, set[str]] = {}
    texts: dict[str, str] = {}
    for f in files:
        p = ROOT / f
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        texts[f] = t
        defs[f] = {m.group(1) for m in DEF.finditer(t)}

    # вживання: скільки разів ім'я визначення з файлу F згадується в ІНШИХ файлах
    name_owner: dict[str, str] = {}
    for f, names in defs.items():
        for n in names:
            name_owner.setdefault(n, f)
    ext_use: dict[str, int] = defaultdict(int)
    for f, t in texts.items():
        for n, owner in name_owner.items():
            if owner == f:
                continue
            c = t.count(n)
            if c:
                ext_use[owner] += c

    rows = []
    for f in files:
        nd = len(defs.get(f, ()))
        use = ext_use.get(f, 0)
        size = len(texts.get(f, "").splitlines())
        rows.append((nd * use, nd, use, size, f))
    rows.sort(key=lambda r: -r[0])

    print(f"НАЙВАЖЛИВІШІ ФАЙЛИ (визначення × зовнішні вживання), шар {args.layer}:")
    print(f"  {'вага':>8} | {'визн':>5} | {'вжив':>6} | {'рядків':>6} | файл")
    for score, nd, use, size, f in rows[:args.top]:
        print(f"  {score:>8} | {nd:>5} | {use:>6} | {size:>6} | {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
