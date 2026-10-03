#!/usr/bin/env python3
"""#2776 — OD-005/OD-006 runtime admission audit.

Transitional integration guard. It measures the current gap between:
  owner-ratified historical residency (D5/D6 full maps)
and
  executable canonical identity admission (reader/carrier/registry).

It intentionally makes no evaluator/lowering claims beyond UNMEASURED.
The runtime carrier is now domain-qualified through CallableIdentity while
the ordinary reader and semantic registry remain transitional. This guard
measures those boundaries independently.
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
CALLABLE = ROOT / "crates" / "sens" / "src" / "callable_identity.rs"
SYNTAX = ROOT / "crates" / "sens" / "src" / "syntax.rs"
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
    parser = PARSER.read_text(encoding="utf-8")
    callable_identity = CALLABLE.read_text(encoding="utf-8")
    syntax = SYNTAX.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")

    assert "token.len() == 8" in parser, (
        "reader is no longer exact-8-only; update #2776 audit for the new identity grammar"
    )
    assert "pub enum CallableIdentity" in callable_identity, (
        "domain-qualified runtime callable identity disappeared"
    )
    assert "Core(CoreDomainIdentity)" in callable_identity and "Legacy8(u8)" in callable_identity, (
        "CallableIdentity must keep Core domains distinct from exact-eight compatibility"
    )
    assert "Sid(CallableIdentity)" in syntax, (
        "AST no longer carries the unified callable identity"
    )
    assert "TAG_DOMAIN_IDENTITY" in syntax and "CallableIdentity::legacy8(value)" in syntax, (
        "FASL/wire identity transport changed; update #2776 audit deliberately"
    )

    widths = {
        len(match.group(1))
        for line in registry.splitlines()
        if (match := REGISTRY_ROW.match(line))
    }
    assert widths == {8}, f"legacy registry key widths changed: {sorted(widths)}"

    return {
        "reader": "bare binary SID is admitted only at exact width 8",
        "runtime_identity": "CallableIdentity = Core(CoreDomainIdentity) | Legacy8(u8)",
        "fasl_binary_payload": "legacy8: one packed byte; Core: explicit domain width + packed payload",
        "registry_identity_keys": "exactly eight bits",
        "non_conclusion": (
            "owner residency is not rejected; runtime admission is not yet implemented"
        ),
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
            rows.append(
                {
                    "domain": domain,
                    "coordinate": item["coordinate"],
                    "width": len(item["coordinate"]),
                    "name_projection": name,
                    "category": item["category"],
                    "owner_resident": True,
                    "direct_binary_reader_identity": False,
                    "exact_width_preserved_in_runtime_identity": True,
                    "owner_coordinate_registry_identity": False,
                    "legacy_surface_sid8": legacy,
                    "legacy_surface_projection_present": legacy is not None,
                    "read_print_roundtrip": False,
                    "lowering_class": "UNMEASURED",
                    "native_evaluator": "UNMEASURED",
                    "derived_lisp": "UNMEASURED",
                    "compiler_support": "UNMEASURED",
                    "conformance": "BLOCKED-BY-IDENTITY-ADMISSION",
                    "blocker": "READER-AND-REGISTRY-ADMISSION",
                }
            )

    assert len(d5["coordinates"]) == 32
    assert len(d6["coordinates"]) == 64
    assert len(rows) == 96
    assert all(row["owner_resident"] for row in rows)

    return {
        "schema": "od005-od006-runtime-admission-audit/v1",
        "authority": "#2538 OD-005/OD-006 + #2762/#2766",
        "generated_from": [
            "knowledge/d5-historical-full-map.json",
            "knowledge/d6-historical-full-map.json",
            "lib/surface/semantic-registry.lisp",
            "crates/sens/src/parser.rs",
            "crates/sens/src/callable_identity.rs",
            "crates/sens/src/syntax.rs",
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
            "blocked_by_identity_admission": sum(
                row["conformance"] == "BLOCKED-BY-IDENTITY-ADMISSION"
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
    print("OD005/OD006 runtime admission audit: PASS")
    for key, value in summary.items():
        print(f"{key}={value}")
    print("NON-CONCLUSION: residency != irreducibility")
    print("NON-CONCLUSION: no D5/D6 semantic implementation is added here")


if __name__ == "__main__":
    main()
