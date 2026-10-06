#!/usr/bin/env python3
"""Validate current canonical human domain tables without aggregate copies."""

from __future__ import annotations

import json
from pathlib import Path

from domain_tables import DOMAIN_TABLES, D8_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d8-foundation.json"
D8_AUTHORITY = ROOT / "knowledge/d8-ratified.json"


def fail(message: str) -> None:
    raise SystemExit(f"DOMAIN-TABLES: FAIL: {message}")


def normalized_en(value: str) -> str:
    return value.removesuffix("?").casefold()


def validate_dense_table(path: Path, width: int, residents: dict[str, str], require_human: bool):
    rows = read_domain_table(path)
    domain = f"D{width}"
    expected_count = 1 << width
    if len(rows) != expected_count:
        fail(f"{domain}: expected {expected_count} rows, found {len(rows)}")

    expected_bits = [f"{n:0{width}b}" for n in range(expected_count)]
    actual_bits = [row.bits for row in rows]
    if actual_bits != expected_bits:
        fail(f"{domain}: rows must be ordered exact-width 0..{expected_count - 1}")

    missing_uk = 0
    missing_san = 0
    for row in rows:
        resident = residents.get(row.bits)
        if resident is None:
            fail(f"{domain}:{row.bits}: absent from ratified authority")

        if row.en is None:
            fail(f"{domain}:{row.bits}: missing en")
        if normalized_en(row.en) != resident.casefold():
            fail(f"{domain}:{row.bits}: en {row.en!r} does not match resident {resident!r}")

        if width == 8:
            if row.lisp != resident:
                fail(f"D8:{row.bits}: LISP {row.lisp!r} must preserve ratified resident {resident!r}")
        elif require_human and row.lisp is None and domain not in {"D2"}:
            fail(f"{domain}:{row.bits}: missing LISP")

        if row.uk is None:
            missing_uk += 1
        if row.san is None:
            missing_san += 1

        if require_human:
            for attr in ("uk", "ukr", "san"):
                if getattr(row, attr) is None:
                    fail(f"{domain}:{row.bits}: missing {attr}")

        predicate = row.en.endswith("?")
        if predicate:
            if row.uk is not None and not row.uk.endswith("?"):
                fail(f"{domain}:{row.bits}: predicate uk must end in ?")
            if row.ukr is not None and not row.ukr.endswith("?"):
                fail(f"{domain}:{row.bits}: predicate ukr must end in ?")
            if row.san is not None and row.san.endswith("?"):
                fail(f"{domain}:{row.bits}: predicate san must not end in ?")

    return rows, missing_uk, missing_san


def main() -> int:
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    total = 0
    all_rows = []

    for width, path in enumerate(DOMAIN_TABLES, start=1):
        residents = foundation["domains"][f"D{width}"]["residents"]
        rows, _, _ = validate_dense_table(path, width, residents, require_human=True)
        all_rows.extend(rows)
        total += 1 << width

    d8_authority = json.loads(D8_AUTHORITY.read_text(encoding="utf-8"))
    if d8_authority.get("status") != "owner-ratified" or d8_authority.get("authority") != "#3960":
        fail("D8 authority is not owner-ratified #3960")
    d8_rows, missing_uk, missing_san = validate_dense_table(
        D8_TABLE,
        8,
        d8_authority["residents"],
        require_human=True,
    )
    all_rows.extend(d8_rows)
    total += 256

    for attr in ("uk", "ukr", "san"):
        seen = {}
        for row in all_rows:
            value = getattr(row, attr)
            previous = seen.get(value)
            key = (row.domain, row.bits, row.lisp)
            if previous is not None and previous != key:
                fail(
                    f"{attr}: duplicate surface {value!r} for "
                    f"{previous} and {key}"
                )
            seen[value] = key

    if total != 382:
        fail(f"expected D1-D6 + D8 total 382 rows, found {total}")

    print("DOMAIN-TABLES: PASS")
    print("files=7 layout=one-domain-per-file current-human-tables=D1-D6,D8")
    print("rows=d1:2,d2:4,d3:8,d4:16,d5:32,d6:64,d8:256 total=382")
    print(f"d8-missing-uk={missing_uk} d8-missing-san={missing_san} d8-missing-ukr=0")
    print("surface-collisions=0 namespaces=uk,ukr,san")
    print("columns=ук->укр->san->en->LISP->sym")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
