#!/usr/bin/env python3
"""Mechanical source-shape inventory for result-status migration.

NON-SEMANTIC: this script does not define D1 truth, result-status behavior, or
language correctness. The semantic gate is the self-checking binary SENS
program tests/semantic/result-status-d1-law.bits, executed by
crates/sens/tests/sens_semantic_witnesses.rs as a mechanism-only harness.

This checker may report source drift/bit-shape facts only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "lib" / "result-status.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
W8 = re.compile(r"\(([01]{8})(?=\s|\))")
HOST = re.compile(r"(?<!\w)(t|NIL)(?!\w)")
D1_TRUE = "(010 (001 ()))"
D1_FALSE = "(101 (001 (0)) (001 (1)))"


def check_status() -> list[str]:
    errs: list[str] = []
    if not STATUS.is_file():
        return [f"missing {STATUS.relative_to(ROOT)}"]
    text = STATUS.read_text(encoding="utf-8")
    # Allow NIL only inside domain-table comments / historical notes if any;
    # in this file bare t/NIL as carriers are forbidden.
    for m in HOST.finditer(text):
        # skip if inside a comment line
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.start())]
        if line.lstrip().startswith(";"):
            continue
        errs.append(f"result-status: host truthiness {m.group()!r} at offset {m.start()}")
    if D1_TRUE not in text:
        errs.append("result-status: exact D1:1 form (010 (001 ())) missing")
    if D1_FALSE not in text:
        errs.append("result-status: exact D1:0 form (101 (001 (0)) (001 (1))) missing")
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(";"):
            continue
        match = W8.search(line)
        if match:
            errs.append(
                f"result-status: retired 8-bit executable token {match.group()!r} on line {line_no}"
            )
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
    all_errs.extend(check_status())
    for n in range(1, 11):
        all_errs.extend(check_domain(n))

    if all_errs:
        print("RESULT-STATUS+BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errs:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("RESULT-STATUS: PASS — exact D1:0/D1:1, no host truthiness, no W8 heads")
    for n in range(1, 11):
        print(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")
    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
