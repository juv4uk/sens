#!/usr/bin/env python3
"""#2766 — D5 canonical runtime-admission audit.

Research/integration audit only. This script does not allocate semantics and
does not infer semantic residency from historical occupancy or human names.

It answers a narrower question:
    how far does an OD-005 exact five-bit coordinate currently travel through
    the executable canonical identity path?

Owner occupancy and semantic derivability remain separate concerns.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

MAP = ROOT / "knowledge/d5-historical-full-map.json"
SOURCE_WORDS = ROOT / "crates/sens/src/source_words.rs"
DOMAIN_WORDS = ROOT / "crates/sens/src/domain_words.rs"
PARSER = ROOT / "crates/sens/src/parser.rs"
SENS = ROOT / "crates/sens/src/sens.rs"
REGISTRY = ROOT / "crates/sens/src/semantic_registry.rs"
LOWER = ROOT / "crates/sens/src/eval/lower.rs"


def fail(message: str) -> None:
    raise SystemExit(f"D5-RUNTIME-ADMISSION-AUDIT=FAIL\n{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    require(path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load_owner_map() -> dict[str, Any]:
    data = json.loads(read(MAP))
    require(data.get("schema") == "d5-historical-full-map/v1", "unexpected D5 map schema")
    require(data.get("domain") == "Core.D5", "owner map domain is not Core.D5")
    require(data.get("width") == 5, "owner map width is not 5")
    require(data.get("capacity") == 32, "owner map capacity is not 32")

    rows = data.get("coordinates", [])
    require(len(rows) == 32, f"owner map must contain 32 rows, got {len(rows)}")

    coordinates = [row.get("coordinate") for row in rows]
    require(len(coordinates) == len(set(coordinates)), "duplicate D5 coordinate")
    require(
        coordinates == [f"{raw:05b}" for raw in range(32)],
        "owner map is not an exact complete 00000..11111 coordinate set",
    )
    for row in rows:
        require(
            re.fullmatch(r"[01]{5}", row["coordinate"]) is not None,
            f"invalid D5 coordinate {row['coordinate']}",
        )
        require(bool(row.get("name")), f"{row['coordinate']}: missing projection name")
    return data


def detect_runtime_shape() -> dict[str, Any]:
    source_words = read(SOURCE_WORDS)
    domain_words = read(DOMAIN_WORDS)
    parser = read(PARSER)
    sens = read(SENS)
    registry = read(REGISTRY)
    lower = read(LOWER)

    source_w5_variant = "W5(Bit5)" in source_words
    source_w5_parse_case = re.search(
        r"5\s*=>\s*BinarySourceWord::W5\s*\(", source_words
    ) is not None
    source_w5_roundtrip_display = (
        "width = self.width()" in source_words and "pub const fn width(self) -> usize" in source_words
    )

    # The ordinary executable parser currently admits semantic IDs only through
    # the exact 8-bit Sens8 path. A future D5 admission may use a different AST
    # variant; this detector intentionally reports that as a shape change which
    # must update the audit rather than silently guessing.
    parser_exact_8_sid = (
        "token.len() == 8" in parser
        and "Sens8::from_exact_bits(token)" in parser
        and "ExprKind::Sid(sid)" in parser
    )
    parser_mentions_w5_identity = any(
        marker in parser
        for marker in (
            "BinarySourceWord::W5",
            "Bit5",
            "D5Word",
            "Domain5",
            "D5Identity",
        )
    )

    typed_d5_carrier = any(
        marker in domain_words
        for marker in (
            "Bit5",
            "Bits<5>",
            "D5Word",
            "Domain5",
            "D5Identity",
        )
    )

    sens8_only_identity = (
        "pub struct Sens8" in sens
        and "pub type Sens = Sens8" in sens
        and "exactly eight" in sens.lower()
    )
    registry_sens8 = (
        "type SemanticId = Sens8" in registry
        and "SEMANTIC_ROWS.len(), 256" in registry
    )
    lower_sens8 = (
        "use crate::Sens8;" in lower
        and re.search(r"fn\s+head_sid\s*\([^)]*\)\s*->\s*Option<Sens8>", lower) is not None
    )

    canonical_d5_ast_identity = (
        typed_d5_carrier
        and parser_mentions_w5_identity
        and not sens8_only_identity
    )
    canonical_d5_registry_identity = canonical_d5_ast_identity and not registry_sens8
    canonical_d5_lowering_identity = canonical_d5_registry_identity and not lower_sens8

    return {
        "source_boundary": {
            "w5_variant": source_w5_variant,
            "w5_parse_case": source_w5_parse_case,
            "width_preserving_display": source_w5_roundtrip_display,
            "supported": source_w5_variant and source_w5_parse_case and source_w5_roundtrip_display,
        },
        "ordinary_parser": {
            "exact_8bit_sens_path_present": parser_exact_8_sid,
            "explicit_d5_identity_path_detected": parser_mentions_w5_identity,
            "canonical_d5_identity_admitted": canonical_d5_ast_identity,
        },
        "typed_domain_carrier": {
            "d5_type_detected": typed_d5_carrier,
        },
        "semantic_registry": {
            "sens8_identity_type": registry_sens8,
            "canonical_d5_identity_admitted": canonical_d5_registry_identity,
        },
        "lowering": {
            "sens8_head_identity": lower_sens8,
            "canonical_d5_identity_admitted": canonical_d5_lowering_identity,
        },
        "evaluator": {
            "canonical_d5_identity_status": (
                "READY-FOR-AUDIT"
                if canonical_d5_lowering_identity
                else "BLOCKED-BY-CANONICAL-IDENTITY-PATH"
            )
        },
    }


def build_report(owner: dict[str, Any], shape: dict[str, Any]) -> dict[str, Any]:
    source_ok = shape["source_boundary"]["supported"]
    ast_ok = shape["ordinary_parser"]["canonical_d5_identity_admitted"]
    carrier_ok = shape["typed_domain_carrier"]["d5_type_detected"]
    registry_ok = shape["semantic_registry"]["canonical_d5_identity_admitted"]
    lowering_ok = shape["lowering"]["canonical_d5_identity_admitted"]
    evaluator_status = shape["evaluator"]["canonical_d5_identity_status"]

    rows = []
    for row in owner["coordinates"]:
        rows.append(
            {
                "coordinate": row["coordinate"],
                "projection_name": row["name"],
                "owner_map_resident": True,
                "exact_width_source_boundary": source_ok,
                "typed_d5_carrier": carrier_ok,
                "canonical_ast_identity": ast_ok,
                "canonical_registry_identity": registry_ok,
                "canonical_lowering_identity": lowering_ok,
                "canonical_evaluator_identity": evaluator_status,
                "implementation_status": (
                    "CANONICAL-IDENTITY-PATH"
                    if lowering_ok
                    else "OWNER-MAP+W5-BOUNDARY-ONLY"
                ),
            }
        )

    def count_bool(field: str) -> int:
        return sum(row[field] is True for row in rows)

    return {
        "schema": "d5-runtime-admission-audit/v1",
        "authority": {
            "occupancy": "OD-005 / knowledge/d5-historical-full-map.json",
            "semantic_residency": "NOT-INFERRED-HERE",
            "human_names": "PROJECTION-ONLY",
        },
        "runtime_shape": shape,
        "summary": {
            "rows": len(rows),
            "owner_map_residents": count_bool("owner_map_resident"),
            "exact_width_source_boundary": count_bool("exact_width_source_boundary"),
            "typed_d5_carrier": count_bool("typed_d5_carrier"),
            "canonical_ast_identity": count_bool("canonical_ast_identity"),
            "canonical_registry_identity": count_bool("canonical_registry_identity"),
            "canonical_lowering_identity": count_bool("canonical_lowering_identity"),
            "canonical_evaluator_ready": sum(
                row["canonical_evaluator_identity"] == "READY-FOR-AUDIT"
                for row in rows
            ),
        },
        "rows": rows,
        "next_boundary": (
            "Introduce an exact D5 semantic identity path without widening/zero-padding to Sens8; "
            "then re-run this audit before implementing row semantics."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="")
    args = parser.parse_args()

    owner = load_owner_map()
    shape = detect_runtime_shape()
    require(shape["source_boundary"]["supported"], "W5 source-boundary support regressed")

    report = build_report(owner, shape)

    if args.json:
        target = Path(args.json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    summary = report["summary"]
    print("D5-RUNTIME-ADMISSION-AUDIT=PASS")
    print(f"owner-map-residents={summary['owner_map_residents']}/32")
    print(f"exact-width-source-boundary={summary['exact_width_source_boundary']}/32")
    print(f"typed-d5-carrier={summary['typed_d5_carrier']}/32")
    print(f"canonical-ast-identity={summary['canonical_ast_identity']}/32")
    print(f"canonical-registry-identity={summary['canonical_registry_identity']}/32")
    print(f"canonical-lowering-identity={summary['canonical_lowering_identity']}/32")
    print(f"canonical-evaluator-ready={summary['canonical_evaluator_ready']}/32")
    print("RULE=owner-residency-does-not-imply-runtime-admission")
    print("RULE=human-projection-does-not-alias-D5-to-Sens8")


if __name__ == "__main__":
    main()
