#!/usr/bin/env python3
"""Point-wise informative witness: narrate PredicateBit + domain bitness.

Axiom: the binary key width IS the domain address.
Checks:
  1. lib/narrate.lisp has no bare host truthiness (t / T / NIL)
  2. Exact D1:1 form (010 (001 ())) is present
  3. Reuses result-proper-list? from migrated result-status surface
  4. Key narrate function surface present
  5. Every lib/domains/dN.lisp has exactly 2^N rows of exact N-bit keys

Does not prove runtime callability or T5 physical execution. Run:

    python3 scripts/test-narrate-d1-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARRATE = ROOT / "lib" / "narrate.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(t|T|NIL)(?!\w)")
D1_TRUE = "(010 (001 ()))"
REQUIRED = (
    "narrate-fact",
    "narrate-provenance",
    "narrate-answer",
    "narrate-outcome",
    "narrate-proper-list?",
    "narrate-list-exact-two?",
    "narrate-list-exact-three?",
    "result-proper-list?",
    "provenance-goal",
    "provenance-rule",
)


def check_narrate() -> list[str]:
    errs: list[str] = []
    if not NARRATE.is_file():
        return [f"missing {NARRATE.relative_to(ROOT)}"]
    text = NARRATE.read_text(encoding="utf-8")
    for m in HOST.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"narrate: host truthiness {m.group()!r} at offset {m.start()}")
    if D1_TRUE not in text:
        errs.append("narrate: exact D1:1 form (010 (001 ())) missing")
    active_code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(";")
    )
    for legacy in ("narrate-outcome-arity?", "(11110111 (000000 fact)", "(000000 outcome)"):
        if legacy in active_code:
            errs.append(f"narrate: legacy arity mechanism still active: {legacy}")
    for fn in REQUIRED:
        if fn not in text:
            errs.append(f"narrate: required surface missing: {fn}")
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
    all_errs.extend(check_narrate())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("NARRATE+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("NARRATE: PASS — no host truthiness, exact D1, result-status reuse")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
