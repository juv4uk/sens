#!/usr/bin/env python3
"""Validate current canonical human domain tables without aggregate copies."""

from __future__ import annotations

import json
import re
from pathlib import Path

from domain_tables import DOMAIN_TABLES, D7_TABLE, D8_TABLE, D9_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
D7_AUTHORITY = ROOT / "knowledge/d7-ratified.json"
D8_AUTHORITY = ROOT / "knowledge/d8-ratified.json"
D9_AUTHORITY = ROOT / "knowledge/d9-ratified.json"


def fail(message: str) -> None:
    raise SystemExit(f"DOMAIN-TABLES: FAIL: {message}")


def en_matches_resident(value: str, resident: str) -> bool:
    candidate = value.casefold()
    target = resident.casefold()
    if candidate == target:
        return True
    if candidate.endswith(("?", "!")) and candidate[:-1] == target:
        return True
    return False


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

    for row in rows:
        resident = residents.get(row.bits)
        if resident is None:
            fail(f"{domain}:{row.bits}: absent from ratified authority")

        if domain == "D3" and row.bits == "000":
            # Every projection of the structural EMPTY value is literally ().
            surfaces = ("uk", "ukr", "san", "en", "lisp", "sym")
            if any(getattr(row, name) != "()" for name in surfaces):
                fail("D3:000: all six columns must be literal ()")
            continue

        if row.en is None:
            fail(f"{domain}:{row.bits}: missing en")
        if not en_matches_resident(row.en, resident):
            fail(f"{domain}:{row.bits}: en {row.en!r} does not match resident {resident!r}")

        if width in {8, 9}:
            if row.lisp != resident:
                fail(f"D{width}:{row.bits}: LISP {row.lisp!r} must preserve ratified resident {resident!r}")
        elif require_human and row.lisp is None and domain not in {"D2"}:
            fail(f"{domain}:{row.bits}: missing LISP")

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

    return rows


def validate_d7(authority: dict):
    if authority.get("status") != "owner-ratified" or authority.get("authority") != "#3572":
        fail("D7 authority is not owner-ratified #3572")

    rows = read_domain_table(D7_TABLE)
    residents = authority["residents"]
    if len(rows) != 126:
        fail(f"D7: expected 126 rows, found {len(rows)}")

    reserved = set(authority["reserved_coordinates"])
    actual_bits = [row.bits for row in rows]
    expected_bits = sorted(residents, key=lambda bits: int(bits, 2))

    if actual_bits != expected_bits:
        fail("D7: rows must match ratified resident coordinates exactly")
    if any(bits in reserved for bits in actual_bits):
        fail("D7: owner-reserved pinned coordinate appeared as a semantic row")

    for row in rows:
        resident = residents[row.bits]
        if row.en is None or row.en.casefold() != resident.casefold():
            fail(f"D7:{row.bits}: en {row.en!r} does not match resident {resident!r}")
        if row.lisp is not None:
            fail(f"D7:{row.bits}: LISP must stay () because D7 is sound/text, not a Lisp operator")
        for attr in ("uk", "ukr", "san"):
            if getattr(row, attr) is None:
                fail(f"D7:{row.bits}: missing {attr}")

    return rows


