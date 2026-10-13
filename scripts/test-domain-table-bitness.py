#!/usr/bin/env python3
"""Point-wise exact-width bitness test for canonical domain tables.

Axiom: the binary key width IS the domain address.
For each lib/domains/dN.lisp, every row key must be exactly N bits,
cover the full 0..2^N-1 space once, and nothing else.

This is a narrow informative witness. It does not prove callability,
occupancy bitmaps, or D10 execution. Run:

    python3 scripts/test-domain-table-bitness.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HEADER_WIDTH = re.compile(
    r"exact[- ]width\s+(\d+)[- ]bit|D(\d+):\s*exact[- ]width\s+(\d+)",
    re.IGNORECASE,
)


def table_path(n: int) -> Path:
    return ROOT / "lib" / "domains" / f"d{n}.lisp"


def check_domain(n: int) -> list[str]:
    path = table_path(n)
    errors: list[str] = []
    if not path.is_file():
        return [f"D{n}: missing file {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    keys = ROW.findall(text)
    expected = 1 << n

    # Header should declare the same width (soft: warn-as-error for conscience).
    declared = None
    for m in HEADER_WIDTH.finditer(text):
        for g in m.groups():
            if g is not None:
                declared = int(g)
                break
        if declared is not None:
            break
    if declared is not None and declared != n:
        errors.append(
            f"D{n}: header declares width {declared}, filename requires {n}"
        )

    if len(keys) != expected:
        errors.append(
            f"D{n}: expected {expected} rows (2^{n}), got {len(keys)}"
        )

    bad_width = [k for k in keys if len(k) != n]
    if bad_width:
        sample = bad_width[0]
        errors.append(
            f"D{n}: key {sample!r} has {len(sample)} bits, need exactly {n}"
        )

    if len(set(keys)) != len(keys):
        errors.append(f"D{n}: duplicate coordinates")

    full = {f"{i:0{n}b}" for i in range(expected)}
    got = set(keys)
    missing = sorted(full - got)
    extra = sorted(got - full)
    if missing:
        errors.append(f"D{n}: missing coordinates e.g. {missing[0]}")
    if extra:
        errors.append(f"D{n}: unauthorized coordinates e.g. {extra[0]}")

    return errors


def main() -> int:
    all_errors: list[str] = []
    report: list[str] = []
    for n in range(1, 11):
        errs = check_domain(n)
        if errs:
            all_errors.extend(errs)
            report.append(f"D{n}: FAIL ({len(errs)} issue(s))")
        else:
            report.append(f"D{n}: PASS exact-width {n}-bit, {1 << n}/{1 << n}")

    for line in report:
        print(line)

    if all_errors:
        print("BITNESS: BLOCKED", file=sys.stderr)
        for e in all_errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("BITNESS: PASS — every domain key width equals domain address")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
