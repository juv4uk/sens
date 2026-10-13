#!/usr/bin/env python3
"""Point-wise informative witness: meta-eval-mutual COND + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/meta-eval-mutual.lisp has no bare host truthiness (t / T / NIL)
  2. Exact D1:1 form (010 (001 ())) is present as fallback
  3. Key surface present (group-closure / group-eval / eval-program-with-groups)
  4. Reuses existing meta-eval helpers (my-apply, bind-params, env-lookup)
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
D1_TRUE = "(010 (001 ()))"
REQUIRED = (
    "my-group-closure?",
    "my-group-eval",
    "my-group-apply",
    "my-eval-program-with-groups",
    "my-build-group-env",
    "my-take-lambda-def-group",
    "my-apply",       # reuse from meta-eval
    "bind-params",    # reuse
    "env-lookup",     # reuse
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
    if D1_TRUE not in text:
        errs.append("meta-eval-mutual: exact D1:1 form (010 (001 ())) missing")
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

    print("META-EVAL-MUTUAL: PASS — two-field COND, exact D1, meta-eval reuse")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
