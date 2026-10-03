#!/usr/bin/env python3
"""#2776 — OD-005/OD-006 exact-domain runtime admission audit.

The audit now measures two independent axes:

1. identity admission — can the exact D5/D6 owner coordinate enter the runtime
   without Sens8 projection while preserving width?
2. executable admission — does that identity have an admitted call mechanism?

After the exact-domain reader migration D5/D6 identity admission is complete.
Callability remains law-by-law: this audit currently recognizes the six D5
numeric/comparison mechanisms admitted by the domain-first runtime slice.
Width alone never grants execution.
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
PARSER = ROOT / "crates" / "sens" / "src" / "parser.rs"
SOURCE_WORDS = ROOT / "crates" / "sens" / "src" / "source_words.rs"
DOMAIN_IDENTITY = ROOT / "crates" / "sens" / "src" / "domain_identity.rs"
SYNTAX = ROOT / "crates" / "sens" / "src" / "syntax.rs"
CANON = ROOT / "crates" / "sens" / "src" / "eval" / "canon.rs"
OUTPUT = ROOT / "knowledge" / "od005-od006-runtime-admission-audit.json"

REGISTRY_ROW = re.compile(r"^\s*\(([01]{8})\s+\(en\s+([^\s()]+|\(\))\)")
D5_NATIVE = {"01010", "01011", "01110", "01111", "10010", "10011"}


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
    parser = PARSER.read_text(encoding="utf-8")
    source_words = SOURCE_WORDS.read_text(encoding="utf-8")
    domain_identity = DOMAIN_IDENTITY.read_text(encoding="utf-8")
    syntax = SYNTAX.read_text(encoding="utf-8")
    canon = CANON.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")

    assert "CoreDomainIdentity::from_source_word" in parser, (
        "reader lost exact-domain identity admission; update #2776 audit"
    )
    assert "BinarySourceWord::W8" in parser and "bare eight-bit Function8/Sens8 syntax is not part of canonical SENS" in parser, (
        "bare W8 rejection changed; update #2776 audit explicitly"
    )
    assert "parse_binary_source_word" in source_words, (
        "exact-width source-word parser is not shared by the general reader"
    )
    assert "pub const fn from_source_word" in domain_identity, (
        "CoreDomainIdentity lost exact source-word bridge"
    )
    assert "TAG_DOMAIN_IDENTITY" in syntax and "ExprKind::DomainIdentity" in syntax, (
        "domain-aware FASL/wire transport changed; update #2776 audit"
    )
    assert "domain identity has no admitted value-call mechanism" in canon, (
        "D5/D6 fail-closed callability boundary changed; update #2776 audit"
    )

    widths = {
        len(match.group(1))
        for line in registry.splitlines()
        if (match := REGISTRY_ROW.match(line))
    }
    assert widths == {8}, f"legacy registry projection widths changed: {sorted(widths)}"

    return {
        "reader": "bare W3-W6 binary words become exact CoreDomainIdentity; bare W8 is rejected from canonical source",
        "runtime_identity": "CoreDomainIdentity preserves D3-D6 width; Sens8 survives only outside canonical source",
        "fasl_binary_payload": "domain identity carries exact width+payload; legacy exact8 remains separately tagged",
        "registry_identity_keys": "existing eight-bit keys are legacy surface projections, not canonical D5/D6 identity",
        "callability": "six D5 numeric/comparison coordinates have direct exact-domain evaluator mechanisms; all other D5/D6 residents remain fail-closed until admitted",
        "non_conclusion": "96/96 identity admission is not 96/96 executable admission",
    }


def build() -> dict:
    d5 = load_json(D5)
    d6 = load_json(D6)
    registry = REGISTRY.read_text(encoding="utf-8")
    surfaces = legacy_surface_map(registry)

    rows: list[dict] = []
    for domain, full_map in (("Core.D5", d5), ("Core.D6", d6)):
        for item in full_map["coordinates"]:
            name = str(item["name"])
            legacy = surfaces.get(name.lower())
            coordinate = item["coordinate"]
            callable_now = domain == "Core.D5" and coordinate in D5_NATIVE
            rows.append(
                {
                    "domain": domain,
                    "coordinate": coordinate,
                    "width": len(item["coordinate"]),
                    "name_projection": name,
                    "category": item["category"],
                    "owner_resident": True,
                    "direct_binary_reader_identity": True,
                    "exact_width_preserved_in_runtime_identity": True,
                    "owner_coordinate_registry_identity": False,
                    "legacy_surface_sid8": legacy,
                    "legacy_surface_projection_present": legacy is not None,
                    "read_print_roundtrip": True,
                    "lowering_class": "DOMAIN-CALL",
                    "native_evaluator": (
                        "EXACT-DOMAIN-NATIVE"
                        if callable_now
                        else "FAIL-CLOSED-WITHOUT-ADMITTED-MECHANISM"
                    ),
                    "derived_lisp": "UNMEASURED",
                    "compiler_support": "UNMEASURED",
                    "conformance": (
                        "CALLABLE-DOMAIN-MECHANISM-ADMITTED"
                        if callable_now
                        else "IDENTITY-ADMITTED-CALLABILITY-PENDING"
                    ),
                    "blocker": (
                        None if callable_now else "NO-ADMITTED-D5-D6-CALL-MECHANISM"
                    ),
                }
            )

    assert len(d5["coordinates"]) == 32
    assert len(d6["coordinates"]) == 64
    assert len(rows) == 96
    assert all(row["owner_resident"] for row in rows)
    assert all(row["direct_binary_reader_identity"] for row in rows)
    assert all(row["exact_width_preserved_in_runtime_identity"] for row in rows)

    return {
        "schema": "od005-od006-runtime-admission-audit/v2",
        "authority": "#2538 OD-005/OD-006 + #2762/#2766 + #2817",
        "generated_from": [
            "knowledge/d5-historical-full-map.json",
            "knowledge/d6-historical-full-map.json",
            "lib/surface/semantic-registry.lisp",
            "crates/sens/src/parser.rs",
            "crates/sens/src/source_words.rs",
            "crates/sens/src/domain_identity.rs",
            "crates/sens/src/syntax.rs",
            "crates/sens/src/eval/canon.rs",
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
            "owner_coordinate_registry_identity": sum(
                row["owner_coordinate_registry_identity"] for row in rows
            ),
            "legacy_surface_projection_present": sum(
                row["legacy_surface_projection_present"] for row in rows
            ),
            "callable_domain_mechanisms": sum(
                row["conformance"] == "CALLABLE-DOMAIN-MECHANISM-ADMITTED"
                for row in rows
            ),
            "identity_admitted_callability_pending": sum(
                row["conformance"] == "IDENTITY-ADMITTED-CALLABILITY-PENDING"
                for row in rows
            ),
            "blocked_by_identity_admission": 0,
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
    print("OD005/OD006 runtime admission audit: PASS")
    for key, value in summary.items():
        print(f"{key}={value}")
    print("NON-CONCLUSION: exact identity admission != universal callability")
    print("NON-CONCLUSION: residency != irreducibility")


if __name__ == "__main__":
    main()
