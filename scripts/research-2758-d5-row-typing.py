#!/usr/bin/env python3
"""Conservative OD-005 D5 row typing for #2758.

Historical coordinate presence is preserved exactly.  This script adds a
separate semantic-status sidecar so D6 consumers do not confuse historical
occupancy with semantic residency.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / "knowledge" / "d5-historical-full-map.json"
PLACEMENT = ROOT / "benchmarks" / "post-d4-semantic-placement" / "placement.json"
D5_CLOSURE_SCRIPT = ROOT / "benchmarks" / "d5-closure-map" / "run.py"
OUT = ROOT / "knowledge" / "d5-historical-semantic-status.json"

NO_KINDS = {
    "DERIVED-UNDER-OWNER": "derived",
    "HISTORICAL-ADAPTER": "historical-adapter",
    "COMPOSITE": "composite",
}

UNKNOWN_KINDS = {
    "CARRIER-FAMILY": "unresolved-domain",
    "POLICY-OVER-CARRIER": "unresolved-domain",
    "PROVEN-ROOT-UNPLACED": "unresolved-domain",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def selector_rows() -> dict[str, dict]:
    ns = runpy.run_path(str(D5_CLOSURE_SCRIPT))
    rows = ns["selector_rows"]()
    if len(rows) != 8:
        raise AssertionError(f"expected 8 generated D5 selectors, got {len(rows)}")
    return rows


def classify() -> dict:
    historical = load(HISTORICAL)
    placement = load(PLACEMENT)
    selectors = selector_rows()

    placement_by_name = {row["operation"]: row for row in placement["rows"]}
    out_rows = []

    for row in historical["coordinates"]:
        coord = row["coordinate"]
        name = row["name"]
        base = {
            "coordinate": coord,
            "historical_parent_d4": row["parent_d4"],
            "historical_name": name,
            "historical_category": row["category"],
            "historical_provenance": row["provenance"],
        }

        if coord in selectors:
            sel = selectors[coord]
            base.update(
                {
                    "phase": "SENS-DERIVATION",
                    "status": "generated",
                    "semantic_resident": "YES",
                    "law_ref": sel["semantic_law_authority"],
                    "witness_refs": [
                        sel["certificate_ref"],
                        sel["coordinate_realization_authority"],
                    ],
                    "falsifier_ref": "#2508/#2749",
                    "semantic_note": (
                        "Existing selector law independently generates this exact D5 resident. "
                        "Historical name/provenance is retained but is not the source of residency."
                    ),
                }
            )
            out_rows.append(base)
            continue

        placed = placement_by_name.get(name)
        if placed is None:
            base.update(
                {
                    "phase": "HISTORICAL-INGEST",
                    "status": "historical-observed",
                    "semantic_resident": "UNKNOWN",
                    "law_ref": "UNRESOLVED",
                    "witness_refs": [],
                    "falsifier_ref": "#2508/#2749",
                    "semantic_note": (
                        "OD-005 supplies historical coordinate/provenance only; no merged "
                        "same-domain semantic-residency theorem is encoded for this row."
                    ),
                }
            )
            out_rows.append(base)
            continue

        kind = placed["placement_kind"]
        evidence = placed.get("evidence", [])

        if kind in NO_KINDS:
            phase = (
                "STRUCTURAL-DISCOVERY"
                if kind in {"HISTORICAL-ADAPTER", "COMPOSITE"}
                else "SENS-DERIVATION"
            )
            base.update(
                {
                    "phase": phase,
                    "status": NO_KINDS[kind],
                    "semantic_resident": "NO",
                    "law_ref": placed["primary_owner"],
                    "witness_refs": evidence,
                    "falsifier_ref": "#2236/#2508/#2749",
                    "semantic_note": placed["reason"],
                }
            )
        elif kind in UNKNOWN_KINDS:
            base.update(
                {
                    "phase": "STRUCTURAL-DISCOVERY",
                    "status": UNKNOWN_KINDS[kind],
                    "semantic_resident": "UNKNOWN",
                    "law_ref": placed["primary_owner"],
                    "witness_refs": evidence,
                    "falsifier_ref": "#2236/#2508/#2749",
                    "semantic_note": placed["reason"],
                }
            )
        else:
            raise AssertionError(f"unclassified placement kind for {name}: {kind}")

        out_rows.append(base)

    yes = sum(r["semantic_resident"] == "YES" for r in out_rows)
    no = sum(r["semantic_resident"] == "NO" for r in out_rows)
    unknown = sum(r["semantic_resident"] == "UNKNOWN" for r in out_rows)

    if (yes, no, unknown) != (8, 9, 15):
        raise AssertionError(
            f"unexpected D5 semantic-status partition: YES={yes} NO={no} UNKNOWN={unknown}"
        )

    by_name = {r["historical_name"]: r for r in out_rows}
    assert by_name["SETQ"]["semantic_resident"] == "UNKNOWN"
    assert by_name["EVALQUOTE"]["semantic_resident"] == "NO"
    assert by_name["PAIRLIS"]["semantic_resident"] == "NO"
    assert by_name["CAAAR"]["semantic_resident"] == "YES"

    return {
        "schema": "d5-historical-semantic-status/v1",
        "issue": "#2758",
        "source_historical_map": "knowledge/d5-historical-full-map.json",
        "source_semantic_placement": "benchmarks/post-d4-semantic-placement/placement.json",
        "principle": "historical occupancy is not automatically semantic residency",
        "counts": {
            "historical_rows": 32,
            "semantic_resident_yes": yes,
            "semantic_resident_no": no,
            "semantic_resident_unknown": unknown,
        },
        "rows": out_rows,
    }


def encode(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = ap.parse_args()

    data = classify()
    rendered = encode(data)

    if args.write:
        OUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != rendered:
            print("D5-ROW-TYPING=STALE")
            return 1
        print("D5-ROW-TYPING=CURRENT")

    c = data["counts"]
    print(f"HISTORICAL={c['historical_rows']}")
    print(f"SEMANTIC-YES={c['semantic_resident_yes']}")
    print(f"SEMANTIC-NO={c['semantic_resident_no']}")
    print(f"SEMANTIC-UNKNOWN={c['semantic_resident_unknown']}")
    print("SETQ=UNKNOWN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
