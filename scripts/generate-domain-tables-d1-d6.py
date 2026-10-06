#!/usr/bin/env python3
"""Validate the six canonical self-describing D1-D6 table files."""

from __future__ import annotations

import json
from pathlib import Path

from domain_tables import DOMAIN_TABLES, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d7-foundation.json"


def fail(message: str) -> None:
    raise SystemExit(f"DOMAIN-TABLES-D1-D6: FAIL: {message}")


def main() -> int:
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    total = 0
    seen_keys: set[str] = set()

    for width, path in enumerate(DOMAIN_TABLES, start=1):
        rows = read_domain_table(path)
        domain = f"D{width}"
        residents = foundation["domains"][domain]["residents"]

        if len(rows) != 1 << width:
            fail(f"{domain}: expected {1 << width} rows, found {len(rows)}")

        expected_bits = [f"{n:0{width}b}" for n in range(1 << width)]
        actual_bits = [row.bits for row in rows]
        if actual_bits != expected_bits:
            fail(f"{domain}: rows must be ordered exact-width 0..{(1 << width) - 1}")

        for row in rows:
            if row.bits in seen_keys:
                fail(f"exact-width key spelling repeated across domain files: {row.bits}")
            seen_keys.add(row.bits)

            resident = residents.get(row.bits)
            if resident is None:
                fail(f"{domain}:{row.bits}: absent from ratified foundation")

            if row.en is None or row.en.removesuffix("?").upper() != resident:
                fail(
                    f"{domain}:{row.bits}: en {row.en!r} "
                    f"does not match resident {resident!r}"
                )

            for attr in ("uk", "ukr", "san", "en"):
                if getattr(row, attr) is None:
                    fail(f"{domain}:{row.bits}: missing {attr}")

            predicate = row.en.endswith("?")
            if predicate:
                if not row.uk.endswith("?"):
                    fail(f"{domain}:{row.bits}: predicate uk must end in ?")
                if not row.ukr.endswith("?"):
                    fail(f"{domain}:{row.bits}: predicate ukr must end in ?")
                if row.san.endswith("?"):
                    fail(f"{domain}:{row.bits}: predicate san must not end in ?")

            total += 1

    if total != 126:
        fail(f"expected D1-D6 total 126 rows, found {total}")

    print("DOMAIN-TABLES-D1-D6: PASS")
    print("files=6 rows=126 layout=one-domain-per-file")
    print("paths=lib/domains/d1.lisp..lib/domains/d6.lisp")
    print("columns=ук->укр->san->en->LISP->sym")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
