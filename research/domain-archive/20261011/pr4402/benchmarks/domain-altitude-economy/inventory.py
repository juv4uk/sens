#!/usr/bin/env python3
"""Build the strict D8 derivability inventory for #4398.

This script does not infer derivability from names. It intersects current
ratified D8 rows with explicit derivability metadata from the ratified/current
semantic inventory.

A row is only a *candidate* for residency-dividend work. It is not measurable
until a separate executable lower-domain expansion artifact and observable
digest witness are attached.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


STRICT_DERIVABILITY = {"DERIVED-NO-SLOT", "GENERATED/STRUCTURAL"}


def name_of(row: dict[str, Any]) -> str:
    return str(
        row.get("resident")
        or row.get("semantic_name")
        or row.get("name")
        or ""
    )


def strict_derivation(row: dict[str, Any], prior: dict[str, Any]) -> bool:
    derivability = str(prior.get("derivability") or row.get("derivability") or "")
    comparison = str(
        prior.get("lower_domain_comparison")
        or row.get("lower_domain_comparison")
        or ""
    )
    return (
        derivability in STRICT_DERIVABILITY
        or "Generated/refined from" in comparison
        or "recursively definable from lower-domain" in comparison
    )


def build_inventory(ratified: dict[str, Any], semantic_inventory: dict[str, Any]) -> dict[str, Any]:
    ratified_rows = ratified.get("rows")
    inventory_rows = semantic_inventory.get("rows")
    if not isinstance(ratified_rows, list) or len(ratified_rows) != 256:
        raise ValueError("expected current ratified D8 rows[256]")
    if not isinstance(inventory_rows, list) or len(inventory_rows) != 256:
        raise ValueError("expected current D8 semantic inventory rows[256]")

    by_name = {name_of(row).upper(): row for row in inventory_rows if name_of(row)}
    candidates = []
    for row in ratified_rows:
        resident = name_of(row)
        prior = by_name.get(resident.upper(), {})
        if not strict_derivation(row, prior):
            continue
        comparison = str(
            prior.get("lower_domain_comparison")
            or row.get("lower_domain_comparison")
            or ""
        )
        derivability = str(prior.get("derivability") or row.get("derivability") or "")
        candidates.append(
            {
                "resident": resident,
                "coordinate": row.get("coordinate")
                or row.get("bits")
                or row.get("d8_coordinate"),
                "relation_class": row.get("relation_class")
                or prior.get("relation_class"),
                "derivability": derivability,
                "lower_domain_comparison": comparison,
                "semantic_behavior": row.get("semantic_behavior")
                or prior.get("behavior")
                or prior.get("semantic_behavior"),
                "evidence": row.get("evidence") or prior.get("evidence") or [],
                "dividend_ready": False,
                "missing_for_dividend": [
                    "executable_exact_binary_lower_domain_expansion",
                    "resident_vs_expansion_observable_digest_parity",
                    "exact_bits_for_both_forms",
                ],
            }
        )

    return {
        "schema": "sens-domain-altitude-d8-inventory/v1",
        "semantic_authority": False,
        "source_authority": {
            "ratified": "knowledge/d8-ratified.json",
            "semantic_inventory": "knowledge/d8-v2-semantic-inventory.json",
        },
        "selection_rule": (
            "explicit DERIVED-NO-SLOT / GENERATED-STRUCTURAL / concrete lower-domain derivation metadata"
        ),
        "candidate_count": len(candidates),
        "dividend_ready_count": sum(1 for row in candidates if row["dividend_ready"]),
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ratified",
        type=Path,
        default=Path("knowledge/d8-ratified.json"),
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("knowledge/d8-v2-semantic-inventory.json"),
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = build_inventory(
        json.loads(args.ratified.read_text(encoding="utf-8")),
        json.loads(args.inventory.read_text(encoding="utf-8")),
    )
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    print(
        f"strict_candidates={report['candidate_count']} "
        f"dividend_ready={report['dividend_ready_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
