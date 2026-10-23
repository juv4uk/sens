#!/usr/bin/env python3
"""Пошук наявних функцій у драбинах D1–D10 (і поверхні D11), перш ніж писати нове.

Навіщо: у доменах уже є тисячі ратифікованих функцій (укр-поверхні з
координатами). Коли пишеться нова програма, треба СПЕРШУ знайти, чи потрібна
операція вже не визначена — і вжити наявне, а не винаходити наново.

Джерело влади: lib/domains/d1.lisp … d10.lisp (рядки виду
  (101111110 (ук …) (укр …) (san …) (en …) (LISP …) (sym ()))).
D11 — дослідницький шар, тому позначається окремо й не вважається чинною владою.

Використання:
  python3 scripts/search-domain-function.py <запит> [--all] [--domain d6] [--limit N]
  python3 scripts/search-domain-function.py --list-domains
  python3 scripts/search-domain-function.py --self-test

Код виходу: 0 — є хоч один збіг (або --self-test ok); 1 — збігів немає; 2 — помилка вживання.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\s*\(([01]{3,})\s+(.*)\)\s*$")
COL = re.compile(r"\((ук|укр|san|en|LISP|sym)\s+(.*?)\)")
NAME = re.compile(r"^[^()\s]+$")


def rows_of(path: Path) -> list[tuple[str, dict[str, str]]]:
    out: list[tuple[str, dict[str, str]]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        bits, rest = m.group(1), m.group(2)
        cols: dict[str, str] = {}
        for cm in COL.finditer(rest):
            cols[cm.group(1)] = cm.group(2).strip()
        if "ук" in cols or "en" in cols:
            out.append((bits, cols))
    return out


def domains() -> dict[str, Path]:
    found = {}
    for path in sorted((ROOT / "lib" / "domains").glob("d*.lisp")):
        stem = path.stem  # d1, d2, ... d10
        if re.fullmatch(r"d\d+", stem):
            found[stem] = path
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="пошук функцій у драбинах D1–D10")
    ap.add_argument("query", nargs="?", help="ім'я або частина імені (укр/лат/символ)")
    ap.add_argument("--domain", help="обмежити доменом, напр. d6")
    ap.add_argument("--all", action="store_true", help="шукати підрядок, а не точний збіг")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--list-domains", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    doms = domains()
    if args.list_domains:
        for d, p in doms.items():
            print(f"{d}: {len(rows_of(p))} рядків")
        return 0

    if args.self_test:
        total = sum(len(rows_of(p)) for p in doms.values())
        ok = total > 0 and "d1" in doms
        print(f"SEARCH-DOMAIN-FUNCTION self-test: {'OK' if ok else 'FAIL'} (доменів {len(doms)}, рядків {total})")
        return 0 if ok else 1

    if not args.query:
        ap.error("потрібен запит (або --list-domains / --self-test)")

    q = args.query.lower()
    hits: list[tuple[str, str, str, dict[str, str]]] = []
    for d, p in doms.items():
        if args.domain and d != args.domain.lower():
            continue
        for bits, cols in rows_of(p):
            names = {k: v for k, v in cols.items() if k in ("ук", "укр", "en", "LISP", "san")}
            for k, v in names.items():
                if NAME.match(v) and ((q in v.lower()) if args.all else (q == v.lower())):
                    hits.append((d, bits, k, cols))
                    break

    if not hits:
        print(f"НЕ ЗНАЙДЕНО у D1–D10: {args.query}")
        print("Якщо операції справді немає — це кандидат у пропозиції D11, а не привід писати дубль.")
        return 1

    print(f"знайдено {len(hits)} (показано до {args.limit}):")
    for d, bits, k, cols in hits[: args.limit]:
        uk = cols.get("ук", cols.get("укр", ""))
        en = cols.get("en", "")
        san = cols.get("san", "")
        lisp = cols.get("LISP", "")
        width = len(bits)
        print(f"  D{d[1:]} : {bits} (W{width})  ук={uk}  en={en}  LISP={lisp}  san={san}")
    print("\nДжерело влади: lib/domains/*.lisp. Вживай наявне, а не винаходь наново.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
