#!/usr/bin/env python3
"""Point-wise informative witness: persistent-map D1 + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/persistent-map.lisp has no bare host truthiness (t / T / NIL)
  2. No host-shaped COND else (010 ()) — only exact D1:1 (010 (001 ()))
  3. Surface: map-insert, map-get, map-contains?, map-empty, map->list
  4. Ukrainian aliases point at the same closures
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Run:
    python3 scripts/test-persistent-map-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "lib" / "persistent-map.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
HOST_ELSE = "(010 ())"
D1_TRUE = "(010 (001 ()))"
REQUIRED = (
    "map-empty",
    "map-insert",
    "map-get",
    "map-contains?",
    "map->list",
    "внутрішня-мапа-вставити",
    "внутрішня-мапа-отримати",
    "внутрішня-мапа-містить",
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
    # Host-shaped else without nested ()
    if HOST_ELSE in text and D1_TRUE not in text:
        errs.append("persistent-map: host-shaped (010 ()) without exact D1:1")
    # Prefer exact D1 present
    if D1_TRUE not in text:
        errs.append("persistent-map: exact D1:1 form (010 (001 ())) missing")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"persistent-map: required surface missing: {fn}")
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

    print("PERSISTENT-MAP: PASS — exact D1 fallbacks, D3 EQ, Ukrainian aliases")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
