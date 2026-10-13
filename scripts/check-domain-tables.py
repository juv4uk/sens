#!/usr/bin/env python3
"""Validate current canonical human domain tables without aggregate copies."""

from __future__ import annotations

from dataclasses import replace
import json
import re
from pathlib import Path

from check_d10_owner_whole_domain_ratification import run as check_d10_owner_ratification
from domain_tables import (
    DOMAIN_TABLES, D7_TABLE, D8_TABLE, D9_TABLE, D10_TABLE,
    DomainTableRow, read_domain_table,
)

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
D7_AUTHORITY = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
D8_AUTHORITY = ROOT / "knowledge/d8-ratified.json"
D9_AUTHORITY = ROOT / "knowledge/d9-ratified.json"
D10_AUTHORITY = ROOT / "knowledge/d10-owner-whole-domain-ratification-20261012.json"
D10_POINTER = ROOT / "knowledge/d10-current-inventory.json"
D10_INVENTORY = ROOT / "knowledge/d10-v18-semantic-inventory.json"


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


def validate_d10_table(rows: list[DomainTableRow], residents: dict[str, str]) -> list[DomainTableRow]:
    """Validate the owner-ratified D10 catalogue without granting runtime admission."""
    expected_bits = [f"{number:010b}" for number in range(1024)]
    if len(rows) != 1024:
        raise ValueError(f"D10: expected 1024 rows, found {len(rows)}")
    if len(residents) != 1024 or set(residents) != set(expected_bits):
        raise ValueError("D10: authority inventory must be the complete 10-bit coordinate set")

    actual_bits = [row.bits for row in rows]
    if actual_bits != expected_bits:
        first = next(
            (index for index, (actual, expected) in enumerate(zip(actual_bits, expected_bits))
             if actual != expected),
            min(len(actual_bits), len(expected_bits)),
        )
        got = actual_bits[first] if first < len(actual_bits) else "<missing>"
        raise ValueError(
            f"D10: row {first} must be exact coordinate {expected_bits[first]}, got {got}"
        )

    for row in rows:
        if row.domain != "D10" or row.width != 10 or len(row.bits) != 10:
            raise ValueError(f"D10:{row.bits}: coordinate/domain width must be exactly 10")
        resident = residents.get(row.bits)
        if not isinstance(resident, str) or not resident:
            raise ValueError(f"D10:{row.bits}: missing pinned inventory resident")
        if row.en is None or not en_matches_resident(row.en, resident):
            raise ValueError(
                f"D10:{row.bits}: en {row.en!r} does not match inventory {resident!r}"
            )
        if row.lisp is None or row.lisp.casefold() != resident.casefold():
            raise ValueError(
                f"D10:{row.bits}: LISP {row.lisp!r} does not preserve inventory name {resident!r}"
            )
        for attr in ("uk", "ukr", "san"):
            if getattr(row, attr) is None:
                raise ValueError(f"D10:{row.bits}: missing {attr}")
        if row.en.endswith("?"):
            if row.uk is not None and not row.uk.endswith("?"):
                raise ValueError(f"D10:{row.bits}: predicate uk must end in ?")
            if row.ukr is not None and not row.ukr.endswith("?"):
                raise ValueError(f"D10:{row.bits}: predicate ukr must end in ?")
            if row.san is not None and row.san.endswith("?"):
                raise ValueError(f"D10:{row.bits}: predicate san must not end in ?")
    return rows


def self_test_d10_table_validator() -> int:
    """Positive control plus focused mutations for width, density and identity."""
    residents = {}
    rows = []
    for number in range(1024):
        bits = f"{number:010b}"
        name = f"fixture-{number}"
        residents[bits] = name
        rows.append(DomainTableRow(
            "D10", 10, bits, "uk-" + bits, "ukr-" + bits,
            "san-" + bits, name, name, None,
        ))
    validate_d10_table(rows, residents)

    mutations = [
        ("missing row", rows[:-1]),
        ("short coordinate", [replace(rows[0], bits="000000000"), *rows[1:]]),
        ("duplicate coordinate", [rows[0], replace(rows[1], bits=rows[0].bits), *rows[2:]]),
        ("out-of-order coordinate", [rows[1], rows[0], *rows[2:]]),
        ("wrong domain", [replace(rows[0], domain="D9"), *rows[1:]]),
        ("wrong declared width", [replace(rows[0], width=9), *rows[1:]]),
        ("English label drift", [replace(rows[0], en="wrong"), *rows[1:]]),
        ("LISP identity drift", [replace(rows[0], lisp="wrong"), *rows[1:]]),
    ]
    for label, mutant in mutations:
        try:
            validate_d10_table(mutant, residents)
        except ValueError:
            continue
        raise ValueError(f"D10 self-test admitted mutation: {label}")
    return len(mutations)


