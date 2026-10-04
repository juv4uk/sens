#!/usr/bin/env python3
"""#3025 — classify the ratified D5 FEXPR/MACRO pair from merged protocol donors.

Research-only. This script does not execute legacy Function8 rows and does not
allocate or move any Core.D5 coordinate. It composes:
- OD-005 owner occupancy;
- the merged five-axis special-call factor artifact.

The question is only whether 00010/00011 form one local sibling law.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
SPECIAL = ROOT / "benchmarks" / "d5-structural-discovery" / "special-call-factor.json"
OUT = ROOT / "knowledge" / "d5-fexpr-macro-pair.json"

EXPECTED_DELTAS = {
    "explicit-caller-env",
    "returned-form-protocol",
    "expansion-timing",
    "invocation-packaging",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def coordinate_row(owner: dict[str, Any], coordinate: str) -> dict[str, Any]:
    rows = [row for row in owner["coordinates"] if row["coordinate"] == coordinate]
    assert len(rows) == 1, (coordinate, rows)
    return rows[0]


def protocol_row(special: dict[str, Any], protocol: str) -> dict[str, Any]:
    rows = [row for row in special["protocols"] if row["protocol"] == protocol]
    assert len(rows) == 1, (protocol, rows)
    return rows[0]["axes"]


def axis_rows(special: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["factor_id"]: row for row in special["axes"]}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render() -> dict[str, Any]:
    owner = load(OWNER_MAP)
    special = load(SPECIAL)

    assert owner["domain"] == "Core.D5"
    assert owner["width"] == 5
    assert owner["capacity"] == 32
    assert owner["status_counts"]["total"] == 32
    assert owner["status_counts"]["unallocated"] == 0

    fexpr = coordinate_row(owner, "00010")
    macro = coordinate_row(owner, "00011")
    assert fexpr["name"] == "FEXPR"
    assert macro["name"] == "MACRO"
    assert fexpr["parent_d4"] == macro["parent_d4"] == "0001"

    fexpr_axes = protocol_row(special, "fexpr-fsubr")
    macro_axes = protocol_row(special, "hart-macro")

    all_axes = set(fexpr_axes) | set(macro_axes)
    shared = sorted(axis for axis in all_axes if fexpr_axes[axis] == macro_axes[axis])
    deltas = sorted(axis for axis in all_axes if fexpr_axes[axis] != macro_axes[axis])

    # Positive shared control: both protocols consume raw syntax.
    assert "raw-form-input" in shared
    assert fexpr_axes["raw-form-input"] is True
    assert macro_axes["raw-form-input"] is True

    # Strong negative control against one-bit sibling interpretation.
    assert set(deltas) == EXPECTED_DELTAS, deltas
    assert len(deltas) == 4

    # Every differing axis must already have an independent executable witness.
    rows = axis_rows(special)
    for axis in deltas:
        row = rows[axis]
        assert row["status"] == "independently-observable-axis"
        assert row["evidence"]
        assert row["remove_one_attack"]

    result = {
        "schema": "d5-fexpr-macro-pair/1",
        "domain": "Core.D5",
        "owner_map_authority": owner["authority"],
        "owner_map_mutation": "NONE",
        "pair": {
            "prefix_d4": "0001",
            "child0": {
                "coordinate": fexpr["coordinate"],
                "historical_name": fexpr["name"],
                "protocol_donor": "fexpr-fsubr",
            },
            "child1": {
                "coordinate": macro["coordinate"],
                "historical_name": macro["name"],
                "protocol_donor": "hart-macro",
            },
        },
        "shared_axes": shared,
        "independent_deltas": deltas,
        "delta_count": len(deltas),
        "classification": "PROTOCOL-PRODUCT/MULTI-DELTA",
        "relation_class": "SEMANTIC-LAW",
        "local_one_bit_sibling_law": False,
        "d4_parenthood": "NOT-INFERRED",
        "global_d5_suffix_theorem": "NOT-PROVED",
        "runtime_requirement": "NO-NEW-D5-RUNTIME; REPLAY-MERGED-PROTOCOL-DONORS",
        "legacy_function8_execution": "FORBIDDEN",
        "evidence": ["#2522/#2528", "#2591/#2602", "#3019", "#2508"],
        "falsifier": (
            "a merged donor replay that collapses the four independently witnessed "
            "deltas to one admitted semantic axis without hidden mechanism/table authority"
        ),
    }

    assert result["classification"] == "PROTOCOL-PRODUCT/MULTI-DELTA"
    assert result["local_one_bit_sibling_law"] is False
    assert result["owner_map_mutation"] == "NONE"
    return result


def main() -> None:
    result = render()
    text = canonical(result)

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.write:
        OUT.write_text(text, encoding="utf-8")
    if args.check:
        assert OUT.exists(), "D5 FEXPR/MACRO report missing"
        assert OUT.read_text(encoding="utf-8") == text, "D5 FEXPR/MACRO report stale"

    print("D5-FEXPR-MACRO-PAIR=PASS")
    print("coordinates=00010,00011")
    print("shared-axis=raw-form-input")
    print("independent-deltas=4")
    print("delta-axes=" + ",".join(result["independent_deltas"]))
    print("classification=PROTOCOL-PRODUCT/MULTI-DELTA")
    print("local-one-bit-sibling-law=no")
    print("d4-parenthood=NOT-INFERRED")
    print("global-d5-suffix-theorem=NOT-PROVED")
    print("owner-map-mutation=NONE")


if __name__ == "__main__":
    main()
