#!/usr/bin/env python3
"""Validate current canonical human domain tables without aggregate copies."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from domain_tables import (
    DOMAIN_TABLES,
    D7_TABLE,
    D8_TABLE,
    D9_TABLE,
    D10_TABLE,
    read_domain_table,
)

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
D7_AUTHORITY = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
D8_AUTHORITY = ROOT / "knowledge/d8-ratified.json"
D9_AUTHORITY = ROOT / "knowledge/d9-ratified.json"
D10_POINTER = ROOT / "knowledge/d10-current-inventory.json"


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


def git_blob_sha(payload: bytes) -> str:
    """Return Git's SHA-1 blob object ID for pinned-source verification."""
    header = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).hexdigest()


def coordinate_sequence_error(actual_bits: list[str], width: int) -> str | None:
    """Find gaps, duplicates, order drift, or wrong widths in an exact-width grid."""
    expected_bits = [f"{value:0{width}b}" for value in range(1 << width)]
    if len(actual_bits) != len(expected_bits):
        return f"expected {len(expected_bits)} rows, found {len(actual_bits)}"
    for index, bits in enumerate(actual_bits):
        if not isinstance(bits, str) or re.fullmatch(rf"[01]{{{width}}}", bits) is None:
            return f"row {index} is not exactly {width} binary digits"
    if actual_bits != expected_bits:
        return f"coordinates are not the ordered complete {width}-bit range"
    return None


def validate_d10_grid_guard_self_test() -> None:
    """Assert that bit mutation, duplicate, and missing-row regressions are rejected."""
    expected = [f"{value:010b}" for value in range(1024)]
    bit_mutant = expected.copy()
    bit_mutant[512] = f"{int(bit_mutant[512], 2) ^ 2:010b}"
    duplicate_mutant = expected.copy()
    duplicate_mutant[512] = duplicate_mutant[511]
    missing_mutant = expected[:-1]

    for label, mutant in (
        ("one-bit mutation", bit_mutant),
        ("duplicate coordinate", duplicate_mutant),
        ("missing row", missing_mutant),
    ):
        if coordinate_sequence_error(mutant, 10) is None:
            fail(f"D10 negative self-test did not reject {label}")


def validate_d10_catalogue() -> None:
    """Check D10 width and pins without promoting research rows to residents."""
    pointer = json.loads(D10_POINTER.read_text(encoding="utf-8"))
    if pointer.get("schema") != "d10-current-inventory-pointer/v1":
        fail("D10 pointer schema is not current")
    status = str(pointer.get("status", ""))
    if not status.startswith("OWNER-RATIFIED-WHOLE-D10-DOMAIN-1024"):
        fail("D10 whole-domain ratification is not recorded")

    current = pointer.get("canonical_current")
    if not isinstance(current, dict):
        fail("D10 pointer has no canonical_current")
    source_path = current.get("path")
    valid_path = re.fullmatch(
        r"knowledge/d10-v[0-9]+-semantic-inventory\.json",
        source_path if isinstance(source_path, str) else "",
    )
    if valid_path is None:
        fail(f"D10 canonical source path is invalid: {source_path!r}")

    source_bytes = (ROOT / source_path).read_bytes()
    source_sha = git_blob_sha(source_bytes)
    if current.get("git_blob") != source_sha:
        fail("D10 pointer Git blob SHA does not match current inventory")

    table_text = D10_TABLE.read_text(encoding="utf-8")
    first_row_marker = "  (0000000000 "
    if first_row_marker not in table_text:
        fail("D10 table has no first coordinate")
    table_header = table_text.split(first_row_marker, 1)[0]
    if f"Canonical mapping: {source_path}" not in table_header:
        fail("D10 table points at a different inventory")
    if f"Pinned input Git blob: {source_sha}" not in table_header:
        fail("D10 table's inventory pin is stale")

    inventory = json.loads(source_bytes)
    source_rows = inventory.get("rows")
    if not isinstance(source_rows, list) or len(source_rows) != 1024:
        found = len(source_rows) if isinstance(source_rows, list) else "non-list"
        fail(f"D10 inventory must have 1024 rows; found {found}")

    expected_bits = [f"{value:010b}" for value in range(1024)]
    source_bits = [
        row.get("coordinate") if isinstance(row, dict) else None
        for row in source_rows
    ]
    if any(
        not isinstance(bits, str) or re.fullmatch(r"[01]{10}", bits) is None
        for bits in source_bits
    ):
        fail("D10 inventory contains a coordinate that is not exactly 10 bits")
    if len(set(source_bits)) != 1024 or set(source_bits) != set(expected_bits):
        fail("D10 inventory does not cover all 1024 unique 10-bit words")

    metrics = tuple(
        current.get(key) for key in ("selected", "placed", "unplaced", "ratified")
    )
    if metrics != (1024, 1024, 0, 0):
        fail(
            "D10 accounting must be selected/placed/unplaced/ratified=1024/1024/0/0; "
            f"found {metrics}"
        )

    for row in source_rows:
        if not isinstance(row.get("ratified_resident"), bool):
            fail("D10 row is missing explicit ratified_resident state")
        if row["ratified_resident"]:
            fail("D10 research row must not have individual resident ratification")
        if not isinstance(row.get("physical_t5_authorized"), bool):
            fail("D10 row is missing explicit physical_t5_authorized state")
        if row["physical_t5_authorized"]:
            fail("D10 research inventory must not authorize physical T5 execution")

    table_rows = read_domain_table(D10_TABLE)
    error = coordinate_sequence_error([row.bits for row in table_rows], 10)
    if error is not None:
        fail(f"D10 table: {error}")

    source_by_coordinate = {row["coordinate"]: row for row in source_rows}
    semantic_names = [row.get("semantic_name") for row in source_rows]
    if any(not isinstance(name, str) or not name for name in semantic_names):
        fail("D10 inventory row is missing semantic_name")
    if len({name.casefold() for name in semantic_names}) != 1024:
        fail("D10 inventory contains duplicate semantic names")

    for row in table_rows:
        resident = source_by_coordinate[row.bits].get("semantic_name")
        if (
            not isinstance(resident, str)
            or row.en is None
            or not en_matches_resident(row.en, resident)
        ):
            fail(
                f"D10:{row.bits}: en {row.en!r} does not match "
                f"canonical resident {resident!r}"
            )


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

    validate_d10_grid_guard_self_test()
    validate_d10_catalogue()
    # D10 is ratified as a 10-bit codebook, but its 1024 row-level meanings
    # remain unratified research and have no physical T5 authorization.
    # Do not mix D10 surfaces into D1-D9 identity/collision accounting.

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

    print("DOMAIN-TABLES: PASS")
    print("files=10 layout=one-domain-per-file; D1-D9 tables plus separately gated D10 codebook")
    print("rows=d1:2,d2:4,d3:8,d4:16,d5:32,d6:64,d7:128,d8:256,d9:512 current-residents=1022")
    print("D10=1024/1024 unique 10-bit coordinates; resident-ratification=0; physical-T5-authorized=0")
    print("D10-negative-self-test=one-bit-mutation,duplicate,missing-row rejected")
    print("d7-v2=128/128 keyboard cells; legacy v1 reserved only in history")
    print("D7 symbol availability is independent of semantic residency")
    print("non-D7-surface-collisions=0 namespaces=uk,ukr,san")
    print("uk-style=compact ukr-style=expanded selectors=п/р mutation=! in uk,ukr,en predicate=? in uk,ukr,en")
    print("d9-runtime=W9-carrier-separate-fail-closed-#4038")
    print("columns=ук->укр->san->en->LISP->sym")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
