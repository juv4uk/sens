#!/usr/bin/env python3
"""#2422 exact D6 closure map after owner ratification of the domain.

The D6 domain is ratified. Occupancy is not.

This script classifies D6 conservatively:
- selector-law closure is generated evidence inside the ratified domain;
- every other coordinate remains UNKNOWN/free;
- no non-selector resident is pre-placed by this map.

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
    "100": {"root_name": "CAR", "root_choice": 0, "selector_letter": "A"},
    "011": {"root_name": "CDR", "root_choice": 1, "selector_letter": "D"},
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


def load_ratified_residents() -> dict[str, str]:
    """Load the current owner-ratified D6 coordinate map, not the old OD-006 table."""
    path = REPO / "knowledge" / "d6-ratified.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "d6-ratified/v1":
        raise AssertionError("current D6 authority schema mismatch")
    if data.get("status") != "owner-ratified" or data.get("authority") != "#3393":
        raise AssertionError("current D6 map is not the #3393 owner-ratified authority")
    if data.get("width") != WIDTH or data.get("capacity") != 64:
        raise AssertionError("current D6 map has the wrong exact domain")
    if data.get("occupancy") != 64 or data.get("distinct_residents") != 64:
        raise AssertionError("current D6 map must remain dense 64/64")
    residents = data.get("residents")
    expected = {format(n, "06b") for n in range(1 << WIDTH)}
    if not isinstance(residents, dict) or set(residents) != expected:
        raise AssertionError("current D6 resident coordinates must be exactly 000000..111111")
    if len(set(residents.values())) != 64:
        raise AssertionError("current D6 resident projections must be unique")
    return {str(coordinate): str(name) for coordinate, name in residents.items()}


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
    root = "100" if root_choice == 0 else "011"
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
                "domain": "D6",
                "domain_ratified": True,
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
                "semantic_member_of_ratified_domain": True,
                "manual_resident_required": False,
                "placement_ref": "",
                "research_overlay_refs": [],
            }
    return rows


def build_map() -> list[dict[str, Any]]:
    generated = selector_rows()
    forecast_words = load_forecast_words()
    if set(generated) != forecast_words:
        raise AssertionError(
            "Current D6 selector closure disagrees with #2329 forecast: "
            f"local-only={sorted(set(generated)-forecast_words)} "
            f"forecast-only={sorted(forecast_words-set(generated))}"
        )

    residents = load_ratified_residents()
    for coordinate, row in generated.items():
        if residents.get(coordinate) != row["display_name"]:
            raise AssertionError(
                f"selector proof disagrees with owner-ratified #3393 resident "
                f"at {coordinate}: generated={row['display_name']!r}, "
                f"ratified={residents.get(coordinate)!r}"
            )

    rows: list[dict[str, Any]] = []
    for n in range(1 << WIDTH):
        coordinate = format(n, f"0{WIDTH}b")
        if coordinate in generated:
            row = dict(generated[coordinate])
            row["resident"] = residents[coordinate]
            row["resident_authority"] = "#3393"
            row["semantic_member_of_ratified_domain"] = True
        else:
            row = {
                "coordinate": coordinate,
                "width": WIDTH,
                "domain": "D6",
                "domain_ratified": True,
                "resident": residents[coordinate],
                "resident_authority": "#3393",
                "display_name": residents[coordinate],
                "display_name_authority": False,
                "semantic_family": "owner-ratified-other-resident",
                "status": "owner-ratified-other-resident",
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
                "semantic_member_of_ratified_domain": True,
                "manual_resident_required": False,
                "placement_ref": "",
                "research_overlay_refs": [],
            }
        rows.append(row)

    if len(rows) != 64 or {r["coordinate"] for r in rows} != {
        format(n, "06b") for n in range(64)
    }:
        raise AssertionError("current D6 map must cover each exact coordinate once")
    if len({r["resident"] for r in rows}) != 64:
        raise AssertionError("current D6 map must preserve 64 distinct residents")
    if sum(r["status"] == "generated" for r in rows) != 16:
        raise AssertionError("current selector-law closure must contain 16 coordinates")
    if sum(r["status"] == "owner-ratified-other-resident" for r in rows) != 48:
        raise AssertionError("the other 48 coordinates must remain owner-ratified residents")
    if sum(r["status"] == "UNKNOWN/free" for r in rows) != 0:
        raise AssertionError("current owner-ratified D6 has no UNKNOWN/free coordinates")
    if not all(r["semantic_member_of_ratified_domain"] for r in rows):
        raise AssertionError("all current D6 coordinates must be ratified members")
    if any(r["collision"] for r in rows):
        raise AssertionError("D6 closure collision detected")
    if any(r["manual_resident_required"] for r in rows):
        raise AssertionError("current D6 map must not invent manual placements")
    if any(r["placement_ref"] for r in rows):
        raise AssertionError("current residency comes from #3393, not research placement refs")
    return rows


def accounting(rows: list[dict[str, Any]]) -> dict[str, Any]:
    generated = sum(r["status"] == "generated" for r in rows)
    other_residents = sum(r["status"] == "owner-ratified-other-resident" for r in rows)
    unknown_free = sum(r["status"] == "UNKNOWN/free" for r in rows)
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
        "domain_ratified": True,
        "current_residency_authority": "knowledge/d6-ratified.json (#3393)",
        "current_resident_count": len(rows),
        "generated_coordinate_count": generated,
        "other_owner_ratified_resident_count": other_residents,
        "unknown_free_count": unknown_free,
        "flat_exact_coordinate": totals(flat_each),
        "self_framed_selector_certificate": totals(self_framed_each),
        "outer_framed_certificate_payload": totals(outer_framed_each),
        "semantic_fact_model": "selector-root-law-current",
        "shared_basis_semantic_fact_interval": load_selector_fact_interval(),
        "new_d6_generated_rows_charged_as_independent_facts": 0,
        "semantic_accounting_note": (
            "The 16 selectors are a derived subfamily within the already "
            "owner-ratified 64/64 D6 map; this proof creates no new residents."
        ),
        "no_scalar_winner": True,
    }


def report(rows: list[dict[str, Any]], acct: dict[str, Any]) -> str:
    generated = [r for r in rows if r["status"] == "generated"]
    other = [r for r in rows if r["status"] == "owner-ratified-other-resident"]
    unknown = [r for r in rows if r["status"] == "UNKNOWN/free"]
    lines = [
        "# D6 selector closure against current owner-ratified map — #3393",
        "",
        "Current authority: D6 is owner-ratified dense 64/64 under #3393 / Contract 11.8.",
        "This report separates 16 selector-law-derived rows from the other 48 residents;",
        "neither category changes the existing ratified coordinate map.",
        "",
        "| class | count |",
        "|---|---:|",
        f"| exact D6 coordinates | {len(rows)} |",
        f"| selector-law generated (current resident) | {len(generated)} |",
        f"| other owner-ratified residents | {len(other)} |",
        f"| UNKNOWN/free coordinates | {len(unknown)} |",
        f"| collisions | {sum(bool(r['collision']) for r in rows)} |",
        f"| semantic members of ratified D6 | {sum(bool(r['semantic_member_of_ratified_domain']) for r in rows)} |",
        "",
        "Cross-checks:",
        "- generated selector set equals the current #2329 D6 forecast (roots 011 and 100);",
        "- generated names/coordinates match knowledge/d6-ratified.json under #3393;",
        "- every generated row replays through #2345 selector certificate encoding;",
        "- the other 48 coordinates keep their existing #3393 residents; none are marked free.",
        "",
        "Proof/storage accounting for the derived 16-selector subfamily:",
        f"- flat exact identities: {acct['flat_exact_coordinate']['bits_total']} bits / "
        f"{acct['flat_exact_coordinate']['bytes_ceil_total']} bytes;",
        f"- self-framed certificates: {acct['self_framed_selector_certificate']['bits_total']} bits / "
        f"{acct['self_framed_selector_certificate']['bytes_ceil_total']} bytes;",
        f"- outer-framed certificate payloads: {acct['outer_framed_certificate_payload']['bits_total']} bits / "
        f"{acct['outer_framed_certificate_payload']['bytes_ceil_total']} bytes;",
        f"- shared selector semantic-fact basis interval: "
        f"{acct['shared_basis_semantic_fact_interval']} from #2304/#2385;",
        "- generated D6 selector rows add zero independent per-coordinate facts.",
        "",
        "NON-CONCLUSIONS:",
        "- selector derivation does not create or move an owner-ratified resident;",
        "- current D6 has no UNKNOWN/free coordinate under #3393;",
        "- certificate storage is not semantic compression;",
        "- the [0,5] basis interval does not claim global selector minimality;",
        "- ratified residency does not imply runtime callability.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(out: Path, rows: list[dict[str, Any]], acct: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "d6-closure-map/v4",
        "authority": "current-owner-ratified-d6-with-selector-closure",
        "domain": "D6",
        "domain_ratified": True,
        "current_occupancy_authority": "knowledge/d6-ratified.json (#3393)",
        "width": WIDTH,
        "capacity": 1 << WIDTH,
        "provenance": {
            "owner_domain_ratification": "#3393 / Contract 11.8",
            "ratified_map": "knowledge/d6-ratified.json",
            "ratified_selector_law": "#2158",
            "current_forecast": "#2322/#2329",
            "generation_certificates": "#2323/#2345",
            "semantic_fact_ledger": "#2304/#2385",
            "historical_sparse_frontier": "benchmarks/d6-unknown-frontier/pre-od006-closure.py (PRE-OD006 only)",
        },
        "core_math_overlay_policy": "separate overlay only; never mutates Core residency",
        "counts": {
            "generated_selectors": 16,
            "other_owner_ratified_residents": 48,
            "unknown_free": 0,
            "resident_count": 64,
            "collisions": 0,
        },
        "accounting": acct,
        "rows": rows,
    }
    (out / "d6-closure-map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fields = [
        "coordinate", "width", "domain", "domain_ratified", "resident", "resident_authority",
        "display_name", "semantic_family", "status", "root_basis", "root_name", "law_path",
        "canonical_coordinate_path_bits", "semantic_law", "semantic_law_authority",
        "coordinate_realization", "coordinate_realization_authority", "certificate_ref",
        "certificate_replay_ok", "collision", "core_closure",
        "semantic_member_of_ratified_domain", "manual_resident_required", "placement_ref",
        "research_overlay_refs",
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
