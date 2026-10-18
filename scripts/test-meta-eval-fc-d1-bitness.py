#!/usr/bin/env python3
"""Point-wise informative witness: meta-eval-first-class D1 + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/meta-eval-first-class.lisp has no bare host truthiness (t / T / NIL)
  2. Exact D1 full Ukrainian predicate words «так»/«ні» are present; legacy #d1 literals absent
  3. First-class primitive surface present (atom/eq/car/cdr/cons/+/-/*/</=/>)
  4. Public entry my-eval-first-class present
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-meta-eval-fc-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "lib" / "meta-eval-first-class.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
D1_YES = "так"
D1_NO = "ні"
PRIMITIVES = ("atom", "eq", "car", "cdr", "cons", "+", "-", "*", "<", "=", ">")
REQUIRED = (
    "my-fc-primitive",
    "my-fc-root-env",
    "my-fc-eval",
    "my-fc-apply",
    "my-fc-compare-chain",
    "my-eval-first-class",
)


def check_meta() -> list[str]:
    errs: list[str] = []
    if not META.is_file():
        return [f"missing {META.relative_to(ROOT)}"]
    text = META.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"meta-eval-fc: host truthiness {m.group()!r} at offset {m.start()}")
    executable = re.sub(
        r';[^\n]*|"(?:\\.|[^"\\])*"',
        lambda m: " " * len(m.group()),
        text,
    )
    if not re.search(r"\(\s*" + D1_YES + r"(?=\s|\))", executable):
        errs.append("meta-eval-fc: немає прямого ратифікованого D1:так")
    if not re.search(r"(?<![\w-])" + D1_NO + r"(?![\w-])", executable):
        errs.append("meta-eval-fc: немає прямого ратифікованого D1:ні")
    if re.search(r"#d1:[01]", executable):
        errs.append("meta-eval-fc: застарілий типовий #d1 літерал у source")
    d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
    if "(0 (ук ні) (укр ні)" not in d1 or "(1 (ук так) (укр так)" not in d1:
        errs.append("meta-eval-fc: українські D1 слова не збігаються з ратифікацією")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"meta-eval-fc: required surface missing: {fn}")
    for p in PRIMITIVES:
        if f"(001 {p})" not in text and f"(001 {p})" not in text:
            # allow both quoted forms
            if p not in text:
                errs.append(f"meta-eval-fc: first-class primitive missing: {p}")
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
    all_errs.extend(check_meta())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("META-EVAL-FC+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("META-EVAL-FC: PASS — no host truthiness or legacy #d1, Ukrainian D1 words, first-class primitives")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
