#!/usr/bin/env python3
"""#2370 exact-width generation accounting.

Research-only. This script combines:
- the current exact-width function-status census;
- the #2304 semantic-fact ledger;
- fresh #2323 selector certificate storage/mechanism evidence.

It deliberately reports UNKNOWN when selector root/law independence has not yet
been represented in the fact ledger. Row reduction, bit counts and verifier
cost must never be promoted into semantic-fact compression by arithmetic alone.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"GENERATION-ACCOUNTING=FAIL\n{message}")


def classify_selector_ledger_support(ledger: dict[str, Any]) -> dict[str, Any]:
    facts = ledger.get("facts", [])

    selector_facts = []
    for fact in facts:
        haystack = " ".join(
            str(fact.get(field, ""))
            for field in ("id", "claim", "domain", "witness", "provenance")
        ).lower()
        if "selector" in haystack or "car/cdr" in haystack or "car-cdr" in haystack:
            selector_facts.append(fact)

    semantic = [
        fact for fact in selector_facts
        if fact.get("accounting_class") == "semantic"
    ]
    proof = [
        fact for fact in selector_facts
        if fact.get("accounting_class") == "proof"
    ]

    # The current census may use CAR/CDR as a local generator basis while still
    # leaving their global independence UNKNOWN. A semantic compression claim
    # therefore requires an explicit atomic selector fact family in #2304.
    required_roles = {
        "selector-basis-car",
        "selector-basis-cdr",
        "selector-law-A",
        "selector-law-D",
        "selector-family-premise",
    }

    # We intentionally do not guess IDs. Presence is only informational until
    # the ledger grows explicit machine-readable role tags for this family.
    ready = False

    return {
        "selector_fact_rows_found": len(selector_facts),
        "selector_semantic_fact_rows_found": len(semantic),
        "selector_proof_fact_rows_found": len(proof),
        "required_roles": sorted(required_roles),
        "roles_machine_mapped": False,
        "independence_ready": ready,
        "reason": (
            "selector root/law independence is not yet machine-mapped in the "
            "#2304 ledger; semantic compression remains UNKNOWN"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--census",
        type=Path,
        default=Path("knowledge/function-status-census.json"),
    )
    ap.add_argument(
        "--ledger",
        type=Path,
        default=Path("benchmarks/generator-economy/semantic-fact-ledger.json"),
    )
    ap.add_argument("--ledger-summary", type=Path, required=True)
    ap.add_argument("--certificate-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    census = load_json(args.census)
    ledger = load_json(args.ledger)
    ledger_summary = load_json(args.ledger_summary)
    storage = read_tsv(args.certificate_dir / "storage-results.tsv")
    instructions = read_tsv(args.certificate_dir / "instruction-results.tsv")
    certificates = load_json(args.certificate_dir / "certificates.json")
    schema = load_json(args.certificate_dir / "schema.json")

    summary = census["summary"]
    rows = census["rows"]
    active_rows = int(summary["active_function_rows"])
    generated_rows = [row for row in rows if row["status"] == "generated"]
    unknown_rows = [row for row in rows if row["status"] == "UNKNOWN"]
    root_rows = [row for row in rows if row["status"] == "root"]
    residue_rows = [row for row in rows if row["status"] == "residue"]

    require(active_rows == len(rows), "census active row count mismatch")
    require(
        len(generated_rows) == int(summary["counts"]["generated"]),
        "generated row count mismatch",
    )
    require(
        len(unknown_rows) == int(summary["counts"]["UNKNOWN"]),
        "UNKNOWN row count mismatch",
    )

    # Current generated exact-width census should be the certified D4+D5 selector subset.
    generated_by_width = Counter(int(row["width"]) for row in generated_rows)
    require(
        set(generated_by_width) <= {4, 5},
        f"unexpected generated width outside current selector D4/D5 set: {generated_by_width}",
    )

    storage_by_width = {int(row["width"]): row for row in storage}
    flat_identity_bits = 0
    self_framed_certificate_bits = 0
    outer_framed_certificate_payload_bits = 0

    for width, count in sorted(generated_by_width.items()):
        require(width in storage_by_width, f"missing certificate storage row for D{width}")
        s = storage_by_width[width]
        require(int(s["count"]) >= count, f"certificate corpus too small for D{width}")
        flat_identity_bits += count * int(s["flat_identity_bits_each"])
        self_framed_certificate_bits += count * int(s["self_framed_cert_bits_each"])
        outer_framed_certificate_payload_bits += (
            count * int(s["externally_framed_cert_payload_bits_each"])
        )

    instruction_by_mode = {row["mode"]: row for row in instructions}
    for mode in ("flat", "replay", "verify"):
        require(mode in instruction_by_mode, f"missing certificate instruction mode {mode}")

    cert_index = {
        (int(cert["derived_result_width"]), int(cert["derived_result_bits"])): cert
        for cert in certificates
    }
    missing_certs = []
    current_cert_bits = 0
    for row in generated_rows:
        key = (int(row["width"]), int(row["function_identity"], 2))
        cert = cert_index.get(key)
        if cert is None:
            missing_certs.append(row["function_identity"])
            continue
        current_cert_bits += int(cert["packed_bit_len"])
    require(not missing_certs, f"current generated rows lack certificates: {missing_certs}")
    require(
        current_cert_bits == self_framed_certificate_bits,
        "certificate dump and storage table disagree",
    )

    ledger_support = classify_selector_ledger_support(ledger)

    # Proof/mechanism counts are taken from the validated #2304 summary, but we
    # do not pretend unrelated proof facts are selector proof costs.
    proof_fact_count_global = int(ledger_summary["proof_fact_count"])
    mechanism_fact_count_global = int(ledger_summary["mechanism_fact_count"])

    flat_row_model = {
        "active_coordinate_rows": active_rows,
        "generated_rows_treated_as_independent_rows": len(generated_rows),
        "unknown_rows": len(unknown_rows),
        "root_rows": len(root_rows),
        "residue_rows": len(residue_rows),
        "exact_generated_identity_bits": flat_identity_bits,
        "semantic_fact_count": None,
        "semantic_fact_status": (
            "UNKNOWN: active registry rows are not proven mutually independent semantic facts"
        ),
    }

    hybrid_model = {
        "active_coordinate_rows": active_rows,
        "generated_rows": len(generated_rows),
        "registry_rows_potentially_derivable": len(generated_rows),
        "unknown_rows_unchanged": len(unknown_rows),
        "root_rows_current_census": len(root_rows),
        "residue_rows_current_census": len(residue_rows),
        "self_framed_certificate_bits": self_framed_certificate_bits,
        "outer_framed_certificate_payload_bits": outer_framed_certificate_payload_bits,
        "flat_identity_bits_for_same_generated_rows": flat_identity_bits,
        "self_framed_vs_flat_bit_ratio": (
            self_framed_certificate_bits / flat_identity_bits
            if flat_identity_bits else None
        ),
        "outer_framed_vs_flat_bit_ratio": (
            outer_framed_certificate_payload_bits / flat_identity_bits
            if flat_identity_bits else None
        ),
        "certificate_replay_i_refs_per_generated_function": float(
            instruction_by_mode["replay"]["net_i_refs_per_operation"]
        ),
        "certificate_verify_i_refs_per_generated_function": float(
            instruction_by_mode["verify"]["net_i_refs_per_operation"]
        ),
        "flat_coordinate_read_i_refs_per_function": float(
            instruction_by_mode["flat"]["net_i_refs_per_operation"]
        ),
        "semantic_fact_count": None,
        "semantic_compression_status": (
            "UNKNOWN"
            if not ledger_support["independence_ready"]
            else "ready-for-ledger-accounting"
        ),
        "semantic_compression_reason": ledger_support["reason"],
    }

    hidden_instance_map_control = {
        "name": "one-hidden-instance-map-per-generated-row",
        "independent_instance_maps": len(generated_rows),
        "rows_eliminated": len(generated_rows),
        "semantic_fact_savings": 0,
        "status": "rejected-as-semantic-compression",
        "reason": (
            "renaming each explicit semantic row as an independent instance map "
            "does not reduce independent facts"
        ),
    }

    bundled_law_control = {
        "name": "selector-law-bundle-counted-as-one",
        "status": "rejected",
        "reason": (
            "#2304 anti-bundling requires atomic law rows and remove-one/derivability "
            "evidence; a theorem bundle cannot be counted as one independent fact by label"
        ),
    }

    certificate_economy_control = {
        "name": "certificate-storage-is-not-semantic-compression",
        "flat_identity_bits": flat_identity_bits,
        "self_framed_certificate_bits": self_framed_certificate_bits,
        "outer_framed_certificate_payload_bits": outer_framed_certificate_payload_bits,
        "self_framed_delta_bits": self_framed_certificate_bits - flat_identity_bits,
        "outer_framed_delta_bits": (
            outer_framed_certificate_payload_bits - flat_identity_bits
        ),
        "status": (
            "self-framed-certificates-are-larger-than-flat-identities"
            if self_framed_certificate_bits > flat_identity_bits
            else "self-framed-certificates-not-larger"
        ),
    }

    output = {
        "schema": "generation-accounting/v1",
        "authority": "research-only",
        "inputs": {
            "census": str(args.census),
            "ledger": str(args.ledger),
            "certificate_schema": schema.get("schema"),
        },
        "census": {
            "active_rows": active_rows,
            "generated_rows": len(generated_rows),
            "unknown_rows": len(unknown_rows),
            "root_rows": len(root_rows),
            "residue_rows": len(residue_rows),
            "generated_by_width": dict(sorted(generated_by_width.items())),
        },
        "flat_row_model": flat_row_model,
        "hybrid_generated_model": hybrid_model,
        "selector_ledger_support": ledger_support,
        "global_ledger_context": {
            "validated_models": [model["id"] for model in ledger_summary["models"]],
            "proof_fact_count": proof_fact_count_global,
            "mechanism_fact_count": mechanism_fact_count_global,
            "note": "global ledger counts are context, not charged wholesale to selector generation",
        },
        "negative_controls": [
            hidden_instance_map_control,
            bundled_law_control,
            certificate_economy_control,
        ],
        "non_conclusions": [
            "12 generated rows do not imply 12 independent semantic facts saved",
            "CAR/CDR generator-basis use does not prove global root independence",
            "certificate bit savings or overhead do not establish semantic compression",
            "verification instruction cost is mechanism cost, not semantic fact count",
            "UNKNOWN is visible and never silently counted as zero",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "accounting.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    table_rows = [
        {
            "metric": "active_rows",
            "flat": active_rows,
            "hybrid": active_rows,
            "unit": "coordinate rows",
        },
        {
            "metric": "generated_rows",
            "flat": 0,
            "hybrid": len(generated_rows),
            "unit": "rows",
        },
        {
            "metric": "independent_registry_rows_for_generated_subset",
            "flat": len(generated_rows),
            "hybrid": 0,
            "unit": "row-role proxy",
        },
        {
            "metric": "generated_subset_identity_bits",
            "flat": flat_identity_bits,
            "hybrid": self_framed_certificate_bits,
            "unit": "bits (self-framed cert comparison)",
        },
        {
            "metric": "generated_subset_outer_framed_payload_bits",
            "flat": flat_identity_bits,
            "hybrid": outer_framed_certificate_payload_bits,
            "unit": "bits",
        },
        {
            "metric": "semantic_fact_count",
            "flat": "UNKNOWN",
            "hybrid": "UNKNOWN",
            "unit": "independent semantic facts",
        },
    ]
    with (args.out / "accounting.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["metric", "flat", "hybrid", "unit"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(table_rows)

    flat_i = hybrid_model["flat_coordinate_read_i_refs_per_function"]
    replay_i = hybrid_model["certificate_replay_i_refs_per_generated_function"]
    verify_i = hybrid_model["certificate_verify_i_refs_per_generated_function"]

    report = [
        "# Exact-width generation accounting — #2370",
        "",
        "## Current census",
        "",
        f"- active D3+ rows: **{active_rows}**",
        f"- generated rows: **{len(generated_rows)}**",
        f"- UNKNOWN rows: **{len(unknown_rows)}**",
        f"- proven root rows in census: **{len(root_rows)}**",
        f"- bounded residue rows: **{len(residue_rows)}**",
        "",
        "## Current generated D4+D5 selector subset",
        "",
        f"- flat exact-coordinate bits: **{flat_identity_bits}**",
        f"- self-framed certificate bits: **{self_framed_certificate_bits}** "
        f"({self_framed_certificate_bits/flat_identity_bits:.3f}x flat)",
        f"- outer-framed certificate payload bits: **{outer_framed_certificate_payload_bits}** "
        f"({outer_framed_certificate_payload_bits/flat_identity_bits:.3f}x flat)",
        f"- flat coordinate-read control: **{flat_i:.3f} I refs/op**",
        f"- certificate replay: **{replay_i:.3f} I refs/op** ({replay_i/flat_i:.3f}x flat control)",
        f"- certificate verify: **{verify_i:.3f} I refs/op** ({verify_i/flat_i:.3f}x flat control)",
        "",
        "## Semantic compression verdict",
        "",
        "**UNKNOWN.**",
        "",
        ledger_support["reason"] + ".",
        "",
        "The current evidence proves that 12 registry rows are reconstructible and",
        "that their certificates replay exactly. It does not yet prove how many",
        "independent semantic facts the selector root/law model contains after",
        "typing premises and remove-one independence are charged.",
        "",
        "## Negative controls",
        "",
        f"- hidden instance-map model: **REJECTED** — {len(generated_rows)} independent maps "
        f"replace {len(generated_rows)} rows, saving zero semantic facts;",
        f"- bundled selector-law counted as one fact: **REJECTED** by #2304 anti-bundling;",
        f"- self-framed certificate storage: **{self_framed_certificate_bits-flat_identity_bits:+d} bits** "
        "versus flat identities, so certificate storage alone is not the win;",
        "",
        "Next unlock: add machine-readable selector basis/law/typing facts to #2304",
        "with explicit independence status. Then rerun this exact benchmark rather",
        "than changing the accounting rule.",
        "",
    ]
    (args.out / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print("GENERATION-ACCOUNTING=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
