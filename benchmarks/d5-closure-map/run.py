#!/usr/bin/env python3
"""#2763 historical OD-005 D5 machine-map provenance.

SUPERSEDED for current D5 authority by #3305 / knowledge/d5-ratified.json.

This benchmark intentionally preserves the old OD-005 map and its then-current
selector coordinates as historical evidence. It must NOT import the live
Contract 11.6 selector forecast, because current D3/D5 geometry has changed.
Current D5 authority is guarded separately by check-d5-current-authority.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from itertools import product
from pathlib import Path
from typing import Any

WIDTH = 5
CAPACITY = 1 << WIDTH

ROOTS = {
    "101": {"root_name": "CAR", "root_choice": 0, "selector_letter": "A"},
    "110": {"root_name": "CDR", "root_choice": 1, "selector_letter": "D"},
}
LAW_BITS = {
    "0": {"law_id": "sel.law.extend-a", "display": "compose-first-projection", "letter": "A"},
    "1": {"law_id": "sel.law.extend-d", "display": "compose-rest-projection", "letter": "D"},
}

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "benchmarks" / "generator-economy" / "semantic-fact-ledger.json"
OWNER_MAP = REPO / "knowledge" / "d5-historical-full-map.json"
SEMANTIC_LEDGER = REPO / "knowledge" / "d5-d6-semantic-ledger.json"


def load_od005_selector_words() -> set[str]:
    """Frozen OD-005 selector coordinates; historical provenance only."""
    suffix_width = WIDTH - 3
    words = {
        root + "".join(suffix)
        for root in ROOTS
        for suffix in product("01", repeat=suffix_width)
    }
    if len(words) != 8:
        raise AssertionError(f"OD-005 expected 8 D5 selectors, got {len(words)}")
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


def load_owner_map() -> dict[str, dict[str, Any]]:
    data = json.loads(OWNER_MAP.read_text(encoding="utf-8"))
    if data["schema"] != "d5-historical-full-map/v1":
        raise AssertionError(f"unexpected D5 owner-map schema: {data['schema']}")
    if data["domain"] != "Core.D5" or data["width"] != WIDTH or data["capacity"] != CAPACITY:
        raise AssertionError("OD-005 owner-map domain/width/capacity drift")
    if data["status_counts"]["total"] != CAPACITY or data["status_counts"]["unallocated"] != 0:
        raise AssertionError("OD-005 owner map must be 32/32 with zero unallocated")

    rows = data["coordinates"]
    by = {row["coordinate"]: row for row in rows}
    if len(rows) != CAPACITY or len(by) != CAPACITY:
        raise AssertionError("OD-005 owner map must contain 32 unique coordinates")
    expected = {format(i, "05b") for i in range(CAPACITY)}
    if set(by) != expected:
        raise AssertionError("OD-005 owner map does not cover every D5 coordinate")
    for coordinate, row in by.items():
        if row["parent_d4"] != coordinate[:4]:
            raise AssertionError(f"{coordinate}: owner parent_d4 is not exact prefix")
    return by


def load_semantic_ledger() -> dict[str, dict[str, Any]]:
    data = json.loads(SEMANTIC_LEDGER.read_text(encoding="utf-8"))
    rows = [row for row in data["rows"] if row["domain"] == "Core.D5"]
    by = {row["coordinate"]: row for row in rows}
    if len(rows) != CAPACITY or len(by) != CAPACITY:
        raise AssertionError("semantic ledger must contain exactly 32 D5 rows")
    for coordinate, row in by.items():
        if row["residency"] != "YES":
            raise AssertionError(f"{coordinate}: owner residency must remain YES")
        if row["width"] != WIDTH:
            raise AssertionError(f"{coordinate}: semantic-ledger width drift")
    return by


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
                "status": "generated",
                "semantic_family": "selector",
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
                "generated_display_name": selector_display_name(root_bits, suffix),
            }
    return rows


def build_map() -> list[dict[str, Any]]:
    owner = load_owner_map()
    semantic = load_semantic_ledger()
    generated = selector_rows()
    forecast_words = load_od005_selector_words()

    if set(generated) != forecast_words:
        raise AssertionError("historical OD-005 selector closure drift")
    if len(generated) != 8:
        raise AssertionError("D5 selector closure must contain exactly 8 rows")

    rows: list[dict[str, Any]] = []
    for n in range(CAPACITY):
        coordinate = format(n, "05b")
        owner_row = owner[coordinate]
        semantic_row = semantic[coordinate]
        is_selector = coordinate in generated

        if semantic_row["name"] != owner_row["name"]:
            raise AssertionError(f"{coordinate}: semantic ledger name disagrees with owner map")
        if semantic_row["parent"] != owner_row["parent_d4"]:
            raise AssertionError(f"{coordinate}: semantic ledger parent disagrees with owner map")

        selector = generated.get(coordinate)
        if selector is not None and selector["generated_display_name"] != owner_row["name"]:
            raise AssertionError(
                f"{coordinate}: selector theorem yields {selector['generated_display_name']} "
                f"but owner map says {owner_row['name']}"
            )

        row = {
            "coordinate": coordinate,
            "width": WIDTH,
            "domain": "D5",
            "domain_ratified": True,
            "residency": "YES",
            "residency_authority": semantic_row["residency_authority"],
            "display_name": owner_row["name"],
            "display_name_authority": False,
            "historical_category": owner_row["category"],
            "historical_provenance": owner_row["provenance"],
            "status": "generated" if is_selector else "owner-historical",
            "owner_assignment": not is_selector,
            "semantic_family": "selector" if is_selector else owner_row["category"],
            "semantic_class": semantic_row["semantic_class"],
            "semantic_evidence": semantic_row["semantic_evidence"],
            "semantic_note": semantic_row["semantic_note"],
            "implementation_status": semantic_row["implementation_status"],
            "parent_d4": owner_row["parent_d4"],
            "root_basis": selector["root_basis"] if selector else "",
            "root_name": selector["root_name"] if selector else "",
            "law_path": selector["law_path"] if selector else [],
            "canonical_coordinate_path_bits": (
                selector["canonical_coordinate_path_bits"] if selector else ""
            ),
            "semantic_law": selector["semantic_law"] if selector else "",
            "semantic_law_authority": (
                selector["semantic_law_authority"] if selector else ""
            ),
            "coordinate_realization": (
                selector["coordinate_realization"] if selector else "owner historical projection"
            ),
            "coordinate_realization_authority": (
                selector["coordinate_realization_authority"] if selector else "OD-005/#2538"
            ),
            "certificate_ref": selector["certificate_ref"] if selector else "",
            "certificate": selector["certificate"] if selector else None,
            "certificate_replay_ok": (
                selector["certificate_replay_ok"] if selector else False
            ),
            "collision": False,
            "semantic_member_of_ratified_domain": True,
            "manual_resident_required": False,
            "placement_ref": "OD-005/#2538",
            "research_overlay_refs": semantic_row["semantic_evidence"],
        }
        rows.append(row)

    if len(rows) != CAPACITY or len({r["coordinate"] for r in rows}) != CAPACITY:
        raise AssertionError("D5 map must contain every coordinate exactly once")
    if sum(r["status"] == "generated" for r in rows) != 8:
        raise AssertionError("D5 selector-generated count drift")
    if sum(r["status"] == "owner-historical" for r in rows) != 24:
        raise AssertionError("D5 owner-historical count drift")
    if any(r["residency"] != "YES" for r in rows):
        raise AssertionError("OD-005 current map cannot contain non-resident D5 rows")
    if any(r["collision"] for r in rows):
        raise AssertionError("D5 collision detected")
    return rows


def accounting(rows: list[dict[str, Any]]) -> dict[str, Any]:
    generated = sum(r["status"] == "generated" for r in rows)
    owner_historical = sum(r["status"] == "owner-historical" for r in rows)
    depth = WIDTH - 3

    def totals(count: int, bits_each: int) -> dict[str, int]:
        total_bits = count * bits_each
        return {
            "count": count,
            "bits_each": bits_each,
            "bits_total": total_bits,
            "bytes_ceil_total": math.ceil(total_bits / 8),
        }

    return {
        "domain_ratified": True,
        "owner_resident_count": len(rows),
        "generated_coordinate_count": generated,
        "owner_historical_count": owner_historical,
        "unknown_free_count": 0,
        "full_owner_coordinate_payload": totals(len(rows), WIDTH),
        "flat_generated_coordinates": totals(generated, WIDTH),
        "self_framed_selector_certificate": totals(generated, 4 + depth),
        "outer_framed_certificate_payload": totals(generated, 1 + depth),
        "semantic_fact_model": "selector-root-law-current",
        "shared_basis_semantic_fact_interval": load_selector_fact_interval(),
        "new_d5_generated_rows_charged_as_independent_facts": 0,
        "pre_od005_sparse_baseline": {
            "status": "ARCHIVED-RESEARCH",
            "selector_generated": 8,
            "unknown_free": 24,
            "authority": "#2510/#2689 pre-OD005",
        },
        "no_scalar_winner": True,
    }


def report(rows: list[dict[str, Any]], acct: dict[str, Any]) -> str:
    generated = sum(r["status"] == "generated" for r in rows)
    owner_historical = sum(r["status"] == "owner-historical" for r in rows)
    derived = sum(r["semantic_class"] == "derived" for r in rows)
    return "\n".join([
        "# D5 historical owner map — #2763 / OD-005",
        "",
        "Historical owner occupancy source: knowledge/d5-historical-full-map.json.",
        "Semantic derivability authority is independent: knowledge/d5-d6-semantic-ledger.json.",
        "",
        "| class | count |",
        "|---|---:|",
        "| exact D5 coordinates | 32 |",
        f"| resident | {len(rows)} |",
        f"| selector-law generated | {generated} |",
        f"| owner-historical nonselector | {owner_historical} |",
        "| UNKNOWN current occupancy | 0 |",
        f"| rows semantically derived but still resident | {derived} |",
        "| collisions | 0 |",
        "",
        "Rules:",
        "- residency does not imply semantic irreducibility;",
        "- derivability does not erase owner-ratified historical residency;",
        "- eight selector residents still replay the CAR/CDR generator theorem;",
        "- the other 24 residents are OD-005 historical placements, not selector-law children;",
        "- PRE-OD005 8+24 sparse results remain archived research evidence only.",
        "",
        "Accounting:",
        f"- full owner coordinate payload: {acct['full_owner_coordinate_payload']['bits_total']} bits;",
        f"- selector-generated exact coordinates: {acct['flat_generated_coordinates']['bits_total']} bits;",
        f"- selector shared-basis semantic-fact interval: {acct['shared_basis_semantic_fact_interval']}.",
        "",
    ])


def write_outputs(out: Path, rows: list[dict[str, Any]], acct: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "d5-closure-map/v2",
        "authority": "OD-005/#2538",
        "domain": "Core.D5",
        "domain_ratified": True,
        "width": WIDTH,
        "capacity": CAPACITY,
        "counts": {
            "resident": 32,
            "generated": 8,
            "owner-historical": 24,
            "UNKNOWN/free": 0,
            "collisions": 0,
        },
        "provenance": {
            "owner_map": "knowledge/d5-historical-full-map.json",
            "semantic_ledger": "knowledge/d5-d6-semantic-ledger.json",
            "selector_law": "#2158",
            "forecast": "#2322/#2329",
            "generation_certificates": "#2323/#2345",
            "owner_ratification": "OD-005/#2538/#2750",
            "integration": "#2762/#2763",
        },
        "accounting": acct,
        "rows": rows,
    }
    (out / "d5-closure-map.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    fields = [
        "coordinate", "width", "domain", "domain_ratified", "residency",
        "residency_authority", "display_name", "historical_category",
        "historical_provenance", "status", "owner_assignment",
        "semantic_family", "semantic_class", "implementation_status", "parent_d4",
        "root_basis", "root_name", "law_path", "canonical_coordinate_path_bits",
        "semantic_law", "semantic_law_authority", "coordinate_realization",
        "coordinate_realization_authority", "certificate_ref",
        "certificate_replay_ok", "collision", "semantic_member_of_ratified_domain",
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
