#!/usr/bin/env python3
"""Перевірка D5/D6 у канонічному читачі з точними доменними identity.

Звіт перевіряє лише розпізнавання D5/D6 як точних DomainIdentity. Він окремо
показує допуск до Core-операції: D5 такий має, D6 — лише для двох визначених
операцій. Резидентність не оголошується викличністю або повною реалізацією.
Історична SID8-мапа залишається лише provenance.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D5 = ROOT / "knowledge" / "d5-historical-full-map.json"
D6 = ROOT / "knowledge" / "d6-historical-full-map.json"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
READER = ROOT / "crates" / "sens" / "src" / "canonical_reader.rs"
IDENTITY = ROOT / "crates" / "sens" / "src" / "domain_identity.rs"
OUTPUT = ROOT / "knowledge" / "od005-od006-runtime-admission-audit.json"

REGISTRY_ROW = re.compile(r"^\s*\(([01]{8})\s+\(en\s+([^\s()]+|\(\))\)")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def legacy_surface_map(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        match = REGISTRY_ROW.match(line)
        if match and match.group(2) != "()":
            out[match.group(2).lower()] = match.group(1)
    return out


def source_contract() -> dict:
    reader = READER.read_text(encoding="utf-8")
    identity = IDENTITY.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")

    assert "pub fn parse_canonical_binary" in reader
    assert "DomainIdentity::from_source_word" in reader
    assert "Self::D5(value) => Some(CoreDomainIdentity::D5(value))" in identity
    assert "Self::D6(value)" in identity and "0b001110 | 0b001111" in identity
    assert "Self::D10(_)" in identity, "current identity frame must include D10"

    return {
        "reader": "canonical visible-binary source lifts exact-width W1-W9 words",
        "runtime_identity": "DomainIdentity<D1-D10>; D5/D6 preserve exact widths",
        "core_operation": "D5 admitted; D6 only 001110 and 001111",
        "historical_sid8": "provenance only; not a runtime identity or fallback",
        "non_conclusion": "identity does not assert evaluator coverage for every resident",
    }


def build() -> dict:
    d5 = load_json(D5)
    d6 = load_json(D6)
    registry = REGISTRY.read_text(encoding="utf-8")
    surfaces = legacy_surface_map(registry)

    rows: list[dict] = []
    d6_core_operations = {"001110", "001111"}
    for domain, full_map in (("Core.D5", d5), ("Core.D6", d6)):
        for item in full_map["coordinates"]:
            name = str(item["name"])
            legacy = surfaces.get(name.lower())
            coordinate = str(item["coordinate"])
            core_operation = domain == "Core.D5" or coordinate in d6_core_operations
            rows.append(
                {
                    "domain": domain,
                    "coordinate": coordinate,
                    "width": len(coordinate),
                    "name_projection": name,
                    "category": item["category"],
                    "owner_resident": True,
                    "direct_binary_reader_identity": True,
                    "exact_width_preserved_in_runtime_identity": True,
                    "current_domain_identity": True,
                    "core_operation_admitted": core_operation,
                    "legacy_surface_sid8": legacy,
                    "legacy_surface_projection_present": legacy is not None,
                    "read_print_roundtrip": "NOT_ASSERTED",
                    "lowering_class": "CORE_OPERATION" if core_operation else "IDENTITY_ONLY",
                    "native_evaluator": "NOT_ASSERTED",
                    "derived_lisp": "NOT_ASSERTED",
                    "compiler_support": "NOT_ASSERTED",
                    "conformance": "EXACT_DOMAIN_IDENTITY_PASS",
                    "callability_scope": "core-operation admission is separate from residency",
                }
            )

    assert len(d5["coordinates"]) == 32
    assert len(d6["coordinates"]) == 64
    assert len(rows) == 96
    assert all(row["owner_resident"] for row in rows)

    return {
        "schema": "od005-od006-runtime-admission-audit/v2",
        "authority": "#2538 OD-005/OD-006 + #2762/#2766",
        "generated_from": [
            "knowledge/d5-historical-full-map.json",
            "knowledge/d6-historical-full-map.json",
            "lib/surface/semantic-registry.lisp",
            "crates/sens/src/canonical_reader.rs",
            "crates/sens/src/domain_identity.rs",
        ],
        "current_source_contract": source_contract(),
        "summary": {
            "d5_owner_residents": len(d5["coordinates"]),
            "d6_owner_residents": len(d6["coordinates"]),
            "total_owner_residents": len(rows),
            "direct_binary_reader_identity": sum(
                row["direct_binary_reader_identity"] for row in rows
            ),
            "exact_width_runtime_identity": sum(
                row["exact_width_preserved_in_runtime_identity"] for row in rows
            ),
            "current_domain_identity": sum(
                row["current_domain_identity"] for row in rows
            ),
            "legacy_surface_projection_present": sum(
                row["legacy_surface_projection_present"] for row in rows
            ),
            "core_operation_admitted": sum(
                row["core_operation_admitted"]
                for row in rows
            ),
        },
        "rows": rows,
    }


def encoded() -> str:
    return json.dumps(build(), ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    content = encoded()
    if args.write:
        OUTPUT.write_text(content, encoding="utf-8")
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8")
        assert actual == content, (
            "runtime admission matrix is stale; run "
            "python3 scripts/audit-od005-od006-runtime-admission.py --write"
        )

    audit = json.loads(content)
    summary = audit["summary"]
    print("OD005/OD006 exact domain identity audit: PASS")
    for key, value in summary.items():
        print(f"{key}={value}")
    print("NON-CONCLUSION: domain identity != callability")
    print("NON-CONCLUSION: exact identity does not prove complete evaluator coverage")


if __name__ == "__main__":
    main()
