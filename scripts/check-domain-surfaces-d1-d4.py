#!/usr/bin/env python3
"""Guard the exact-domain D1-D5 Ukrainian/Sanskrit runtime projection."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_D14 = ROOT / "lib/surface/domain-surfaces-d1-d4.lisp"
SOURCE_D5 = ROOT / "lib/surface/domain-surfaces-d5.lisp"
SOURCES = (SOURCE_D14, SOURCE_D5)
GENERATED = ROOT / "crates/sens/src/domain_surface_registry_generated.rs"

ROW = re.compile(
    r'^\s*\(row\s+(D[1-5])\s+"([01]+)"\s+(\S+)\s+'
    r'"([^"]+)"\s+"([^"]+)"\s+"([^"]+)"\s+(\S+)\s+(\S+)\)\s*$'
)

EXPECTED_COUNTS = {"D1": 2, "D2": 4, "D3": 8, "D4": 16, "D5": 32}
DISPLAY_ONLY = {("D2", f"{n:02b}") for n in range(4)} | {("D3", "000")}


def fail(message: str) -> None:
    raise SystemExit(f"D1-D5-SURFACE-GUARD: FAIL: {message}")


def parse_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in SOURCES:
        text = source.read_text(encoding="utf-8")
        lowered = text.lower()
        for forbidden in ("sid8", "sens8", "function8"):
            if forbidden in lowered:
                fail(f"legacy token {forbidden!r} is forbidden in {source}")

        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.lstrip().startswith("(row "):
                continue
            match = ROW.match(line)
            if not match:
                fail(f"cannot parse row at {source}:{line_number}")
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


def rust_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_generated(rows: list[dict[str, str]]) -> str:
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Authority: lib/surface/domain-surfaces-d1-d4.lisp + domain-surfaces-d5.lisp",
        "// Checked by: scripts/check-domain-surfaces-d1-d4.py",
        "",
        "#[derive(Clone, Copy, Debug, Eq, PartialEq)]",
        "pub(super) struct DomainSurfaceName {",
        "    pub(super) namespace: &'static str,",
        "    pub(super) name: &'static str,",
        "}",
        "",
        "#[derive(Clone, Copy, Debug, Eq, PartialEq)]",
        "pub(super) struct DomainSurfaceRow {",
        "    pub(super) width: u8,",
        "    pub(super) bits: u8,",
        "    pub(super) source_routable: bool,",
        "    pub(super) surfaces: &'static [DomainSurfaceName],",
        "}",
        "",
        "pub(super) const DOMAIN_SURFACE_ROWS: &[DomainSurfaceRow] = &[",
    ]

    for row in rows:
        width = int(row["domain"][1:])
        source_routable = row["domain"] in {"D3", "D4", "D5"} and row["role"] != "display"
        surfaces = ", ".join(
            [
                "DomainSurfaceName { namespace: "
                + rust_string("uk")
                + ", name: "
                + rust_string(row["uk"])
                + " }",
                "DomainSurfaceName { namespace: "
                + rust_string("sa")
                + ", name: "
                + rust_string(row["sa"])
                + " }",
            ]
        )
        lines.append(
            f"    DomainSurfaceRow {{ width: {width}, bits: 0b{row['bits']}, "
            f"source_routable: {str(source_routable).lower()}, "
            f"surfaces: &[{surfaces}] }},"
        )

    lines.append("];")
    return "\n".join(lines) + "\n"


def validate(rows: list[dict[str, str]]) -> None:
    if len(rows) != 62:
        fail(f"expected 62 exact-domain rows, found {len(rows)}")

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

    for language in ("uk", "sa"):
        seen: dict[str, tuple[str, str]] = {}
        for row in rows:
            spelling = row[language]
            key = (row["domain"], row["bits"])
            previous = seen.get(spelling)
            if previous is not None and previous != key:
                fail(f"{language}: duplicate spelling {spelling!r} for {previous} and {key}")
            seen[spelling] = key

    for row in rows:
        key = (row["domain"], row["bits"])
        if key in DISPLAY_ONLY and row["role"] != "display":
            fail(f"{key}: structural/display identity became callable surface")
        if key not in DISPLAY_ONLY and row["role"] == "display":
            fail(f"{key}: unexpected display-only role")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-generated",
        action="store_true",
        help="rewrite the checked-in Rust projection from Lisp-owned surface data",
    )
    return parser.parse_args()


def main() -> int:
    args = arguments()
    rows = parse_rows()
    validate(rows)

    expected_generated = render_generated(rows)
    if args.write_generated:
        GENERATED.write_text(expected_generated, encoding="utf-8")
    else:
        if not GENERATED.exists():
            fail(f"generated runtime projection is missing: {GENERATED}")
        current_generated = GENERATED.read_text(encoding="utf-8")
        if current_generated != expected_generated:
            fail(
                "generated runtime projection is stale; run "
                "python3 scripts/check-domain-surfaces-d1-d4.py --write-generated"
            )

    print("D1-D5-SURFACE-GUARD: PASS")
    print("rows=62 d1=2 d2=4 d3=8 d4=16 d5=32")
    print("projection=d1-d5 uk+sa exact-domain; source-routing=d3+d4+d5 non-display")
    print("uk=unique sa=unique exact-width=preserved legacy-byte=absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