def validate_compact_uk(rows) -> None:
    for row in rows:
        if row.uk is None or row.ukr is None:
            fail(f"{row.domain}:{row.bits}: uk/ukr must both be present")

        if len(row.uk) > len(row.ukr):
            fail(
                f"{row.domain}:{row.bits}: compact uk surface {row.uk!r} "
                f"is longer than expanded ukr {row.ukr!r}"
            )

        if "-на-місці" in row.uk:
            fail(f"{row.domain}:{row.bits}: compact uk must use ! instead of -на-місці")

        if row.domain == "D7" and (row.uk.startswith("звук-") or row.uk.startswith("текст-")):
            fail(f"{row.domain}:{row.bits}: compact uk must omit redundant D7 context prefix")

        if row.domain == "D7" and row.uk.startswith("український-"):
            fail(f"{row.domain}:{row.bits}: compact uk should use the stable укр- prefix")

        mutation = (
            row.uk.endswith("!")
            or row.ukr.endswith("!")
            or (row.en is not None and row.en.endswith("!"))
            or "на-місці" in row.ukr
        )
        if mutation:
            if not row.uk.endswith("!"):
                fail(f"{row.domain}:{row.bits}: destructive uk surface must end in !")
            if not row.ukr.endswith("!"):
                fail(f"{row.domain}:{row.bits}: destructive ukr surface must end in !")
            if row.en is None or not row.en.endswith("!"):
                fail(f"{row.domain}:{row.bits}: destructive en surface must end in !")

        if row.lisp and re.fullmatch(r"C[AD]{2,7}R", row.lisp.upper()):
            path = row.lisp.upper()[1:-1]
            expected = "-".join("п" if ch == "A" else "р" for ch in path)
            if row.uk != expected:
                fail(
                    f"{row.domain}:{row.bits}: selector uk {row.uk!r} "
                    f"must be compact path {expected!r}"
                )

    by_lisp = {row.lisp: row for row in rows if row.lisp}
    for name, expected in (("GCD", "нсд"), ("LCM", "нск")):
        row = by_lisp.get(name)
        if row is not None and row.uk != expected:
            fail(f"{row.domain}:{row.bits}: {name} compact uk must be {expected!r}")


def main() -> int:
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    total = 0
    all_rows = []

    for width, path in enumerate(DOMAIN_TABLES, start=1):
        residents = foundation["domains"][f"D{width}"]["residents"]
        rows = validate_dense_table(path, width, residents, require_human=True)
        all_rows.extend(rows)
        total += 1 << width

    d7_authority = json.loads(D7_AUTHORITY.read_text(encoding="utf-8"))
    d7_rows = validate_d7(d7_authority)
    all_rows.extend(d7_rows)
    total += 126

    d8_authority = json.loads(D8_AUTHORITY.read_text(encoding="utf-8"))
    if d8_authority.get("status") != "owner-ratified" or d8_authority.get("authority") != "#3960":
        fail("D8 authority is not owner-ratified #3960")
    d8_rows = validate_dense_table(
        D8_TABLE,
        8,
        d8_authority["residents"],
        require_human=True,
    )
    all_rows.extend(d8_rows)
    total += 256

    d9_authority = json.loads(D9_AUTHORITY.read_text(encoding="utf-8"))
    if d9_authority.get("status") != "owner-ratified" or d9_authority.get("authority") != "#4008":
        fail("D9 authority is not owner-ratified #4008")
    d9_rows = validate_dense_table(
        D9_TABLE,
        9,
        d9_authority["residents"],
        require_human=True,
    )
    all_rows.extend(d9_rows)
    total += 512

    validate_compact_uk(all_rows)

    for attr in ("uk", "ukr", "san"):
        seen = {}
        for row in all_rows:
            value = getattr(row, attr)
            previous = seen.get(value)
            key = (row.domain, row.bits, row.en)
            if previous is not None and previous != key:
                fail(
                    f"{attr}: duplicate surface {value!r} for "
                    f"{previous} and {key}"
                )
            seen[value] = key

    if total != 1020:
        fail(f"expected D1-D9 current residents total 1020 rows, found {total}")

    print("DOMAIN-TABLES: PASS")
    print("files=9 layout=one-domain-per-file")
    print("rows=d1:2,d2:4,d3:8,d4:16,d5:32,d6:64,d7:126,d8:256,d9:512 total=1020")
    print("d7-reserved=0100001,0101010")
    print("missing-uk=0 missing-ukr=0 missing-san=0")
    print("surface-collisions=0 namespaces=uk,ukr,san")
    print("uk-style=compact ukr-style=expanded selectors=п/р mutation=! in uk,ukr,en predicate=? in uk,ukr,en")
    print("d9-runtime=W9-carrier-separate-fail-closed-#4038")
    print("columns=ук->укр->san->en->LISP->sym")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
