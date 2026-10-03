#!/usr/bin/env python3
"""#2505 exact D5 closure map after owner ratification of the domain.

The D5 domain is ratified. Occupancy is not.

This map:
- enumerates all 32 exact D5 coordinates;
- replays only selector-law descendants already implied by admitted roots/law;
- leaves every other coordinate UNKNOWN/free;
- does not pre-place SETQ, RETURN, macro/transformer, or Core-Math objects.

Research/closeout artifact; no production allocation is performed here.
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

WIDTH = 5
ROOTS = {
    "101": {"root_name": "CAR", "root_choice": 0, "selector_letter": "A"},
    "110": {"root_name": "CDR", "root_choice": 1, "selector_letter": "D"},
}
LAW_BITS = {
    "0": {"law_id": "sel.law.extend-a", "display": "compose-first-projection", "letter": "A"},
    "1": {"law_id": "sel.law.extend-d", "display": "compose-rest-projection", "letter": "D"},
}

REPO = Path(__file__).resolve().parents[2]
FORECAST = REPO / "scripts" / "research-2322-generative-domain-forecast.py"
LEDGER = REPO / "benchmarks" / "generator-economy" / "semantic-fact-ledger.json"


def load_forecast_words() -> set[str]:
    namespace = runpy.run_path(str(FORECAST))
    selector_words = namespace["selector_words"]
    words = set(selector_words(WIDTH))
    if len(words) != 8:
        raise AssertionError(f"#2329 forecast expected 8 D5 selectors, got {len(words)}")
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
        raise ValueError("certificate payload above exact bit_len")
    encoded_depth = (payload >> depth) & 0b111
    if encoded_depth != depth:
        raise ValueError("certificate depth mismatch")
    root_choice = (payload >> (depth + 3)) & 1
    path = payload & ((1 << depth) - 1 if depth else 0)
    root = "101" if root_choice == 0 else "110"
    suffix = format(path, f"0{depth}b") if depth else ""
    return root + suffix


def selector_display_name(root_bits: str, suffix: str) -> str:
    letters = ROOTS[root_bits]["selector_letter"] + "".join(
        LAW_BITS[b]["letter"] for b in suffix
    )
    return "C" + letters + "R"


def selector_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    suffix_width = WIDTH - 3
    for root_bits, meta in ROOTS.items():
        for suffix_tuple in product("01", repeat=suffix_width):
            suffix = "".join(suffix_tuple)
            coordinate = root_bits + suffix
            cert = encode_certificate(int(meta["root_choice"]), suffix)
            if decode_certificate(cert) != coordinate:
                raise AssertionError(f"certificate replay drift: {coordinate}")

            rows[coordinate] = {
                "coordinate": coordinate,
                "width": WIDTH,
                "domain": "D5",
                "domain_ratified": True,
                "display_name": selector_display_name(root_bits, suffix),
                "display_name_authority": False,
                "semantic_family": "selector",
                "status": "generated",
                "root_basis": root_bits,
                "root_name": meta["root_name"],
                "law_path": [LAW_BITS[bit]["law_id"] for bit in suffix],
                "canonical_coordinate_path_bits": suffix,
                "semantic_law": "selector projection composition",
                "semantic_law_authority": "#2158",
                "coordinate_realization": "root_bits || canonical_path_bits",
                "coordinate_realization_authority": "#2329/#2366",
                "certificate_ref": "#2323/#2345",
                "certificate": cert,
                "certificate_replay_ok": True,
                "collision": False,
                "semantic_member_of_ratified_domain": True,
                "manual_resident_required": False,
                "placement_ref": "",
                "research_overlay_refs": [],
            }
    return rows


def unknown_row(coordinate: str) -> dict[str, Any]:
    return {
        "coordinate": coordinate,
        "width": WIDTH,
        "domain": "D5",
        "domain_ratified": True,
        "display_name": "",
        "display_name_authority": False,
        "semantic_family": "",
        "status": "UNKNOWN/free",
        "root_basis": "",
        "root_name": "",
        "law_path": [],
        "canonical_coordinate_path_bits": "",
        "semantic_law": "",
        "semantic_law_authority": "",
        "coordinate_realization": "",
        "coordinate_realization_authority": "",
        "certificate_ref": "",
        "certificate": None,
        "certificate_replay_ok": False,
        "collision": False,
        "semantic_member_of_ratified_domain": False,
        "manual_resident_required": False,
        "placement_ref": "",
        "research_overlay_refs": [],
    }


def post_d4_exclusion_metadata() -> dict[str, dict[str, str]]:
    return {
        "SET-SETQ": {
            "decision": "d5-ineligible-shared-location-family",
            "reason": (
                "shared-location behavior survives only with explicit carrier/policy "
                "structure; DEFINE->SETQ requires two independent local refinements"
            ),
            "evidence": "#2492/#2498/#2518/#2616/#2617/#2705",
        },
        "RETURN": {
            "decision": "d5-ineligible-proven-root-domain-unresolved",
            "reason": (
                "non-local-exit is a proven parentless root; no same-base D4 parent "
                "exists and roothood/free capacity do not select D5"
            ),
            "evidence": "#2488/#2504/#2616/#2662/#2705",
        },
        "FEXPR-FSUBR": {
            "decision": "d5-ineligible-carrier-family",
            "reason": (
                "raw-form input and explicit caller-env are separable carrier facts; "
                "the historical protocol has no exact one-delta D4 parent theorem"
            ),
            "evidence": "#2522/#2530/#2616/#2617/#2705",
        },
        "TRANSFORMER": {
            "decision": "d5-ineligible-policy-over-carrier",
            "reason": (
                "current transformer behavior spans raw-form carrier plus returned-form "
                "and timing policy factors; the LAMBDA comparison is multi-delta"
            ),
            "evidence": "#2522/#2567/#2591/#2616/#2617/#2705",
        },
    }


def build_map() -> list[dict[str, Any]]:
    generated = selector_rows()
    forecast_words = load_forecast_words()
    if set(generated) != forecast_words:
        raise AssertionError(
            "D5 selector closure disagrees with merged forecast: "
            f"local-only={sorted(set(generated)-forecast_words)} "
            f"forecast-only={sorted(forecast_words-set(generated))}"
        )

    rows: list[dict[str, Any]] = []
    for n in range(1 << WIDTH):
        coordinate = format(n, f"0{WIDTH}b")
        rows.append(generated.get(coordinate, unknown_row(coordinate)))

    if len(rows) != 32 or len({r["coordinate"] for r in rows}) != 32:
        raise AssertionError("D5 map must contain every coordinate exactly once")
    if sum(r["status"] == "generated" for r in rows) != 8:
        raise AssertionError("D5 selector closure must contain exactly 8 rows")
    if sum(r["status"] == "UNKNOWN/free" for r in rows) != 24:
        raise AssertionError("D5 must retain exactly 24 UNKNOWN/free rows")
    if any(r["collision"] for r in rows):
        raise AssertionError("D5 closure collision detected")

    # Explicit anti-preallocation guards for current open capability candidates.
    if any(r["placement_ref"] for r in rows):
        raise AssertionError("SETQ/RETURN/etc. must not be pre-placed by closure map")
    if any(r["manual_resident_required"] for r in rows):
        raise AssertionError("selector generation must not become manual occupancy")

    # Completed post-D4 closeout is explanatory metadata only. These capabilities
    # must never gain D5 placement authority through the closure-map artifact.
    expected_post_d4_nonselector_ids = {
        "SET-SETQ",
        "RETURN",
        "FEXPR-FSUBR",
        "TRANSFORMER",
    }
    if expected_post_d4_nonselector_ids != set(post_d4_exclusion_metadata()):
        raise AssertionError("post-D4 D5 exclusion metadata drifted")

    return rows


def accounting(rows: list[dict[str, Any]]) -> dict[str, Any]:
    generated = sum(r["status"] == "generated" for r in rows)
    depth = WIDTH - 3

    def totals(bits_each: int) -> dict[str, int]:
        total_bits = generated * bits_each
        return {
            "bits_each": bits_each,
            "bits_total": total_bits,
            "bytes_ceil_total": math.ceil(total_bits / 8),
        }

    return {
        "domain_ratified": True,
        "generated_coordinate_count": generated,
        "unknown_free_count": 32 - generated,
        "flat_exact_coordinate": totals(WIDTH),
        "self_framed_selector_certificate": totals(4 + depth),
        "outer_framed_certificate_payload": totals(1 + depth),
        "semantic_fact_model": "selector-root-law-current",
        "shared_basis_semantic_fact_interval": load_selector_fact_interval(),
        "new_d5_generated_rows_charged_as_independent_facts": 0,
        "excluded_or_unplaced_nonselector_capabilities": post_d4_exclusion_metadata(),
        "no_scalar_winner": True,
    }


def report(rows: list[dict[str, Any]], acct: dict[str, Any]) -> str:
    generated = sum(r["status"] == "generated" for r in rows)
    unknown = sum(r["status"] == "UNKNOWN/free" for r in rows)
    return "\n".join([
        "# D5 closure map — #2505",
        "",
        "Owner status: D5 domain is RATIFIED. Occupancy remains law-driven.",
        "",
        "| class | count |",
        "|---|---:|",
        "| exact D5 coordinates | 32 |",
        f"| selector-law generated | {generated} |",
        f"| UNKNOWN/free | {unknown} |",
        "| manually pre-placed SETQ/RETURN | 0 |",
        "| collisions | 0 |",
        "",
        "Rules:",
        "- generated selector rows are semantic consequences of #2158;",
        "- append-bit realization is canonical-coordinate evidence, not the semantic law;",
        "- UNKNOWN/free is legitimate inside a ratified domain;",
        "- SET/SETQ, RETURN, FEXPR/FSUBR and TRANSFORMER are D5-NO under #2616/#2617/#2705;",
        "- Core-Math cannot fill D5 by analogy.",
        "",
        "Accounting:",
        f"- flat generated coordinates: {acct['flat_exact_coordinate']['bits_total']} bits;",
        f"- self-framed selector certificates: {acct['self_framed_selector_certificate']['bits_total']} bits;",
        f"- outer-framed certificate payloads: {acct['outer_framed_certificate_payload']['bits_total']} bits;",
        f"- selector shared-basis semantic-fact interval: {acct['shared_basis_semantic_fact_interval']}.",
        "",
    ])


def write_outputs(out: Path, rows: list[dict[str, Any]], acct: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "d5-closure-map/v1",
        "authority": "core-closeout-evidence",
        "domain": "D5",
        "domain_ratified": True,
        "width": WIDTH,
        "capacity": 1 << WIDTH,
        "provenance": {
            "owner_domain_ratification": "#2414/#2490",
            "selector_law": "#2158",
            "forecast": "#2322/#2329",
            "generation_certificates": "#2323/#2345",
            "coordinate_classification": "#2366",
            "fact_ledger": "#2304/#2385",
            "placement_law": "#2236",
            "post_d4_d5_closeout": "#2616/#2617/#2705",
            "shared_location_carrier": "#2617/#2705",
            "return_residue_root": "#2488/#2617/#2705",
            "special_call_protocol": "#2522/#2616/#2705",
            "transformer_closeout": "#2616/#2617/#2705",
        },
        "counts": {
            "generated": 8,
            "ratified-root": 0,
            "ratified-residue": 0,
            "UNKNOWN/free": 24,
            "collisions": 0,
        },
        "accounting": acct,
        "rows": rows,
    }
    (out / "d5-closure-map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fields = [
        "coordinate", "width", "domain", "domain_ratified", "display_name",
        "semantic_family", "status", "root_basis", "root_name", "law_path",
        "canonical_coordinate_path_bits", "semantic_law", "semantic_law_authority",
        "coordinate_realization", "coordinate_realization_authority",
        "certificate_ref", "certificate_replay_ok", "collision",
        "semantic_member_of_ratified_domain", "manual_resident_required",
        "placement_ref", "research_overlay_refs",
    ]
    with (out / "d5-closure-map.tsv").open("w", newline="", encoding="utf-8") as fh:
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
