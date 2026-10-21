#!/usr/bin/env python3
"""Validate current canonical human domain tables without aggregate copies."""

from __future__ import annotations

import json
from pathlib import Path

from domain_tables import DOMAIN_TABLES, D7_TABLE, D8_TABLE, D9_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
D8_AUTHORITY = ROOT / "knowledge/d8-ratified.json"
D9_AUTHORITY = ROOT / "knowledge/d9-ratified.json"
D7_KEYBOARD_V2 = ROOT / "knowledge/d7-keyboard-v2-ratified.json"


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


def validate_d7():
    # Both current human projections and the owner's ratified v2 keyboard
    # describe the SAME exact W7 coordinates. Historical Devanagari/v1
    # values must never silently replace the current IAST display.
    rows = read_domain_table(D7_TABLE)
    authority = json.loads(D7_KEYBOARD_V2.read_text(encoding="utf-8"))
    if (authority.get("schema") != "sens.d7.keyboard/v2"
            or authority.get("status") != "owner-ratified"
            or authority.get("width") != 7
            or authority.get("capacity") != 128
            or authority.get("occupancy") != 128
            or not isinstance(authority.get("table"), list)
            or len(authority["table"]) != 128):
        fail("D7: owner-ratified keyboard v2 missing/incomplete")
    expected_bits = [f"{number:07b}" for number in range(128)]
    if len(rows) != 128:
        fail("D7: exactly 128 rows required")
    for number, (bits, row, keyboard) in enumerate(zip(expected_bits, rows, authority["table"])):
        if row.width != 7 or row.bits != bits or keyboard.get("bits") != bits:
            fail(f"D7:{bits}: current domain coordinate/order drift")
        if row.lisp is not None:
            fail(f"D7:{bits}: data glyph cannot mint a Lisp callable")
        # C0/DEL are real W7 data but deliberately have no printable human
        # projection in d7.lisp; their raw machine scalar stays in the JSON.
        control = number < 32 or number == 127
        expected = {
            "uk": keyboard.get("uk"),
            "ukr": keyboard.get("uk"),
            "en": keyboard.get("ascii"),
            "san": keyboard.get("iast"),
        }
        for column, glyph in expected.items():
            if not isinstance(glyph, str) or len(glyph) == 0:
                fail(f"D7:{bits}: missing ratified {column} glyph")
            if getattr(row, column) != (None if control else glyph):
                fail(f"D7:{bits}: current {column} glyph disagrees with keyboard v2")
    return rows


def validate_uk_surfaces(rows) -> None:
    for row in rows:
        if row.domain == "D7":
            continue  # D7 cells are glyphs, not word-form projections.
        if row.uk is None or row.ukr is None:
            fail(f"{row.domain}:{row.bits}: uk/ukr must both be present")

        # uk and ukr are independent Ukrainian projections. Do not infer a
        # shortening/alias policy from their names; only enforce the explicit
        # mutation marker when a projection actually carries it.
        mutation = any(
            value is not None and value.endswith("!")
            for value in (row.uk, row.ukr, row.en)
        )
        if mutation:
            if not row.uk.endswith("!"):
                fail(f"{row.domain}:{row.bits}: destructive uk surface must end in !")
            if not row.ukr.endswith("!"):
                fail(f"{row.domain}:{row.bits}: destructive ukr surface must end in !")
            if row.en is None or not row.en.endswith("!"):
                fail(f"{row.domain}:{row.bits}: destructive en surface must end in !")

def main() -> int:
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    total = 0
    all_rows = []

    for width, path in enumerate(DOMAIN_TABLES, start=1):
        residents = foundation["domains"][f"D{width}"]["residents"]
        rows = validate_dense_table(path, width, residents, require_human=True)
        all_rows.extend(rows)
        total += 1 << width

    d7_rows = validate_d7()
    all_rows.extend(d7_rows)
    total += 128

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

    validate_uk_surfaces(all_rows)

    for attr in ("uk", "ukr", "san"):
        seen = {}
        for row in all_rows:
            if row.domain == "D7":
                continue  # Shared glyphs and missing glyphs do not collide across domains.
            value = getattr(row, attr)
            previous = seen.get(value)
            key = (row.domain, row.bits, row.en)
            if previous is not None and previous != key:
                fail(
                    f"{attr}: duplicate surface {value!r} for "
                    f"{previous} and {key}"
                )
            seen[value] = key

    if total != 1022:
        fail(f"expected D1-D9 current residents total 1022 rows, found {total}")

    print("DOMAIN-TABLES: PASS")
    print("files=9 layout=one-domain-per-file")
    print("rows=d1:2,d2:4,d3:8,d4:16,d5:32,d6:64,d7:128,d8:256,d9:512 total=1022")
    print("d7-current=128/128 exact W7 coordinates; no callable names")
    print("D7 symbol availability is independent of semantic residency")
    print("non-D7-surface-collisions=0 namespaces=uk,ukr,san")
    print("uk/ukr=independent Ukrainian projections mutation=! in uk,ukr,en predicate=? in uk,ukr,en")
    print("d9-runtime=W9-carrier-separate-fail-closed-#4038")
    print("columns=ук->укр->san->en->LISP->sym")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
