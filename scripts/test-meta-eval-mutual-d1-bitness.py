#!/usr/bin/env python3
"""Mechanical source inventory: meta-eval-mutual D1 surface + domain bitness.

CI_GLUE_NO_SEMANTICS: this Python file never establishes a SENS logical PASS.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/meta-eval-mutual.lisp has no bare host truthiness (t / T / NIL)
  2. A computed SENS D1:YES outcome is present; bare truth heads and #d1: are absent
  3. Key surface present (recursive-group closure / group-eval / eval-program-with-groups)
  4. Reuses existing MetaEval helpers under current Ukrainian names
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-meta-eval-mutual-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUT = ROOT / "lib" / "meta-eval-mutual.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
D1_TRUE = "(атом? (як-є ()))"
REQUIRED = (
    "це-замикання-рекурсивної-групи?",
    "обчислити-групу-мета",
    "застосувати-групове-замикання",
    "обчислити-програму-з-рекурсивними-групами",
    "побудувати-лексичні-зв'язки-рекурсивної-групи",
    "взяти-групу-лямбда-визначень",
    "застосувати-функцію-мета",
    "зв'язати-аргументи-з-лямбда-параметрами",
    "знайти-значення-імені-в-лексичному-середовищі",
)


def check_mutual() -> list[str]:
    errs: list[str] = []
    if not MUT.is_file():
        return [f"missing {MUT.relative_to(ROOT)}"]
    text = MUT.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"meta-eval-mutual: host truthiness {m.group()!r} at offset {m.start()}")
    active = "\n".join(line.split(";", 1)[0] for line in text.splitlines())
    if D1_TRUE not in active:
        errs.append("meta-eval-mutual: обчислюваний D1:YES через SENS ATOM(QUOTE NIL) відсутній")
    if re.search(r"\(\s*(?:так|ні)(?=\s|\))", active):
        errs.append("meta-eval-mutual: викличне голе так/ні замість SENS D1")
    if "#d1:" in active:
        errs.append("meta-eval-mutual: raw/typed one-bit literal remains in executable source")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"meta-eval-mutual: required surface missing: {fn}")
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
    all_errs.extend(check_mutual())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("META-EVAL-MUTUAL+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("META-EVAL-MUTUAL: MECHANICAL_PASS — source markers only; semantic_pass=NOT_INFERRED")
    for n in range(1, 11):
        print(f"D{n}: MECHANICAL_PASS width={n} rows={1 << n}/{1 << n}")
    print("BITNESS: MECHANICAL_PASS — exact key widths only; semantic_pass=NOT_INFERRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
