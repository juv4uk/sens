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


def classify_selector_ledger_support(
    ledger: dict[str, Any],
    ledger_summary: dict[str, Any],
) -> dict[str, Any]:
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

    model_by_id = {
        model["id"]: model
        for model in ledger_summary.get("models", [])
    }
    flat = model_by_id.get("selector-flat-current")
    generated = model_by_id.get("selector-root-law-current")
    interval_ready = flat is not None and generated is not None

    if interval_ready:
        flat_interval = [
            int(flat["semantic_fact_lower_bound"]),
            int(flat["semantic_fact_upper_bound"]),
        ]
        generated_interval = [
            int(generated["semantic_fact_lower_bound"]),
            int(generated["semantic_fact_upper_bound"]),
        ]
        require(
            generated_interval[1] <= flat_interval[1],
            "selector generated-model upper bound exceeds flat-model upper bound",
        )
        reason = (
            "validated #2304 selector models narrow the independent-semantic-fact "
            "upper bound while leaving the lower bound unresolved"
        )
        upper_bound_reduction = flat_interval[1] - generated_interval[1]
        lower_bound_reduction = flat_interval[0] - generated_interval[0]
    else:
        flat_interval = None
        generated_interval = None
        upper_bound_reduction = None
        lower_bound_reduction = None
        reason = (
            "selector fact-ledger models are absent; semantic compression remains UNKNOWN"
        )

    return {
        "selector_fact_rows_found": len(selector_facts),
        "selector_semantic_fact_rows_found": len(semantic),
        "selector_proof_fact_rows_found": len(proof),
        "interval_ready": interval_ready,
        "flat_model_id": "selector-flat-current",
        "generated_model_id": "selector-root-law-current",
        "flat_semantic_fact_interval": flat_interval,
        "generated_semantic_fact_interval": generated_interval,
        "semantic_fact_upper_bound_reduction": upper_bound_reduction,
        "semantic_fact_lower_bound_reduction": lower_bound_reduction,
        "exact_minimality_proven": (
            interval_ready
            and flat_interval[0] == flat_interval[1]
            and generated_interval[0] == generated_interval[1]
        ),
        "reason": reason,
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

    ledger_support = classify_selector_ledger_support(ledger, ledger_summary)

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
        "selector_semantic_fact_interval": ledger_support[
            "flat_semantic_fact_interval"
        ],
        "semantic_fact_status": (
            "interval-only: active registry rows are not proven mutually independent semantic facts"
            if ledger_support["interval_ready"]
            else "UNKNOWN: selector fact-ledger models unavailable"
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
        "selector_semantic_fact_interval": ledger_support[
            "generated_semantic_fact_interval"
        ],
        "semantic_compression_status": (
            "bounded-upper-bound-narrowing"
            if ledger_support["interval_ready"]
            else "UNKNOWN"
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
            "metric": "selector_semantic_fact_lower_bound",
            "flat": (
                ledger_support["flat_semantic_fact_interval"][0]
                if ledger_support["interval_ready"]
                else "UNKNOWN"
            ),
            "hybrid": (
                ledger_support["generated_semantic_fact_interval"][0]
                if ledger_support["interval_ready"]
                else "UNKNOWN"
            ),
            "unit": "independent semantic facts",
        },
        {
            "metric": "selector_semantic_fact_upper_bound",
            "flat": (
                ledger_support["flat_semantic_fact_interval"][1]
                if ledger_support["interval_ready"]
                else "UNKNOWN"
            ),
            "hybrid": (
                ledger_support["generated_semantic_fact_interval"][1]
                if ledger_support["interval_ready"]
                else "UNKNOWN"
            ),
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

    if ledger_support["interval_ready"]:
        flat_interval = ledger_support["flat_semantic_fact_interval"]
        generated_interval = ledger_support["generated_semantic_fact_interval"]
        verdict_lines = [
            "## Semantic compression verdict",
            "",
            "**BOUNDED INTERVAL NARROWING.**",
            "",
            f"- flat selector model: **[{flat_interval[0]}, {flat_interval[1]}]** independent semantic facts;",
            f"- root+law selector model: **[{generated_interval[0]}, {generated_interval[1]}]**;",
            f"- upper bound narrows by **{ledger_support['semantic_fact_upper_bound_reduction']}**;",
            f"- lower bound changes by **{ledger_support['semantic_fact_lower_bound_reduction']}**;",
            "",
            "This is not a proof that the root+law model contains exactly five independent facts.",
            "The lower bound remains zero because CAR/CDR, selector-family premises and",
            "extend-A/extend-D law necessity have not yet passed remove-one/minimality proofs.",
            "",
            "What is proved here is narrower: 12 current descendants are reconstructible,",
            "so they no longer need to remain in the model's independent-UNKNOWN upper-bound bucket.",
            "",
        ]
    else:
        verdict_lines = [
            "## Semantic compression verdict",
            "",
            "**UNKNOWN.**",
            "",
            ledger_support["reason"] + ".",
            "",
            "The current evidence proves that 12 registry rows are reconstructible and",
            "that their certificates replay exactly. It does not yet provide a",
            "machine-validated semantic-fact interval for the selector family.",
            "",
        ]

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
        *verdict_lines,
        "## Negative controls",
        "",
        f"- hidden instance-map model: **REJECTED** — {len(generated_rows)} independent maps "
        f"replace {len(generated_rows)} rows, saving zero semantic facts;",
        f"- bundled selector-law counted as one fact: **REJECTED** by #2304 anti-bundling;",
        f"- self-framed certificate storage: **{self_framed_certificate_bits-flat_identity_bits:+d} bits** "
        "versus flat identities, so certificate storage alone is not the win;",
        "",
        "Next unlock: run remove-one/root-minimality attacks on selector basis/law/premise",
        "facts to raise the lower bounds or tighten the upper bounds. Keep this accounting",
        "rule unchanged while the evidence improves.",
        "",
    ]
    (args.out / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print("GENERATION-ACCOUNTING=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
