#!/usr/bin/env python3
"""OD-006 D6 runtime-admission audit (#2766).

Owner residency is already ratified 64/64. This audit asks a different question:
which exact D6 identities are mechanically representable and which are actually
admitted into the current semantic/runtime path?

It performs no semantic implementation and no name-based identity inference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER_MAP = ROOT / "knowledge" / "d6-historical-full-map.json"
SOURCE_WORDS = ROOT / "crates" / "sens" / "src" / "source_words.rs"
SOURCE_PACKING = ROOT / "crates" / "sens" / "src" / "source_packing.rs"
DOMAIN_WORDS = ROOT / "crates" / "sens" / "src" / "domain_words.rs"
VALUE = ROOT / "crates" / "sens" / "src" / "value.rs"
REGISTRY = ROOT / "crates" / "sens" / "src" / "semantic_registry.rs"
LOWER = ROOT / "crates" / "sens" / "src" / "eval" / "lower.rs"
OUT = ROOT / "knowledge" / "d6-runtime-admission-audit.json"

SELECTOR_COORDS = {
    f"{parent}{suffix}"
    for parent in (
        "10100","10101","10110","10111",
        "11000","11001","11010","11011",
    )
    for suffix in ("0","1")
}


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def mechanism_facts() -> dict:
    source = text(SOURCE_WORDS)
    packing = text(SOURCE_PACKING)
    domain = text(DOMAIN_WORDS)
    value = text(VALUE)
    registry = text(REGISTRY)
    lower = text(LOWER)

    facts = {
        "bit6_source_variant": "W6(Bit6)" in source,
        "bit6_source_parse": "6 => BinarySourceWord::W6(Bit6::new(packed)?)" in source,
        "bit6_source_display": 'width = self.width()' in source and '"{:0width$b}"' in source,
        "bit6_packing": "BinarySourceWord::W6(word) => packer.push(word)" in packing,
        "bit6_unpacking": "6 => BinarySourceWord::W6(packed.read::<6>(bit_offset)?)" in packing,
        "typed_d6_carrier": (
            "Bit6" in domain
            or "Domain6" in domain
            or "D6" in domain
        ),
        "value_d6_identity": (
            "Value::D6" in value
            or "D6(" in value
            or "Bit6" in value
        ),
        "registry_d6_identity": (
            "type SemanticId = Sens8" not in registry
            or "Bit6" in registry
            or "Domain6" in registry
        ),
        "lowering_d6_identity": (
            "Bit6" in lower
            or "Domain6" in lower
            or "D6" in lower
        ),
    }

    expected = {
        "bit6_source_variant": True,
        "bit6_source_parse": True,
        "bit6_source_display": True,
        "bit6_packing": True,
        "bit6_unpacking": True,
        "typed_d6_carrier": True,
        "value_d6_identity": False,
        "registry_d6_identity": False,
        "lowering_d6_identity": False,
    }
    if facts != expected:
        raise AssertionError(
            "D6 runtime substrate changed; update audit classification deliberately: "
            f"expected={expected} actual={facts}"
        )
    return facts


def build() -> dict:
    owner = json.loads(OWNER_MAP.read_text(encoding="utf-8"))
    facts = mechanism_facts()

    assert owner["schema"] == "d6-historical-full-map/v1"
    assert owner["width"] == 6
    assert owner["capacity"] == 64
    assert len(owner["coordinates"]) == 64
    assert owner["status_counts"]["unallocated"] == 0

    rows = []
    for item in owner["coordinates"]:
        coordinate = item["coordinate"]
        assert len(coordinate) == 6 and set(coordinate) <= {"0","1"}

        selector = coordinate in SELECTOR_COORDS
        rows.append({
            "coordinate": coordinate,
            "name": item["name"],
            "parent_d5": item["parent_d5"],
            "owner_residency": "YES",
            "owner_authority": owner["authority"],
            "source_exact_w6": "YES",
            "source_print_exact_w6": "YES",
            "packed_roundtrip_w6": "YES",
            "typed_d6_carrier": "YES",
            "runtime_value_identity": "NO",
            "semantic_registry_d6_identity": "NO",
            "lowering_d6_identity": "NO",
            "native_evaluator_d6_identity": "NO",
            "compiler_d6_identity": "NOT-AUDITED",
            "semantic_identity_test": "NO",
            "selector_generator_evidence": "YES" if selector else "NO",
            "implementation_status": (
                "MECHANICAL-W6+GENERATOR-EVIDENCE"
                if selector else
                "MECHANICAL-W6-ONLY"
            ),
        })

    assert sum(r["selector_generator_evidence"] == "YES" for r in rows) == 16
    assert all(r["owner_residency"] == "YES" for r in rows)
    assert all(r["source_exact_w6"] == "YES" for r in rows)
    assert all(r["typed_d6_carrier"] == "YES" for r in rows)
    assert all(r["native_evaluator_d6_identity"] == "NO" for r in rows)

    return {
        "schema": "d6-runtime-admission-audit/v1",
        "issue": "#2766",
        "principle": "typed Core.D6 admission is explicit and remains separate from value/registry/lowering/evaluator semantics",
        "owner_map": "knowledge/d6-historical-full-map.json",
        "mechanism_facts": facts,
        "summary": {
            "owner_resident": 64,
            "source_exact_w6": 64,
            "packed_roundtrip_w6": 64,
            "typed_d6_carrier": 64,
            "runtime_value_identity": 0,
            "semantic_registry_d6_identity": 0,
            "lowering_d6_identity": 0,
            "native_evaluator_d6_identity": 0,
            "selector_generator_evidence": 16,
            "compiler_d6_identity": "NOT-AUDITED",
        },
        "rows": rows,
    }


def render(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args()

    data = build()
    payload = render(data)
    if args.write:
        OUT.write_text(payload, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != payload:
            print("D6-RUNTIME-ADMISSION-AUDIT=STALE")
            return 1
        print("D6-RUNTIME-ADMISSION-AUDIT=CURRENT")

    for key, value in data["summary"].items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
