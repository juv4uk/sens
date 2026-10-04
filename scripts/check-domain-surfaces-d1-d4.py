#!/usr/bin/env python3
"""Guard the exact-domain D1-D4 Ukrainian/Sanskrit surface projection."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/surface/domain-surfaces-d1-d4.lisp"

ROW = re.compile(
    r'^\s*\(row\s+(D[1-4])\s+"([01]+)"\s+(\S+)\s+'
    r'"([^"]+)"\s+"([^"]+)"\s+"([^"]+)"\s+(\S+)\s+(\S+)\)\s*$'
)

EXPECTED_COUNTS = {"D1": 2, "D2": 4, "D3": 8, "D4": 16}
DISPLAY_ONLY = {("D2", f"{n:02b}") for n in range(4)} | {("D3", "000")}


def fail(message: str) -> None:
    raise SystemExit(f"D1-D4-SURFACE-GUARD: FAIL: {message}")


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    lowered = text.lower()
    for forbidden in ("sid8", "sens8", "function8"):
        # The header intentionally names forbidden legacy classes once.
        if lowered.count(forbidden) != 1:
            fail(f"legacy token {forbidden!r} must appear only in the prohibition comment")

    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("(row "):
            continue
        match = ROW.match(line)
        if not match:
            fail(f"cannot parse row at line {line_number}")
        domain, bits, role, en, uk, sa, uk_status, sa_status = match.groups()
        rows.append(
            {
                "domain": domain,
                "bits": bits,
                "role": role,
                "en": en,
                "uk": uk,
                "sa": sa,
                "uk_status": uk_status,
                "sa_status": sa_status,
            }
        )

    if len(rows) != 30:
        fail(f"expected 30 exact-domain rows, found {len(rows)}")

    keys = [(row["domain"], row["bits"]) for row in rows]
    if len(set(keys)) != len(keys):
        fail("duplicate exact-domain key")

    for domain, count in EXPECTED_COUNTS.items():
        width = int(domain[1:])
        domain_rows = [row for row in rows if row["domain"] == domain]
        if len(domain_rows) != count:
            fail(f"{domain}: expected {count} rows, found {len(domain_rows)}")
        expected_bits = {f"{n:0{width}b}" for n in range(1 << width)}
        actual_bits = {row["bits"] for row in domain_rows}
        if actual_bits != expected_bits:
            fail(f"{domain}: projection is not complete exact-width coverage")

    # Human lowering must not be ambiguous inside this current D1-D4 surface slice.
    for language in ("uk", "sa"):
        seen = {}
        for row in rows:
            spelling = row[language]
            if spelling in seen:
                fail(
                    f"{language}: duplicate spelling {spelling!r} for "
                    f"{seen[spelling]} and {(row['domain'], row['bits'])}"
                )
            seen[spelling] = (row["domain"], row["bits"])

    for row in rows:
        key = (row["domain"], row["bits"])
        if key in DISPLAY_ONLY and row["role"] != "display":
            fail(f"{key}: structural/display identity became callable surface")
        if key not in DISPLAY_ONLY and row["role"] == "display":
            fail(f"{key}: unexpected display-only role")

    print("D1-D4-SURFACE-GUARD: PASS")
    print("rows=30 d1=2 d2=4 d3=8 d4=16")
    print("uk=unique sa=unique exact-width=preserved legacy-byte=forbidden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
