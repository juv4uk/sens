#!/usr/bin/env python3
"""Пошук наявних функцій у драбинах D1–D10 за назвою — тонка обгортка.

Навіщо: перед написанням нової функції звіритися, чи потрібна операція вже
не визначена. Вживай наявне, а не винаводь наново.

ЄДИНИЙ механізм. Цей пошуковик НЕ читає драбини сам — він ІМПОРТУЄ наявний
`scripts/discover_domain_function_candidates.py` (load_domain_tables + aliases),
який є владою над поверхнями. Обгортка додає лише зручний пошук за назвою
та вивід укр-проєкцією першою (координата — лише довідка).

Використання:
  python3 scripts/search-domain-function.py <запит> [--all] [--domain d6] [--limit N]
  python3 scripts/search-domain-function.py --list-domains
  python3 scripts/search-domain-function.py --self-test

Код виходу: 0 — є збіг (або --self-test ok); 1 — збігів немає; 2 — помилка вживання.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVER = ROOT / "scripts" / "discover_domain_function_candidates.py"
SINGLE = re.compile(r"^[^()\s]+$")


def _load_discover():
    spec = importlib.util.spec_from_file_location("discover_domain_function_candidates", DISCOVER)
    if spec is None or spec.loader is None:
        raise SystemExit("SEARCH-DOMAIN-FUNCTION: не вдалося завантажити discover_domain_function_candidates.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _human(row: dict) -> dict[str, str]:
    out = {}
    for col in ("ук", "укр", "san", "en", "LISP"):
        value = row[col]
        if row.get(col + "_quoted") or value in {"", "()", "<compound>"}:
            continue
        out[col] = value
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="пошук функцій у драбинах D1–D10 (перед написанням — шукай, не вигадуй)",
        epilog="Приклади:  search-domain-function.py сполучити   |   search-domain-function.py --all спол   |   "
               "search-domain-function.py --domain d6 список   |   search-domain-function.py --list-domains")
    ap.add_argument("query", nargs="?")
    ap.add_argument("--domain", help="обмежити доменом, напр. d6")
    ap.add_argument("--all", action="store_true", help="шукати підрядок, а не точний збіг")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--list-domains", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    discover = _load_discover()
    tables = discover.load_domain_tables(ROOT)

    if args.self_test:
        total = sum(len(rows) for rows in tables.values())
        ok = total > 0 and 3 in tables
        print(f"SEARCH-DOMAIN-FUNCTION self-test: {'OK' if ok else 'FAIL'} (доменів {len(tables)}, рядків {total}, джерело: discover_domain_function_candidates)")
        return 0 if ok else 1

    if args.list_domains:
        for d in sorted(tables):
            print(f"d{d}: {len(tables[d])} рядків")
        return 0

    if not args.query:
        ap.error("потрібен запит (або --list-domains / --self-test)")

    q = args.query.lower()
    want_domain = None
    if args.domain:
        m = re.fullmatch(r"d?(\d+)", args.domain.lower())
        if not m:
            ap.error("--domain має вигляд d6")
        want_domain = int(m.group(1))

    def collect(pred) -> list:
        out = []
        for d in sorted(tables):
            if want_domain is not None and d != want_domain:
                continue
            for row in tables[d]:
                names = _human(row)
                for col, value in names.items():
                    if not SINGLE.match(value):
                        continue
                    if pred(value.lower()):
                        out.append((d, row, names))
                        break
        return out

    hits = collect(lambda v: q == v)
    auto_substring = False
    if not hits and not args.all:
        # Комфорт: частковий запит не мусить провалюватися — пробуємо підрядок.
        hits = collect(lambda v: q in v)
        auto_substring = bool(hits)

    if not hits:
        import difflib
        pool = []
        for d in sorted(tables):
            if want_domain is not None and d != want_domain:
                continue
            for row in tables[d]:
                for value in _human(row).values():
                    if SINGLE.match(value):
                        pool.append(value)
        close = difflib.get_close_matches(args.query, pool, n=8, cutoff=0.55)
        print(f"НЕ ЗНАЙДЕНО у D1–D10: {args.query}")
        if close:
            print("Можливо, ви мали на увазі: " + ", ".join(close))
        print("Якщо операції справді немає — це кандидат у пропозиції D11, а не привід писати дубль.")
        return 1

    print(f"знайдено {len(hits)} (показано до {args.limit}):")
    for d, row, names in hits[: args.limit]:
        uk = names.get("ук", names.get("укр", ""))
        bits = row.get("bits", "")
        width = len(bits)
        print(f"  {uk}  [укр-проєкція]  (координата D{d}:{bits}, W{width})  en={names.get('en','')}  LISP={names.get('LISP','')}")
    print("\nДжерело влади: lib/domains/*.lisp (через discover_domain_function_candidates). Вживай наявне, а не винаходь наново.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
