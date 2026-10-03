#!/usr/bin/env python3
"""#2761 — current-main D5/D6 semantic identity consistency guard.

Consumes only the owner-directive historical maps already on main.

This does not ratify a new coordinate. It prevents stale replay logic from
identifying two different semantic objects merely because an older research
lane projected the same human name onto both domains.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D5 = ROOT / "knowledge" / "d5-historical-full-map.json"
D6 = ROOT / "knowledge" / "d6-historical-full-map.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def by_coordinate(payload: dict, coordinate: str) -> dict:
    rows = payload.get("coordinates", [])
    matches = [row for row in rows if row.get("coordinate") == coordinate]
    if len(matches) != 1:
        raise AssertionError(
            f"{path_name(payload)} coordinate {coordinate}: expected one row, got {len(matches)}"
        )
    return matches[0]


def path_name(payload: dict) -> str:
    return str(payload.get("domain", payload.get("schema", "unknown")))


def names(payload: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in payload.get("coordinates", []):
        out.setdefault(str(row.get("name")), []).append(str(row.get("coordinate")))
    return out


def build() -> dict:
    d5 = load(D5)
    d6 = load(D6)

    assert d5["authority"] == "owner-directive-2026-10-03"
    assert d6["authority"] == "owner-directive-2026-10-03"
    assert d5["status_counts"]["total"] == 32
    assert d5["status_counts"]["unallocated"] == 0
    assert d6["status_counts"]["total"] == 64
    assert d6["status_counts"]["unallocated"] == 0

    d5_setq = by_coordinate(d5, "00111")
    d6_child = by_coordinate(d6, "001111")

    assert d5_setq["name"] == "SETQ"
    assert d6_child["name"] == "DEFVAR"
    assert d6_child["parent_d5"] == "00111"

    d5_names = names(d5)
    d6_names = names(d6)

    # Current owner maps are exact enough to reject the stale identity replay:
    # SETQ belongs to D5:00111, while its 1-bit D6 child is DEFVAR.
    assert d5_names.get("SETQ") == ["00111"]
    assert "SETQ" not in d6_names
    assert d6_names.get("DEFVAR") == ["001111"]

    # Human-name equality is never an identity bridge across domains.
    identity_same = (
        d5_setq["name"] == d6_child["name"]
        and d5.get("domain") == d6.get("domain")
        and d5_setq["coordinate"] == d6_child["coordinate"]
    )
    assert identity_same is False

    return {
        "schema": "d5-d6-setq-identity/v1",
        "issue": 2761,
        "phase": "SENS-DERIVATION",
        "authority": "consistency-check-over-current-owner-directive-maps",
        "d5": {
            "domain": d5["domain"],
            "coordinate": d5_setq["coordinate"],
            "name": d5_setq["name"],
            "behavior": d5_setq["behavior"],
        },
        "d6": {
            "domain": d6["domain"],
            "coordinate": d6_child["coordinate"],
            "name": d6_child["name"],
            "behavior": d6_child["behavior"],
            "parent_d5": d6_child["parent_d5"],
        },
        "verdict": {
            "same_semantic_object": False,
            "stale_d6_setq_identity_allowed": False,
            "current_d5_setq": "Core.D5:00111",
            "current_d6_child": "Core.D6:001111=DEFVAR",
            "relation": "D6 child of D5 coordinate; distinct semantic object/name/law",
        },
        "non_conclusions": [
            "human name is not a cross-domain identity bridge",
            "this guard does not derive D5 or D6 occupancy",
            "this guard does not create a new owner decision",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = build()

    print("D5-D6-SETQ-IDENTITY=PASS")
    print("D5-SETQ=Core.D5:00111")
    print("D6-001111=DEFVAR")
    print("D6-SETQ-NAME=ABSENT")
    print("SAME-SEMANTIC-OBJECT=NO")
    print("STALE-D6-SETQ-REPLAY=REJECTED")
    print("RULE=same-name-across-domains-is-not-identity")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
