#!/usr/bin/env python3
"""#2422 exact D6 closure map from admitted selector evidence.

Research-only. This script classifies D6 conservatively:
- selector-law closure is generated evidence;
- every other coordinate remains UNKNOWN/free;
- no row becomes Core-admissible without separate owner ratification.

Hardening:
- cross-check generated coordinates against merged #2329;
- replay #2345 selector certificates for every generated D6 row;
- consume #2304/#2385 selector semantic-fact accounting without treating
  UNKNOWN as zero.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import runpy
from itertools import product
from pathlib import Path
from typing import Any

WIDTH = 6
ROOTS = {
    "101": {"root_name": "CAR", "root_choice": 0, "selector_letter": "A"},
    "110": {"root_name": "CDR", "root_choice": 1, "selector_letter": "D"},
}
LAW_BITS = {
    "0": {"law_id": "sel.law.extend-a", "display": "compose-first-projection", "letter": "A"},
    "1": {"law_id": "sel.law.extend-d", "display": "compose-rest-projection", "letter": "D"},
}

REPO = Path(__file__).resolve().parents[2]
FORECAST = REPO / "scripts/research-2322-generative-domain-forecast.py"
LEDGER = REPO / "benchmarks/generator-economy/semantic-fact-ledger.json"


def load_forecast_words() -> set[str]:
    namespace = runpy.run_path(str(FORECAST))
    selector_words = namespace["selector_words"]
    words = set(selector_words(WIDTH))
    if len(words) != 16:
        raise AssertionError(f"#2329 forecast expected 16 D6 selectors, got {len(words)}")
    return words


def load_selector_fact_interval() -> list[int]:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    matches = [m for m in data["models"] if m["id"] == "selector-root-law-current"]
    if len(matches) != 1:
        raise AssertionError("expected exactly one selector-root-law-current ledger model")
    interval = matches[0]["expected_semantic_fact_interval"]
    if interval != [0, 5]:
        raise AssertionError(f"selector ledger interval drifted: {interval}")
    return interval


def encode_certificate(root_choice: int, suffix: str) -> dict[str, Any]:
    depth = len(suffix)
    if root_choice not in (0, 1) or not (0 <= depth <= 5):
        raise ValueError("invalid selector certificate root/depth")
    path = int(suffix, 2) if suffix else 0
    if path >= (1 << depth):
        raise ValueError("selector certificate path does not fit depth")
    bit_len = 4 + depth
    payload = (root_choice << (depth + 3)) | (depth << depth) | path
    return {
        "schema": "selector-generation-certificate/v1",
        "root_choice": root_choice,
        "depth": depth,
        "path_bits": suffix,
        "path_value": path,
        "payload": payload,
        "bit_len": bit_len,
    }


def decode_certificate(cert: dict[str, Any]) -> str:
    bit_len = int(cert["bit_len"])
    payload = int(cert["payload"])
    if not 4 <= bit_len <= 9:
        raise ValueError("certificate bit_len outside #2345 schema")
    depth = bit_len - 4
    if payload & ~((1 << bit_len) - 1):
        raise ValueError("certificate has payload bits above exact bit_len")
    encoded_depth = (payload >> depth) & 0b111
    if encoded_depth != depth:
        raise ValueError("certificate encoded depth mismatch")
    root_choice = (payload >> (depth + 3)) & 1
    path = payload & ((1 << depth) - 1 if depth else 0)
    root = "101" if root_choice == 0 else "110"
    suffix = format(path, f"0{depth}b") if depth else ""
    return root + suffix


def selector_display_name(root_bits: str, suffix: str) -> str:
    letters = ROOTS[root_bits]["selector_letter"] + "".join(LAW_BITS[b]["letter"] for b in suffix)
    return "C" + letters + "R"


def selector_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    suffix_width = WIDTH - 3
    for root_bits, meta in ROOTS.items():
        for suffix_tuple in product("01", repeat=suffix_width):
            suffix = "".join(suffix_tuple)
            coordinate = root_bits + suffix
            cert = encode_certificate(int(meta["root_choice"]), suffix)
            replayed = decode_certificate(cert)
            if replayed != coordinate:
                raise AssertionError(f"#2345 certificate replay drift: {coordinate} -> {replayed}")

            rows[coordinate] = {
                "coordinate": coordinate,
                "width": WIDTH,
                "display_name": selector_display_name(root_bits, suffix),
                "display_name_authority": False,
                "semantic_family": "selector",
                "status": "generated",
                "root_basis": root_bits,
                "root_name": meta["root_name"],
                "law_path": [LAW_BITS[bit]["law_id"] for bit in suffix],
                "law_steps_display": [LAW_BITS[bit]["display"] for bit in suffix],
                "canonical_coordinate_path_bits": suffix,
                "semantic_law": "selector projection composition",
                "semantic_law_authority": "#2158",
                "coordinate_realization": "root_bits || canonical_path_bits",
                "coordinate_realization_authority": "#2329/#2366",
                "certificate_ref": "#2323/#2345",
                "certificate": cert,
                "certificate_replay_ok": True,
                "collision": False,
                "core_closure": True,
                "core_admissible": False,
                "admission_reason": "requires separate D6 owner ratification via #2414",
                "research_overlay_refs": [],
            }
    return rows


def build_map() -> list[dict[str, Any]]:
    generated = selector_rows()
    forecast_words = load_forecast_words()
    if set(generated) != forecast_words:
        raise AssertionError(
            "D6 closure disagrees with merged #2329 forecast: "
            f"local-only={sorted(set(generated)-forecast_words)} "
            f"forecast-only={sorted(forecast_words-set(generated))}"
        )

    rows: list[dict[str, Any]] = []
    for n in range(1 << WIDTH):
        coordinate = format(n, f"0{WIDTH}b")
        if coordinate in generated:
            row = generated[coordinate]
        else:
            row = {
                "coordinate": coordinate,
                "width": WIDTH,
                "display_name": "",
                "display_name_authority": False,
                "semantic_family": "",
                "status": "UNKNOWN/free",
                "root_basis": "",
                "root_name": "",
                "law_path": [],
                "law_steps_display": [],
                "canonical_coordinate_path_bits": "",
                "semantic_law": "",
                "semantic_law_authority": "",
                "coordinate_realization": "",
                "coordinate_realization_authority": "",
                "certificate_ref": "",
                "certificate": None,
                "certificate_replay_ok": False,
                "collision": False,
                "core_closure": False,
                "core_admissible": False,
                "admission_reason": "no admitted Core root/law evidence for this coordinate",
                "research_overlay_refs": [],
            }
        rows.append(row)

    if len(rows) != 64 or len({r["coordinate"] for r in rows}) != 64:
        raise AssertionError("D6 map must contain every exact coordinate exactly once")
    if sum(r["status"] == "generated" for r in rows) != 16:
        raise AssertionError("D6 selector closure must contain exactly 16 generated coordinates")
    if sum(r["status"] == "UNKNOWN/free" for r in rows) != 48:
        raise AssertionError("D6 must conservatively retain exactly 48 UNKNOWN/free coordinates")
    if any(r["collision"] for r in rows):
        raise AssertionError("D6 closure collision detected")
    if any(r["core_admissible"] for r in rows):
        raise AssertionError("#2422 is evidence-only; no D6 row may be admitted by this map")
    return rows


def accounting(rows: list[dict[str, Any]]) -> dict[str, Any]:
    generated = sum(r["status"] == "generated" for r in rows)
    depth = WIDTH - 3
    flat_each = WIDTH
    self_framed_each = 4 + depth
    outer_framed_each = 1 + depth

    def totals(bits_each: int) -> dict[str, int]:
        total_bits = generated * bits_each
        return {
            "bits_each": bits_each,
            "bits_total": total_bits,
            "bytes_ceil_total": math.ceil(total_bits / 8),
        }

    return {
        "generated_coordinate_count": generated,
        "flat_exact_coordinate": totals(flat_each),
        "self_framed_selector_certificate": totals(self_framed_each),
        "outer_framed_certificate_payload": totals(outer_framed_each),
        "semantic_fact_model": "selector-root-law-current",
        "shared_basis_semantic_fact_interval": load_selector_fact_interval(),
        "new_d6_generated_rows_charged_as_independent_facts": 0,
        "semantic_accounting_note": (
            "D6 descendants are derived in the declared selector root+law model; "
            "the shared basis itself remains independence-UNKNOWN within [0,5]."
        ),
        "no_scalar_winner": True,
    }


def report(rows: list[dict[str, Any]], acct: dict[str, Any]) -> str:
    generated = [r for r in rows if r["status"] == "generated"]
    unknown = [r for r in rows if r["status"] == "UNKNOWN/free"]
    lines = [
        "# D6 closure map — #2422",
        "",
        "This is a closure/proof map, not an allocation table.",
        "",
        "| class | count |",
        "|---|---:|",
        f"| exact D6 coordinates | {len(rows)} |",
        f"| selector-law generated | {len(generated)} |",
        f"| UNKNOWN/free | {len(unknown)} |",
        f"| collisions | {sum(bool(r['collision']) for r in rows)} |",
        f"| core-admissible before owner ratification | {sum(bool(r['core_admissible']) for r in rows)} |",
        "",
        "Cross-checks:",
        "- generated set equals merged #2329 D6 forecast;",
        "- every generated row replays through #2345 selector certificate encoding;",
        "- semantic selector composition (#2158) is separated from canonical bit realization (#2366).",
        "",
        "Proof/storage accounting:",
        f"- flat exact identities: {acct['flat_exact_coordinate']['bits_total']} bits / "
        f"{acct['flat_exact_coordinate']['bytes_ceil_total']} bytes;",
        f"- self-framed certificates: {acct['self_framed_selector_certificate']['bits_total']} bits / "
        f"{acct['self_framed_selector_certificate']['bytes_ceil_total']} bytes;",
        f"- outer-framed certificate payloads: {acct['outer_framed_certificate_payload']['bits_total']} bits / "
        f"{acct['outer_framed_certificate_payload']['bytes_ceil_total']} bytes;",
        f"- shared selector semantic-fact basis interval: "
        f"{acct['shared_basis_semantic_fact_interval']} from #2304/#2385;",
        "- generated D6 rows add zero independent per-coordinate facts in that declared root+law model.",
        "",
        "NON-CONCLUSIONS:",
        "- UNKNOWN/free is not residue and not an allocation invitation;",
        "- certificate storage is not semantic compression;",
        "- the [0,5] basis interval does not claim global selector minimality;",
        "- Core-Math hypotheses cannot change Core closure status;",
        "- no D6 coordinate becomes Core-admissible without separate #2414 owner ratification.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(out: Path, rows: list[dict[str, Any]], acct: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "d6-closure-map/v2",
        "authority": "research-only",
        "width": WIDTH,
        "capacity": 1 << WIDTH,
        "provenance": {
            "core_authority": "#2410",
            "ratified_selector_law": "#2158",
            "forecast": "#2322/#2329",
            "generation_certificates": "#2323/#2345",
            "anti_numerology": "#2366",
            "semantic_fact_ledger": "#2304/#2385",
            "closeout_parent": "#2414",
        },
        "core_math_overlay_policy": "separate overlay only; never mutates Core status",
        "counts": {
            "generated": 16,
            "ratified-root": 0,
            "ratified-residue": 0,
            "UNKNOWN/free": 48,
            "collisions": 0,
            "core-admissible": 0,
        },
        "accounting": acct,
        "rows": rows,
    }
    (out / "d6-closure-map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fields = [
        "coordinate", "width", "display_name", "semantic_family", "status",
        "root_basis", "root_name", "law_path", "canonical_coordinate_path_bits",
        "semantic_law", "semantic_law_authority", "coordinate_realization",
        "coordinate_realization_authority", "certificate_ref",
        "certificate_replay_ok", "collision", "core_closure", "core_admissible",
        "admission_reason", "research_overlay_refs",
    ]
    with (out / "d6-closure-map.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: (
                    "|".join(row[key]) if isinstance(row.get(key), list)
                    else row.get(key, "")
                )
                for key in fields
            })

    (out / "accounting.json").write_text(
        json.dumps(acct, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "report.md").write_text(report(rows, acct), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rows = build_map()
    acct = accounting(rows)
    write_outputs(args.out, rows, acct)
    print(report(rows, acct))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
