#!/usr/bin/env python3
"""#3040 — classify Core.D5 GO/RETURN using merged control-factor evidence.

Research-only. Owner coordinates remain immutable. The classifier replays the
existing non-local-exit factor witness and cross-checks the current residency /
derivability ledger. No production control mechanism is added.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
SEMANTIC_LEDGER = ROOT / "knowledge" / "d5-d6-semantic-ledger.json"
DONOR = ROOT / "scripts" / "research-2590-nonlocal-exit.py"
OUT = ROOT / "knowledge" / "d5-go-return-pair.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def row(rows: list[dict[str, Any]], name: str) -> dict[str, Any]:
    hits = [item for item in rows if item.get("name") == name and item.get("domain") == "Core.D5"]
    assert len(hits) == 1, (name, hits)
    return hits[0]


def owner_row(owner: dict[str, Any], coordinate: str) -> dict[str, Any]:
    hits = [item for item in owner["coordinates"] if item["coordinate"] == coordinate]
    assert len(hits) == 1, (coordinate, hits)
    return hits[0]


def replay_donor() -> str:
    proc = subprocess.run(
        ["python3", str(DONOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    out = proc.stdout
    required = [
        "NONLOCAL-EXIT-FACTOR=PASS",
        "PARENT-GO=REJECT-base-operation-mismatch",
        "STRONGEST-HONEST-PARENT=NO-PARENT",
        "PROG-CLASSIFICATION=COMPOSITE",
    ]
    for marker in required:
        assert marker in out, (marker, out)
    return out


def render() -> dict[str, Any]:
    owner = load(OWNER_MAP)
    ledger = load(SEMANTIC_LEDGER)
    donor_out = replay_donor()

    go_owner = owner_row(owner, "01100")
    return_owner = owner_row(owner, "01101")
    assert go_owner["name"] == "GO"
    assert return_owner["name"] == "RETURN"
    assert go_owner["parent_d4"] == return_owner["parent_d4"] == "0110"

    go = row(ledger["rows"], "GO")
    ret = row(ledger["rows"], "RETURN")
    assert go["coordinate"] == "01100"
    assert ret["coordinate"] == "01101"
    assert go["semantic_class"] == "derived"
    assert ret["semantic_class"] == "root"
    assert "intra-prog transfer" in go["semantic_note"].lower()
    assert "non-local exit" in ret["semantic_note"].lower()

    # The donor's SemanticShape table makes all three differences explicit.
    axes = ["payload-kind", "control-extent", "stack-effect"]
    donor_source = DONOR.read_text(encoding="utf-8")
    assert 'SemanticShape("GO", "tag-symbol", "jump-to-label", "intra-frame-ip-change")' in donor_source
    assert 'SemanticShape("RETURN", "value", "nonlocal-exit-transfer", "unwinds-to-enclosing-prog")' in donor_source
    assert "PARENT-GO=REJECT-base-operation-mismatch" in donor_out

    return {
        "schema": "d5-go-return-pair/1",
        "domain": "Core.D5",
        "owner_map_authority": owner["authority"],
        "owner_map_mutation": "NONE",
        "pair": {
            "prefix_d4": "0110",
            "child0": {"coordinate": "01100", "historical_name": "GO"},
            "child1": {"coordinate": "01101", "historical_name": "RETURN"},
        },
        "semantic_classes": {"GO": "derived", "RETURN": "root"},
        "same_base_object": False,
        "observable_mismatches": axes,
        "classification": "HISTORICAL-PAIRING",
        "relation_class": "COORDINATE-LAW",
        "local_one_bit_sibling_law": False,
        "d4_parenthood": "NOT-INFERRED",
        "global_d5_suffix_theorem": "NOT-PROVED",
        "donor_replay": "PASS",
        "evidence": ["#2590/#2606", "#2765/#2772", "#3019", "#2508"],
        "falsifier": (
            "a replayable same-base law reducing GO and RETURN to one independent "
            "delta while preserving payload, control extent, and stack observations"
        ),
    }


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    result = render()
    if args.write:
        OUT.write_text(canonical(result), encoding="utf-8")
    if args.check:
        assert OUT.exists(), "D5 GO/RETURN report missing"
        assert json.loads(OUT.read_text(encoding="utf-8")) == result, (
            "D5 GO/RETURN report stale"
        )

    print("D5-GO-RETURN-PAIR=PASS")
    print("coordinates=01100,01101")
    print("semantic-classes=derived,root")
    print("same-base-object=no")
    print("observable-mismatches=3")
    print("classification=HISTORICAL-PAIRING")
    print("relation-class=COORDINATE-LAW")
    print("local-one-bit-sibling-law=no")
    print("d4-parenthood=NOT-INFERRED")
    print("global-d5-suffix-theorem=NOT-PROVED")
    print("owner-map-mutation=NONE")


if __name__ == "__main__":
    main()
