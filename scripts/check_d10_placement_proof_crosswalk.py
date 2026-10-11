#!/usr/bin/env python3
"""Verify D10's *existing* 256 placements against ratified D9; expose missing placements.

No new candidate, coordinate, opcode, runtime authority or ratification is created.
The crosswalk output keeps selected/unplaced meanings visible for subsequent proof intake.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlacementError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PlacementError(message)


def audit(d9: dict, seed: dict, inventory: dict) -> dict:
    require(d9.get("status") == "owner-ratified", "D9 must be owner-ratified")
    require(d9.get("authority") == "#4008", "wrong normative D9 authority")
    require(d9.get("width") == 9 and d9.get("occupancy") == 512, "D9 width/occupancy drift")
    require(seed.get("law", {}).get("name") == "selector-suffix-extension",
            "wrong D10 selector generator")
    require(seed.get("width") == 10 and inventory.get("width") == 10,
            "incorrect D10 identity width")
    require(seed.get("status") == "RESEARCH-UNRATIFIED"
            and inventory.get("status") == "RESEARCH-UNRATIFIED-PARTIAL",
            "unapproved D10 authority")
    require(inventory.get("capacity") == seed.get("target_capacity") == 1024,
            "D10 capacity drift")
    require(len(d9.get("rows", [])) == 512, "D9 row count incorrect")
    parents = {row["coordinate"]: row for row in d9["rows"]}
    require(len(parents) == 512, "duplicate D9 coordinates")
    seed_rows = seed.get("rows")
    require(isinstance(seed_rows, list) and len(seed_rows) == 256,
            "expected exactly 256 proved selector children")
    d10_rows = inventory.get("rows")
    require(isinstance(d10_rows, list), "D10 inventory missing")
    by_id = {r["stable_id"]: r for r in d10_rows}
    require(len(by_id) == len(d10_rows), "D10 stable_id collision")
    names = [r["semantic_name"] for r in d10_rows]
    require(len(set(names)) == len(names), "D10 duplicate semantic identity")
    seen_codes = set()
    seen_children = set()
    parent_counts = {}
    manifest = []
    for child in seed_rows:
        parent_code = child["parent_coordinate"]
        parent = parents.get(parent_code)
        require(parent is not None, "D10 references missing D9 parent")
        require(parent.get("coordinate_basis") == "proved-selector-generator",
                "D10 child derived from D9 gauge, not selector theorem")
        require(child.get("parent_stable_id") == parent.get("stable_id"),
                "D10 parent stable-id mismatch")
        require(child.get("parent_semantic_name") == parent.get("resident"),
                "D10 parent law identity mismatch")
        bit = child.get("generator_suffix_bit")
        require(bit in ("0", "1"), "invalid selector bit")
        expected_code = parent_code + bit
        require(child.get("coordinate") == expected_code
                and re.fullmatch(r"[01]{10}", expected_code) is not None,
                "bad D10 child coordinate")
        role = "CAR/A" if bit == "0" else "CDR/D"
        require(child.get("generator_suffix_role") == role,
                "D10 selector suffix direction inverted")
        require(parent["resident"].startswith("C") and parent["resident"].endswith("R"),
                "invalid source selector naming")
        expected_name = parent["resident"][:-1] + ("A" if bit == "0" else "D") + "R"
        require(child["semantic_name"] == expected_name, "D10 generator semantic mismatch")
        require(expected_code not in seen_codes, "D10 10-bit coordinate collision")
        seen_codes.add(expected_code)
        require(child["stable_id"] not in seen_children, "duplicate D10 child ID")
        seen_children.add(child["stable_id"])
        current = by_id.get(child["stable_id"])
        require(current is not None, "seed child absent from canonical D10")
        for key in ("semantic_name", "coordinate", "coordinate_basis", "relation_class"):
            require(current.get(key) == child.get(key), "seed/inventory mismatch: " + key)
        require(current.get("coordinate_basis") == "PROVED-SELECTOR-GENERATOR",
                "coordinate not supported by generator")
        require(current.get("ratified_resident") is False, "D10 illegally ratified")
        parent_counts[parent_code] = parent_counts.get(parent_code, 0) + 1
        manifest.append({
            "stable_id": child["stable_id"], "semantic_name": child["semantic_name"],
            "coordinate": expected_code, "parent_domain": "D9",
            "parent_coordinate": parent_code,
            "parent_stable_id": parent["stable_id"],
            "suffix_bit": bit, "proof": "D9 parent #4008 + selector-suffix-extension #4012",
            "ratified": False,
        })
    require(len(parent_counts) == 128 and all(n == 2 for n in parent_counts.values()),
            "must have 128 D9 theorem-parents each with exactly two children")
    all_codes = [r["coordinate"] for r in d10_rows if r.get("coordinate") is not None]
    require(len(all_codes) == len(set(all_codes)) == 256,
            "new unsupported or duplicate D10 coordinates")
    require(set(all_codes) == seen_codes, "unproved D10 coordinate appeared")
    for row in d10_rows:
        require(row.get("ratified_resident") is False, "D10 must remain unratified")
        if row["stable_id"] not in seen_children:
            require(row.get("coordinate") is None
                    and row.get("coordinate_basis") == "UNPLACED",
                    "non-selector row obtained unjustified coordinate")
    account = inventory.get("accounting", {})
    n = len(d10_rows)
    require(n <= 1024 and account.get("selected_semantic_candidates") == n,
            "selected D10 occupancy drift")
    require(account.get("law_forced_coordinates") == 256,
            "law-forced accounting drift")
    require(account.get("unplaced_selected_candidates") == n - 256,
            "unplaced D10 accounting drift")
    require(account.get("remaining_semantic_inventory") == 1024 - n,
            "remaining D10 accounting drift")
    require(account.get("ratified_d10_residents") == 0,
            "unapproved D10 ratification")
    return {
        "schema": "d10-placement-proof-crosswalk/v1",
        "scope": "CANONICAL-D10-RESEARCH-NO-RATIFICATION",
        "selected": n, "capacity": 1024,
        "proof_forced_placed": 256, "proof_parents": len(parent_counts),
        "selected_unplaced": n - 256, "semantic_gaps": 1024 - n,
        "ratified": 0, "placements": manifest,
        "unplaced": [{"stable_id": row["stable_id"], "semantic_name": row["semantic_name"],
                      "coordinate": None, "status": "SELECTED-UNPLACED"}
                     for row in d10_rows if row["stable_id"] not in seen_children],
    }


def negative_controls(d9: dict, seed: dict, inv: dict) -> int:
    tests = [
        ("parent", lambda d, s, i: s["rows"][0].__setitem__("parent_coordinate", "000000000")),
        ("suffix", lambda d, s, i: s["rows"][0].__setitem__("generator_suffix_bit", "1")),
        ("name", lambda d, s, i: s["rows"][0].__setitem__("semantic_name", "FALSE-LAW")),
        ("coordinate", lambda d, s, i: s["rows"][0].__setitem__("coordinate", "1111111111")),
        ("collision", lambda d, s, i: i["rows"][256].__setitem__("coordinate", s["rows"][0]["coordinate"])),
        ("ratified", lambda d, s, i: i["rows"][0].__setitem__("ratified_resident", True)),
        ("missing", lambda d, s, i: i["rows"].pop(0)),
        ("count", lambda d, s, i: i["accounting"].__setitem__("remaining_semantic_inventory", 0)),
        ("gauge", lambda d, s, i: d["rows"].__setitem__(next(j for j,x in enumerate(d["rows"]) if x["coordinate"] == s["rows"][0]["parent_coordinate"]), {**next(x for x in d["rows"] if x["coordinate"] == s["rows"][0]["parent_coordinate"]), "coordinate_basis": "owner-ratified-s4-gauge-choice"})),
    ]
    for label, change in tests:
        d, s, i = copy.deepcopy(d9), copy.deepcopy(seed), copy.deepcopy(inv)
        change(d, s, i)
        try:
            audit(d, s, i)
        except (PlacementError, KeyError, IndexError):
            continue
        raise PlacementError("negative control escaped: " + label)
    return len(tests)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()
    d9 = json.loads((args.root / "knowledge/d9-ratified.json").read_text())
    seed = json.loads((args.root / "knowledge/d10-selector-seed.json").read_text())
    inv = json.loads((args.root / "knowledge/d10-v1-semantic-inventory.json").read_text())
    report = audit(d9, seed, inv)
    if args.self_test:
        report["negative_mutations_rejected"] = negative_controls(d9, seed, inv)
    if args.manifest:
        args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("placements", "unplaced")},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
