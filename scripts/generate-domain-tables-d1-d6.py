#!/usr/bin/env python3
"""Generate/check canonical D1-D6 human projection tables."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d7-foundation.json"
PROJECTION = ROOT / "knowledge/domain-table-projection-d1-d6.json"
OUTPUT = ROOT / "docs/generated/domain-tables-d1-d6.md"
SURFACE_SOURCES = (
    ROOT / "lib/surface/domain-surfaces-d1-d4.lisp",
    ROOT / "lib/surface/domain-surfaces-d5.lisp",
)

COLUMNS = ["ук", "укр", "san", "eng", "LISP", "SUM"]
EMPTY_MARKER = "()"
HEADER = "| bits | ук | укр | san | eng | LISP | SUM |"
DIVIDER = "|---|---|---|---|---|---|---|"

EXACT_ROW = re.compile(
    r'^\s*\(row\s+(D[1-5])\s+"([01]+)"\s+(\S+)\s+'
    r'"([^"]+)"\s+"([^"]+)"\s+"([^"]+)"\s+(\S+)\s+(\S+)\)\s*$'
)


def fail(message: str) -> None:
    raise SystemExit(f"DOMAIN-TABLES-D1-D6: FAIL: {message}")


def load_exact_surfaces() -> dict[tuple[str, str], dict[str, str]]:
    rows: dict[tuple[str, str], dict[str, str]] = {}
    for path in SURFACE_SOURCES:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.lstrip().startswith("(row "):
                continue
            match = EXACT_ROW.match(line)
            if not match:
                fail(f"cannot parse exact surface row at {path}:{line_no}")
            domain, bits, _role, eng, uk, san, _uk_status, _san_status = match.groups()
            rows[(domain, bits)] = {"uk": uk, "san": san, "eng": eng}
    return rows


def validate(
    foundation: dict,
    projection: dict,
    exact_surfaces: dict[tuple[str, str], dict[str, str]],
) -> None:
    if projection.get("columns") != COLUMNS:
        fail(f"column order must be {COLUMNS!r}")
    if projection.get("empty_marker") != EMPTY_MARKER:
        fail(f"empty marker must be {EMPTY_MARKER!r}")

    domains = projection.get("domains")
    if not isinstance(domains, list) or len(domains) != 6:
        fail("projection must contain exactly D1-D6")

    total = 0
    seen: set[tuple[str, str]] = set()

    for width, projected in enumerate(domains, start=1):
        domain = f"D{width}"
        if projected.get("domain") != domain:
            fail(f"expected {domain} at position {width}")

        current = foundation["domains"][domain]
        name = current.get("sanskrit_name")
        if not name:
            fail(f"{domain}: missing sanskrit_name in ratified foundation")
        if projected.get("name") != name:
            fail(f"{domain}: projection name drift")

        rows = projected.get("rows")
        if not isinstance(rows, list) or len(rows) != (1 << width):
            fail(f"{domain}: expected {1 << width} rows")

        expected_bits = sorted(current["residents"], key=lambda b: int(b, 2))
        actual_bits = [row.get("bits") for row in rows]
        if actual_bits != expected_bits:
            fail(f"{domain}: row bit order/coverage drift")

        for row in rows:
            bits = row["bits"]
            resident = row.get("resident")
            expected_resident = current["residents"][bits]
            if resident != expected_resident:
                fail(f"{domain}:{bits}: resident drift {resident!r} != {expected_resident!r}")

            key = (domain, bits)
            if key in seen:
                fail(f"duplicate key {domain}:{bits}")
            seen.add(key)

            values = row.get("values")
            if not isinstance(values, list) or len(values) != 6:
                fail(f"{domain}:{bits}: expected six surface columns")

            expected_sum = f"{name}:{bits}={resident}"
            if values[5] != expected_sum:
                fail(f"{domain}:{bits}: SUM drift")

            if width <= 5:
                exact = exact_surfaces.get(key)
                if exact is None:
                    fail(f"{domain}:{bits}: missing current exact surface row")
                if values[0] != exact["uk"]:
                    fail(f"{domain}:{bits}: ук drift from exact-domain source")
                if values[2] != exact["san"]:
                    fail(f"{domain}:{bits}: san drift from exact-domain source")
                if values[3] != exact["eng"]:
                    fail(f"{domain}:{bits}: eng drift from exact-domain source")

            total += 1

    if total != 126:
        fail(f"expected 126 rows, found {total}")
    if len(exact_surfaces) != 62:
        fail(f"expected 62 exact D1-D5 surface rows, found {len(exact_surfaces)}")


def cell(value: object) -> str:
    if value is None or value == "":
        return EMPTY_MARKER
    return str(value)


def render(projection: dict) -> str:
    lines = [
        "# Domain tables D1–D6",
        "",
        "**Authority:** `knowledge/d1-d7-foundation.json` (#3572).",
        "",
        "Human projection source: `knowledge/domain-table-projection-d1-d6.json`.",
        "Exact identity remains `bits + domain + ratified law`.",
        "",
        "Canonical surface order: **ук → укр → san → eng → LISP → SUM**.",
        f"Empty/missing surface marker: `{projection['empty_marker']}`.",
        "",
    ]

    for domain in projection["domains"]:
        lines += [f"## {domain['name']} ({domain['domain']})", "", HEADER, DIVIDER]
        for row in domain["rows"]:
            values = [cell(value) for value in row["values"]]
            rendered = " | ".join(f"`{value}`" for value in values)
            lines.append(f"| `{row['bits']}` | {rendered} |")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    projection = json.loads(PROJECTION.read_text(encoding="utf-8"))
    exact_surfaces = load_exact_surfaces()
    validate(foundation, projection, exact_surfaces)
    generated = render(projection)

    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(generated, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        return 0

    if not OUTPUT.exists():
        fail(f"missing generated file: {OUTPUT.relative_to(ROOT)}")
    if OUTPUT.read_text(encoding="utf-8") != generated:
        fail("generated markdown is stale; run with --write")

    print("DOMAIN-TABLES-D1-D6: PASS")
    print("rows=126 order=ук->укр->san->eng->LISP->SUM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
