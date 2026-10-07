#!/usr/bin/env python3
"""Generate human domain documentation from binary Contract authority.

Semantic membership comes ONLY from a JSON inventory emitted by the Rust
`sens-contract-inventory` binary. Canonical per-domain tables contribute
presentation strings for coordinates that already exist in that inventory.
They may never add, remove, or infer a semantic resident.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from domain_tables import CURRENT_HUMAN_TABLES, read_domain_table

SCHEMA = "sens-binary-contract-inventory/v1"


def _authority_coordinates(inventory: dict) -> dict[str, set[str]]:
    if inventory.get("schema") != SCHEMA:
        raise ValueError(f"expected {SCHEMA}")
    if inventory.get("reader") != "canonical-visible-binary":
        raise ValueError("inventory was not produced through the canonical visible-binary reader")
    if inventory.get("d2_complete") is not True:
        raise ValueError("binary Contract does not exercise the complete D2 structure law")

    coords: dict[str, set[str]] = {}
    d2 = set(inventory.get("d2_structure", []))
    if d2 != {"00", "01", "10", "11"}:
        raise ValueError(f"D2 structure mismatch: {sorted(d2)}")
    coords["D2"] = d2

    residents = inventory.get("residents")
    if not isinstance(residents, dict):
        raise ValueError("inventory residents must be an object")

    for width in range(1, 10):
        domain = f"D{width}"
        if width == 2:
            continue
        values = residents.get(domain)
        if not isinstance(values, list):
            raise ValueError(f"missing {domain} binary authority")
        expected_width = width
        bits = set()
        for value in values:
            if not isinstance(value, str) or len(value) != expected_width or set(value) - {"0", "1"}:
                raise ValueError(f"invalid exact coordinate {domain}:{value!r}")
            if value in bits:
                raise ValueError(f"duplicate exact coordinate {domain}:{value}")
            bits.add(value)
        coords[domain] = bits

    return coords


def _projection_rows(paths=CURRENT_HUMAN_TABLES):
    rows = {}
    for path in paths:
        for row in read_domain_table(Path(path)):
            key = (row.domain, row.bits)
            if key in rows:
                raise ValueError(f"duplicate projection row {row.domain}:{row.bits}")
            rows[key] = row
    return rows


def _cell(value: str | None) -> str:
    if value is None:
        return ""
    return value.replace("|", "\\|").replace("\n", " ")


def generate_markdown(inventory: dict, paths=CURRENT_HUMAN_TABLES) -> str:
    authority = _authority_coordinates(inventory)
    projections = _projection_rows(paths)

    for domain, bits in authority.items():
        projected = {row_bits for (row_domain, row_bits) in projections if row_domain == domain}
        if projected != bits:
            missing = sorted(bits - projected)
            extra = sorted(projected - bits)
            raise ValueError(
                f"{domain} projection drift: missing={missing[:8]} extra={extra[:8]}"
            )

    lines = [
        "<!-- GENERATED: semantic membership comes from canonical binary Contract authority. -->",
        "<!-- Human strings below are presentation projections only. -->",
        "",
        "# Contract 11.8 — generated domain projection",
        "",
        "| domain | bits | ук | укр | san | en | LISP | sym |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for width in range(1, 10):
        domain = f"D{width}"
        for bits in sorted(authority[domain]):
            row = projections[(domain, bits)]
            lines.append(
                "| "
                + " | ".join(
                    [
                        domain,
                        bits,
                        _cell(row.uk),
                        _cell(row.ukr),
                        _cell(row.san),
                        _cell(row.en),
                        _cell(row.lisp),
                        _cell(row.sym),
                    ]
                )
                + " |"
            )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    rendered = generate_markdown(inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
