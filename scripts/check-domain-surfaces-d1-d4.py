#!/usr/bin/env python3
"""Guard D1-D5 runtime surfaces from the canonical per-domain tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from domain_tables import DOMAIN_TABLES, read_domain_tables

ROOT = Path(__file__).resolve().parents[1]
SOURCES = DOMAIN_TABLES[:5]
GENERATED = ROOT / "crates/sens/src/domain_surface_registry_generated.rs"

EXPECTED_COUNTS = {"D1": 2, "D2": 4, "D3": 8, "D4": 16, "D5": 32}
DISPLAY_ONLY = {("D2", f"{n:02b}") for n in range(4)} | {("D3", "000")}


def fail(message: str) -> None:
    raise SystemExit(f"D1-D5-SURFACE-GUARD: FAIL: {message}")


def parse_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in read_domain_tables(SOURCES):
        if row.en is None or row.uk is None or row.san is None:
            fail(f"{row.domain}:{row.bits}: en/uk/san must be present")
        rows.append(
            {
                "domain": row.domain,
                "bits": row.bits,
                "role": row.role,
                "en": row.en,
                "uk": row.uk,
                "sa": row.san,
            }
        )
    return rows


def rust_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_generated(rows: list[dict[str, str]]) -> str:
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Authority: lib/domains/d1.lisp ... lib/domains/d5.lisp",
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
            fail(f"{domain}: table is not complete exact-width coverage")

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
        if key == ("D3", "000") and any(row[name] != "()" for name in ("en", "uk", "sa")):
            fail("D3:000 must project literally as () in every language")
        if row["role"] == "predicate":
            if not row["uk"].endswith("?"):
                fail(f"{key}: predicate UK surface must end in ?")
            if not row["en"].endswith("?"):
                fail(f"{key}: predicate EN surface must end in ?")
            if row["sa"].endswith("?"):
                fail(f"{key}: predicate Sanskrit surface must not end in ?")

        if key in DISPLAY_ONLY and row["role"] != "display":
            fail(f"{key}: structural/display identity became callable surface")
        if key not in DISPLAY_ONLY and row["role"] == "display":
            fail(f"{key}: unexpected display-only role")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-generated",
        action="store_true",
        help="rewrite Rust projection from canonical per-domain tables",
    )
    return parser.parse_args()


def main() -> int:
    args = arguments()
    rows = parse_rows()
    validate(rows)

    expected_generated = render_generated(rows)
    if args.write_generated:
        GENERATED.write_text(expected_generated, encoding="utf-8")
    elif not GENERATED.exists():
        fail(f"generated runtime projection is missing: {GENERATED}")
    elif GENERATED.read_text(encoding="utf-8") != expected_generated:
        fail(
            "generated runtime projection is stale; run "
            "python3 scripts/check-domain-surfaces-d1-d4.py --write-generated"
        )

    print("D1-D5-SURFACE-GUARD: PASS")
    print("rows=62 source=lib/domains/d1..d5 uk+san exact-domain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
