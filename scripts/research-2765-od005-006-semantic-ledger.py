#!/usr/bin/env python3
"""OD-005/OD-006 historical residency vs semantic-class ledger (#2765).

Owner maps define exact residency for all D5/D6 coordinates.
This ledger keeps semantic derivability/classification orthogonal:
resident != primitive, derived != non-resident.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D5 = ROOT / "knowledge" / "d5-historical-full-map.json"
D6 = ROOT / "knowledge" / "d6-historical-full-map.json"
PLACEMENT = ROOT / "benchmarks" / "post-d4-semantic-placement" / "placement.json"
OUT = ROOT / "knowledge" / "d5-d6-semantic-ledger.json"

D5_SELECTORS = {
    "10100","10101","10110","10111",
    "11000","11001","11010","11011",
}
D6_SELECTORS = {
    f"{prefix}{suffix}"
    for prefix in ("10100","10101","10110","10111","11000","11001","11010","11011")
    for suffix in ("0","1")
}

CLASS_BY_PLACEMENT = {
    "DERIVED-UNDER-OWNER": "derived",
    "HISTORICAL-ADAPTER": "historical-mechanism",
    "COMPOSITE": "composite",
    "PROVEN-ROOT-UNPLACED": "root",
    "CARRIER-FAMILY": "protocol",
    "POLICY-OVER-CARRIER": "protocol",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_from_placement(name: str, placement_by_name: dict[str, dict]) -> dict:
    row = placement_by_name.get(name)
    if row is None:
        return {
            "semantic_class": "historical-observed",
            "semantic_evidence": [],
            "semantic_note": "No stronger merged semantic classification is attached to this historical resident yet.",
        }

    kind = row["placement_kind"]
    semantic_class = CLASS_BY_PLACEMENT.get(kind)
    if semantic_class is None:
        raise AssertionError(f"unhandled placement kind for {name}: {kind}")

    return {
        "semantic_class": semantic_class,
        "semantic_evidence": row.get("evidence", []),
        "semantic_note": row["reason"],
    }


def build_rows(owner: dict, width: int, placement_by_name: dict[str, dict]) -> list[dict]:
    selector_coords = D5_SELECTORS if width == 5 else D6_SELECTORS
    parent_key = "parent_d4" if width == 5 else "parent_d5"
    rows = []

    for src in owner["coordinates"]:
        coord = src["coordinate"]
        name = src["name"]
        if len(coord) != width or set(coord) - {"0","1"}:
            raise AssertionError(f"invalid exact coordinate {coord!r} for D{width}")

        row = {
            "domain": f"Core.D{width}",
            "coordinate": coord,
            "width": width,
            "name": name,
            "parent": src[parent_key],
            "residency": "YES",
            "residency_authority": owner["authority"],
            "historical_category": src["category"],
            "historical_provenance": src["provenance"],
            "implementation_status": "NOT-AUDITED",
        }

        if coord in selector_coords:
            row.update({
                "semantic_class": "generated",
                "semantic_evidence": ["#2158", "#2323/#2345", "#2329/#2366"],
                "semantic_note": "Selector law generates this resident; owner residency and generator derivability are both preserved.",
            })
        else:
            row.update(semantic_from_placement(name, placement_by_name))

        rows.append(row)

    return rows


def build() -> dict:
    d5 = load(D5)
    d6 = load(D6)
    placement = load(PLACEMENT)
    placement_by_name = {row["operation"]: row for row in placement["rows"]}

    assert d5["width"] == 5 and d5["capacity"] == 32 and len(d5["coordinates"]) == 32
    assert d6["width"] == 6 and d6["capacity"] == 64 and len(d6["coordinates"]) == 64

    rows = build_rows(d5, 5, placement_by_name) + build_rows(d6, 6, placement_by_name)
    if len(rows) != 96:
        raise AssertionError("semantic ledger must contain exactly 96 D5+D6 rows")
    if len({(r["domain"], r["coordinate"]) for r in rows}) != 96:
        raise AssertionError("duplicate domain/coordinate identity")

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["semantic_class"]] = counts.get(row["semantic_class"], 0) + 1

    by = {(r["domain"], r["coordinate"]): r for r in rows}
    assert by[("Core.D5","00111")]["name"] == "SETQ"
    assert by[("Core.D6","001111")]["name"] == "DEFVAR"
    assert by[("Core.D5","00111")]["residency"] == "YES"
    assert by[("Core.D6","001111")]["residency"] == "YES"
    assert by[("Core.D5","00000")]["semantic_class"] == "derived"  # EVALQUOTE
    assert by[("Core.D5","00001")]["semantic_class"] == "historical-mechanism"  # FUNCTION
    assert by[("Core.D5","00101")]["semantic_class"] == "composite"  # PROG
    assert by[("Core.D5","01101")]["semantic_class"] == "root"  # RETURN
    assert by[("Core.D5","00010")]["semantic_class"] == "protocol"  # FEXPR
    assert by[("Core.D6","111101")]["semantic_class"] == "derived"  # MAPLIST
    assert by[("Core.D6","111110")]["semantic_class"] == "derived"  # SUBLIS
    assert by[("Core.D6","000100")]["semantic_class"] == "protocol"  # FSUBR
    assert sum(r["semantic_class"] == "generated" and r["width"] == 5 for r in rows) == 8
    assert sum(r["semantic_class"] == "generated" and r["width"] == 6 for r in rows) == 16
    assert all(r["residency"] == "YES" for r in rows)

    return {
        "schema": "od005-od006-semantic-ledger/v1",
        "issue": "#2765",
        "principle": "owner residency is orthogonal to semantic derivability",
        "owner_maps": [
            "knowledge/d5-historical-full-map.json",
            "knowledge/d6-historical-full-map.json",
        ],
        "counts": {
            "rows": 96,
            "d5_residents": 32,
            "d6_residents": 64,
            "semantic_classes": counts,
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

    payload = render(build())
    if args.write:
        OUT.write_text(payload, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != payload:
            print("D5-D6-SEMANTIC-LEDGER=STALE")
            return 1
        print("D5-D6-SEMANTIC-LEDGER=CURRENT")

    data = json.loads(payload)
    print("RESIDENCY=D5:32/32,D6:64/64")
    for key, value in sorted(data["counts"]["semantic_classes"].items()):
        print(f"SEMANTIC-{key.upper()}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