def validate_d7(authority: dict):
    # Text-only D7 v2 owner authority, never the historical 126-cell sound map.
    if (authority.get("schema"), authority.get("status"),
            authority.get("width"), authority.get("capacity"),
            authority.get("occupancy")) != (
            "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128):
        fail("D7 keyboard/v2 authority not ratified 128/128")
    rows = read_domain_table(D7_TABLE)
    ledger = authority.get("table", [])
    if len(rows) != 128 or len(ledger) != 128:
        fail("D7: exactly 128 rows required")
    for number, (row, source) in enumerate(zip(rows, ledger)):
        bits = f"{number:07b}"
        if source.get("bits") != bits or row.bits != bits:
            fail(f"D7:{bits}: coordinate/order drift")
        if row.lisp is not None:
            fail(f"D7:{bits}: data glyph cannot mint a Lisp callable")
        expected = (
            (source["uk"], source["uk"], source["san"],
             source["ascii"], source["uk"])
            if 32 <= number < 127 else (None, None, None, None, None)
        )
        if (row.uk, row.ukr, row.san, row.en, row.sym) != expected:
            fail(f"D7:{bits}: keyboard projection drift")
    for column in ("ascii", "uk", "san"):
        if len({source[column] for source in ledger}) != 128:
            fail(f"D7: {column} glyph collision")
    return rows


def validate_compact_uk(rows) -> None:
    for row in rows:
        if row.domain == "D7":
            continue  # D7 cells are glyphs, not verbose/compact human names.
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


    # D10 whole-domain ratification is distinct from per-resident proofs and
    # physical T5/runtime admission. Reuse the owner checker, then validate
    # the human table against the exact pinned inventory and exact 10-bit grid.
    try:
        check_d10_owner_ratification(ROOT)
        d10_authority = json.loads(D10_AUTHORITY.read_text(encoding="utf-8"))
        d10_pointer = json.loads(D10_POINTER.read_text(encoding="utf-8"))
        if d10_pointer["canonical_current"]["path"] != str(D10_INVENTORY.relative_to(ROOT)):
            fail("D10: current inventory pointer path drift")
        inventory_blob = d10_authority["inventory"]["git_blob"]
        if d10_pointer["canonical_current"]["git_blob"] != inventory_blob:
            fail("D10: pointer and owner authority inventory pins differ")
        inventory = json.loads(D10_INVENTORY.read_text(encoding="utf-8"))
        expected_pin = f"; Pinned input Git blob: {inventory_blob}"
        if expected_pin not in D10_TABLE.read_text(encoding="utf-8").splitlines():
            fail("D10: human table does not pin the ratified inventory blob")
        d10_residents = {
            row["coordinate"]: row["semantic_name"] for row in inventory["rows"]
        }
        d10_rows = read_domain_table(D10_TABLE)
        d10_negative_cases = self_test_d10_table_validator()
        validate_d10_table(d10_rows, d10_residents)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        fail(f"D10 exact-width/authority validation: {exc}")

    validate_compact_uk(all_rows)


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
    combined_total = total + len(d10_rows)
    if len(d10_rows) != 1024 or combined_total != 2046:
        fail(f"D10 catalogue count mismatch: d10={len(d10_rows)}, combined={combined_total}")

    print("DOMAIN-TABLES: PASS")
    print("files=10 layout=one-domain-per-file")
    print("rows=d1:2,d2:4,d3:8,d4:16,d5:32,d6:64,d7:128,d8:256,d9:512,d10:1024 total=2046")
    print("D1-D9 current residents=1022; D10 whole-domain catalogue=1024")
    print("D10=selected:1024 placed:1024 unplaced:0 per-row-ratified:0")
    print("D10 exact-width=10 ordered-range=0000000000..1111111111 mutation-controls=" + str(d10_negative_cases) + " PASS")
    print("D10 semantic-law-attestation=INCOMPLETE physical-T5-runtime-admission=FALSE")
    print("d7-v2=128/128 keyboard cells; legacy v1 reserved only in history")
    print("D7 symbol availability is independent of semantic residency")
    print("non-D7-surface-collisions=0 namespaces=uk,ukr,san (D1-D9 audit; D10 labels remain separately scoped)")
    print("uk-style=compact ukr-style=expanded selectors=п/р mutation=! in uk,ukr,en predicate=? in uk,ukr,en")
    print("d9-runtime=W9-carrier-separate-fail-closed-#4038")
    print("columns=ук->укр->san->en->LISP->sym")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
