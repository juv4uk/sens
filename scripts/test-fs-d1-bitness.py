#!/usr/bin/env python3
"""Point-wise informative witness: fs COND + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/fs.lisp has no bare host truthiness (t / T / NIL)
  2. The fallback computes exact D1:1 with ATOM(QUOTE ()), not an unbound name
  3. Reuses Ukrainian UTF-8 and raw filesystem capability projections
  4. Key fs surface present
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Run:
    python3 scripts/test-fs-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FS = ROOT / "lib" / "fs.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
D1_TRUE = "((атом? (як-є ()))"
REQUIRED = (
    "читати-файл",
    "записати-файл",
    "кодування-юнікод-8-кодувати-рядок",
    "читати-сирий-текст-файла",
    "записати-байти-файла",
)


def check_fs() -> list[str]:
    errs: list[str] = []
    if not FS.is_file():
        return [f"missing {FS.relative_to(ROOT)}"]
    text = FS.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"fs: host truthiness {m.group()!r} at offset {m.start()}")
    if D1_TRUE not in text:
        errs.append("fs: executable D1:1 = ATOM(QUOTE ()) missing")
    if "#d1:1" in text:
        errs.append("fs: encoded D1 literal is forbidden in primary source")
    executable = "\n".join(line for line in text.splitlines()
                             if not line.lstrip().startswith(";"))
    if re.search(r"\(\s*[01]{3,9}(?=\s|\))", executable):
        errs.append("fs: raw binary call head is forbidden in primary source")
    if re.search(r"\(\s*так(?=\s|\))", executable):
        errs.append("fs: unbound legacy truth head forbidden")
    if "((функція " in executable:
        errs.append("fs: anonymous D5 value-call forbidden")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"fs: required Ukrainian projection missing: {fn}")
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
    all_errs.extend(check_fs())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("FS+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("FS: PASS — two-field COND, computed D1 and Ukrainian raw I/O")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
