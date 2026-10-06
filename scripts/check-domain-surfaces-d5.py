#!/usr/bin/env python3
"""Guard canonical D5 human table against ratified D5 authority."""

from __future__ import annotations

import json
from pathlib import Path

from domain_tables import DOMAIN_TABLES, read_domain_table, read_domain_tables

ROOT = Path(__file__).resolve().parents[1]
D5 = DOMAIN_TABLES[4]
AUTHORITY = ROOT / "knowledge/d5-ratified.json"


def fail(message: str) -> None:
    raise SystemExit(f"D5-SURFACE-GUARD: FAIL: {message}")


def main() -> int:
    d5 = read_domain_table(D5)
    if len(d5) != 32:
        fail(f"expected 32 D5 rows, found {len(d5)}")

    expected_bits = {f"{n:05b}" for n in range(32)}
    actual_bits = {row.bits for row in d5}
    if actual_bits != expected_bits:
        fail("D5 table must cover exactly 00000..11111")

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    residents = authority["residents"]
    if len(residents) != 32:
        fail("authority file is not 32/32")

    for row in d5:
        expected_name = residents.get(row.bits)
        if expected_name is None:
            fail(f"{row.bits}: absent from current D5 authority")
        if row.en is None or row.en.removesuffix("?").upper() != expected_name:
            fail(
                f"{row.bits}: table en {row.en!r} "
                f"does not match authority {expected_name!r}"
            )

    all_rows = read_domain_tables(DOMAIN_TABLES[:5])
    for attr in ("uk", "san"):
        seen: dict[str, tuple[str, str]] = {}
        for row in all_rows:
            spelling = getattr(row, attr)
            if spelling is None:
                fail(f"{row.domain}:{row.bits}: missing {attr}")
            key = (row.domain, row.bits)
            previous = seen.get(spelling)
            if previous is not None and previous != key:
                fail(
                    f"{attr}: spelling {spelling!r} collides between "
                    f"{previous} and {key}"
                )
            seen[spelling] = key

    selectors = {
        "01100": ("р-п-п", "śeṣa-ādi-ādi"),
        "01101": ("р-п-р", "śeṣa-ādi-śeṣa"),
        "01110": ("р-р-п", "śeṣa-śeṣa-ādi"),
        "01111": ("р-р-р", "śeṣa-śeṣa-śeṣa"),
        "10000": ("п-п-п", "ādi-ādi-ādi"),
        "10001": ("п-п-р", "ādi-ādi-śeṣa"),
        "10010": ("п-р-п", "ādi-śeṣa-ādi"),
        "10011": ("п-р-р", "ādi-śeṣa-śeṣa"),
    }
    by_bits = {row.bits: row for row in d5}
    for bits, (uk, san) in selectors.items():
        row = by_bits[bits]
        if row.uk != uk or row.san != san:
            fail(f"{bits}: selector surface is not law-generated composition")

    print("D5-SURFACE-GUARD: PASS")
    print("rows=32 width=5 source=lib/domains/d5.lisp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
