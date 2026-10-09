#!/usr/bin/env python3
"""Generate and verify D7 display-only projection from ratified SENS tables.

No D7 function names or executable dispatch are generated: these are
human-readable UK/Sanskrit renderings for already-width-qualified D7 values.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domain_tables import D7_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "knowledge/d7-ratified.json"
GENERATED = ROOT / "crates/sens/src/d7_display_registry_generated.rs"


def check_rows():
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if not (
        authority["status"] == "owner-ratified"
        and authority["domain"] == "D7"
        and authority["width"] == 7
        and authority["capacity"] == 128
        and authority["occupancy"] == 126
        and authority["owner_reserved_pinned"] == 2
    ):
        raise ValueError("D7 authority/occupancy was not ratified")
    rows = read_domain_table(D7_TABLE)
    residents = set(authority["residents"])
    reserved = set(authority["reserved_coordinates"])
    all_coordinates = {f"{index:07b}" for index in range(128)}
    if not (
        len(rows) == 126
        and len(residents) == 126
        and len(reserved) == 2
        and residents | reserved == all_coordinates
        and residents.isdisjoint(reserved)
        and {row.bits for row in rows} == residents
    ):
        raise ValueError("D7 resident/reserved coordinates do not match owner authority")
    for row in rows:
        if not row.uk or not row.san:
            raise ValueError(f"D7:{row.bits}: missing human display names")
        if row.lisp is not None:
            raise ValueError(f"D7:{row.bits}: sound/text must not become a Lisp function")
        if row.en != authority["residents"][row.bits]:
            raise ValueError(f"D7:{row.bits}: role label drift")
    return rows


def rust_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def generated_source(rows) -> str:
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// D7 authority: lib/domains/d7.lisp + knowledge/d7-ratified.json (#3572).",
        "// Checked by scripts/check-d7-runtime-projection.py.",
        "// Display-only: NEVER usable for source-head or evaluator routing.",
        "",
        "#[derive(Clone, Copy)]",
        "pub(super) struct D7DisplayRow {",
        "    pub(super) bits: u8,",
        "    pub(super) uk: &'static str,",
        "    pub(super) sa: &'static str,",
        "}",
        "",
        "pub(super) const D7_DISPLAY_ROWS: &[D7DisplayRow] = &[",
    ]
    for row in rows:
        lines.append(
            f"    D7DisplayRow {{ bits: 0b{row.bits}, "
            f"uk: {rust_string(row.uk)}, sa: {rust_string(row.san)} }},"
        )
    lines.append("];")
    return "\n".join(lines) + "\n"


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--write-generated", action="store_true")
    args = cli.parse_args()
    expected = generated_source(check_rows())
    if args.write_generated:
        GENERATED.write_text(expected, encoding="utf-8")
    elif not GENERATED.is_file() or GENERATED.read_text(encoding="utf-8") != expected:
        raise SystemExit("D7-DISPLAY-PROJECTION: FAIL: generated Rust differs from ratified D7 table")
    print("D7-DISPLAY-PROJECTION: PASS (126 residents, 2 reserved; no callable D7 admission)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
