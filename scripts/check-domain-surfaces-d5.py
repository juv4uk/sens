#!/usr/bin/env python3
"""Guard the exact-domain D5 Ukrainian/Sanskrit surface projection."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D14 = ROOT / "lib/surface/domain-surfaces-d1-d4.lisp"
D5 = ROOT / "lib/surface/domain-surfaces-d5.lisp"
AUTHORITY = ROOT / "knowledge/d5-ratified.json"

ROW = re.compile(
    r'^\s*\(row\s+(D[1-5])\s+"([01]+)"\s+(\S+)\s+'
    r'"([^"]+)"\s+"([^"]+)"\s+"([^"]+)"\s+(\S+)\s+(\S+)\)\s*$'
)


def fail(message: str) -> None:
    raise SystemExit(f"D5-SURFACE-GUARD: FAIL: {message}")


def parse(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.lstrip().startswith("(row "):
            continue
        match = ROW.match(line)
        if not match:
            fail(f"{path}: cannot parse row at line {line_number}")
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
    return rows


def main() -> int:
    source = D5.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in ("sid8", "sens8", "function8"):
        if forbidden in lowered:
            fail(f"legacy token {forbidden!r} is forbidden in D5 projection")

    d5 = parse(D5)
    if len(d5) != 32:
        fail(f"expected 32 D5 rows, found {len(d5)}")

    expected_bits = {f"{n:05b}" for n in range(32)}
    actual_bits = {row["bits"] for row in d5}
    if actual_bits != expected_bits:
        fail("D5 projection must cover exactly 00000..11111")
    if any(row["domain"] != "D5" or len(row["bits"]) != 5 for row in d5):
        fail("every D5 row must preserve exact width=5")

    keys = [(row["domain"], row["bits"]) for row in d5]
    if len(set(keys)) != 32:
        fail("duplicate D5 exact-domain key")

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    residents = authority["residents"]
    if len(residents) != 32:
        fail("authority file is not 32/32")
    for row in d5:
        expected_name = residents.get(row["bits"])
        if expected_name is None:
            fail(f"{row['bits']}: absent from current D5 authority")
        if row["en"].upper() != expected_name:
            fail(
                f"{row['bits']}: surface resident {row['en']!r} "
                f"does not match authority {expected_name!r}"
            )

    all_rows = parse(D14) + d5
    for language in ("uk", "sa"):
        seen: dict[str, tuple[str, str]] = {}
        for row in all_rows:
            spelling = row[language]
            key = (row["domain"], row["bits"])
            previous = seen.get(spelling)
            if previous is not None and previous != key:
                fail(
                    f"{language}: spelling {spelling!r} collides between "
                    f"{previous} and {key}"
                )
            seen[spelling] = key

    selectors = {
        "01100": ("решта-від-першого-від-першого", "śeṣa-ādi-ādi"),
        "01101": ("решта-від-першого-від-решти", "śeṣa-ādi-śeṣa"),
        "01110": ("решта-від-решти-від-першого", "śeṣa-śeṣa-ādi"),
        "01111": ("решта-від-решти-від-решти", "śeṣa-śeṣa-śeṣa"),
        "10000": ("перше-від-першого-від-першого", "ādi-ādi-ādi"),
        "10001": ("перше-від-першого-від-решти", "ādi-ādi-śeṣa"),
        "10010": ("перше-від-решти-від-першого", "ādi-śeṣa-ādi"),
        "10011": ("перше-від-решти-від-решти", "ādi-śeṣa-śeṣa"),
    }
    by_bits = {row["bits"]: row for row in d5}
    for bits, (uk, sa) in selectors.items():
        row = by_bits[bits]
        if row["role"] != "selector" or row["uk"] != uk or row["sa"] != sa:
            fail(f"{bits}: selector surface is not law-generated composition")

    print("D5-SURFACE-GUARD: PASS")
    print("rows=32 width=5 authority=#3305 uk=unique sa=unique")
    print("combined-surface=D1-D5 legacy-byte=absent selectors=generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
