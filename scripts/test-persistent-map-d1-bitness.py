#!/usr/bin/env python3
"""Джерельний контроль живої української мапи та точних ключів D1–D10.

Це НЕ evaluator: позитивні й негативні обчислення виконують справжні SENS
crates/sens/tests/persistent_map.rs та d9_map_lisp_facade.rs.
Не повертати старі двійкові голови, host truthiness чи англійські виклики.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "lib" / "persistent-map.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
RAW_BINARY_HEAD = re.compile(r"\([01]{3,10}(?=\s|\))")
BARE_TRUTH = re.compile(r"\((?:так|ні)(?=\s|\))")
D1_TRUE = "((атом? (як-є ()))"
REQUIRED = (
    "мапа-порожній",
    "мапа-вставити",
    "мапа-отримати",
    "мапа-містить?",
    "мапа-список",
    "внутрішня-мапа-вставити",
    "внутрішня-мапа-отримати",
    "внутрішня-мапа-містить",
    "внутрішня-мапа-список",
    "внутрішня-мапа-порожній",
)


def check_pm() -> list[str]:
    errs: list[str] = []
    if not PM.is_file():
        return [f"missing {PM.relative_to(ROOT)}"]
    text = PM.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"persistent-map: host truthiness {m.group()!r} at offset {m.start()}")
    code = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    if RAW_BINARY_HEAD.search(code):
        errs.append("persistent-map: machine-encoded call-head found in human .lisp")
    if BARE_TRUTH.search(code):
        errs.append("persistent-map: uncomputed (так/ні) predicate call")
    if code.count(D1_TRUE) != 2:
        errs.append("persistent-map: expected exactly two executable D3→D1 fallbacks")
    for fn in REQUIRED:
        if len(re.findall(r"(?m)^\(визначити\s+" + re.escape(fn) + r"(?=\s|\))", code)) != 1:
            errs.append(f"persistent-map: missing or duplicated Ukrainian DEFINE: {fn}")
    return errs


def check_domain(n: int) -> list[str]:
    path = ROOT / "lib" / "domains" / f"d{n}.lisp"
    errs: list[str] = []
    if not path.is_file():
        return [f"D{n}: missing"]
    keys = ROW.findall(path.read_text(encoding="utf-8"))
    expect = 1 << n
    if len(keys) != expect:
        errs.append(f"D{n}: expected {expect} rows, got {len(keys)}")
    bad = [k for k in keys if len(k) != n]
    if bad:
        errs.append(f"D{n}: key width {len(bad[0])} != {n}")
    if len(set(keys)) != len(keys):
        errs.append(f"D{n}: duplicate coordinates")
    return errs


def main() -> int:
    all_errs: list[str] = []
    all_errs.extend(check_pm())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("PERSISTENT-MAP+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("PERSISTENT-MAP SOURCE: PASS — два D3→D1 fallbacks, чинні українські DEFINE; SENS runtime перевіряється окремо")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
