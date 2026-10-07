#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from generate_binary_contract_domain_projection import generate_markdown

ROOT = Path(__file__).resolve().parents[1]


def migration_inventory() -> dict:
    foundation = json.loads(
        (ROOT / "knowledge" / "d1-d9-foundation.json").read_text(encoding="utf-8")
    )
    domains = foundation["domains"]
    residents = {}
    total = 0

    for width in range(1, 10):
        domain = f"D{width}"
        bits = sorted(domains[domain]["residents"].keys())
        if width == 2:
            continue
        residents[domain] = bits
        total += len(bits)

    return {
        "schema": "sens-binary-contract-inventory/v1",
        "reader": "canonical-visible-binary",
        "d2_structure": sorted(domains["D2"]["residents"].keys()),
        "d2_complete": True,
        "residents": residents,
        "coordinate_count": total,
    }


def main() -> int:
    inventory = migration_inventory()
    rendered = generate_markdown(inventory)

    rows = [line for line in rendered.splitlines() if line.startswith("| D")]
    assert len(rows) == 1020, len(rows)
    assert inventory["coordinate_count"] == 1016
    assert "| D1 | 0 |" in rendered
    assert "| D2 | 00 |" in rendered
    assert "| D3 | 000 |" in rendered
    assert "| D9 | 111111111 |" in rendered

    # Projection tables are never allowed to mint a resident absent from
    # binary authority. Removing one coordinate must fail rather than silently
    # regenerating it from the human table.
    broken = json.loads(json.dumps(inventory))
    broken["residents"]["D9"].remove("111111111")
    try:
        generate_markdown(broken)
    except ValueError as error:
        assert "D9 projection drift" in str(error)
    else:
        raise AssertionError("human projection illegally restored a missing D9 resident")

    print("binary-contract-projection: PASS (1020 rows; 1016 non-D2 residents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
