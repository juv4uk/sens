#!/usr/bin/env python3
"""#3005 — replay SET/SETQ as a local D5 target-acquisition sibling law.

This is intentionally a thin composed witness.

Semantic donor:
  crates/sens/tests/post_d4_set_setq_factor.rs (#2589)

Owner-coordinate donor:
  knowledge/d5-historical-full-map.json (OD-005)

The script does not define a second SET/SETQ semantics. It first requires the
existing executable #2589 witness to pass, then classifies the already-ratified
D5 sibling coordinates.

Research only. No owner-map/runtime mutation.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER_MAP = ROOT / "knowledge" / "d5-historical-full-map.json"
DONOR_TEST = "post_d4_set_setq_factor"

SET_COORD = "00110"
SETQ_COORD = "00111"


def iter_objects(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from iter_objects(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_objects(item)


def owner_row(data, coordinate: str):
    rows = [
        obj for obj in iter_objects(data)
        if obj.get("coordinate") == coordinate
    ]
    if len(rows) != 1:
        raise AssertionError(
            f"expected one owner row for {coordinate}, got {len(rows)}"
        )
    return rows[0]


def run_donor() -> None:
    proc = subprocess.run(
        [
            "cargo", "test", "-q",
            "-p", "sens",
            "--test", DONOR_TEST,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout)
        raise SystemExit(proc.returncode)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--skip-donor-test",
        action="store_true",
        help="CI/debug only; classification is authoritative only when donor passes",
    )
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    donor_pass = False
    if not args.skip_donor_test:
        run_donor()
        donor_pass = True

    data = json.loads(OWNER_MAP.read_text(encoding="utf-8"))
    set_row = owner_row(data, SET_COORD)
    setq_row = owner_row(data, SETQ_COORD)

    # Exact owner-map sibling geometry.
    assert SET_COORD[:-1] == SETQ_COORD[:-1] == "0011"
    assert SET_COORD[-1] == "0"
    assert SETQ_COORD[-1] == "1"
    assert set_row.get("parent_d4") == "0011"
    assert setq_row.get("parent_d4") == "0011"

    # Owner behavior text is diagnostic/provenance only, but it must remain
    # compatible with the independently executable #2589 semantic donor.
    set_behavior = str(set_row.get("behavior", "")).lower()
    setq_behavior = str(setq_row.get("behavior", "")).lower()
    assert "computed" in set_behavior
    assert "static" in setq_behavior or "symbol" in setq_behavior

    # #2589 establishes:
    #   SET  = evaluated/computed target acquisition + shared mutation core
    #   SETQ = syntax-fixed/literal target acquisition + same mutation core
    #
    # Search/update/missing-name policy is explicitly held fixed there.
    classification = "LOCAL-SIBLING-LAW" if donor_pass else "UNVERIFIED"

    result = {
        "schema": "d5-set-setq-sibling-law/v1",
        "authority": "research-only",
        "issue": 3005,
        "domain": "Core.D5",
        "owner_authority": "OD-005",
        "semantic_donor": "#2589/post_d4_set_setq_factor",
        "donor_executable_pass": donor_pass,
        "coordinates": {
            "child0": SET_COORD,
            "child1": SETQ_COORD,
            "shared_printed_prefix": "0011",
        },
        "fixed_axes": {
            "mutation_core": "nearest-existing/fail shared-location update",
            "update_value_policy": "held equal",
            "search_scope": "held equal",
            "missing_binding_policy": "held equal",
        },
        "varied_axis": {
            "name": "target-symbol-acquisition",
            SET_COORD: "evaluate/compute target expression to obtain Core symbol",
            SETQ_COORD: "take target Core symbol syntax-fixed/literal",
        },
        "decision": classification,
        "relation_class": (
            "SEMANTIC-LAW" if donor_pass else "UNKNOWN"
        ),
        "d4_parenthood_0011": "NOT-INFERRED",
        "d6_law_mutation": "NONE",
        "owner_map_mutation": "NONE",
        "non_conclusions": [
            "shared printed prefix 0011 does not make D4 DEFINE the semantic parent",
            "the sibling law does not encode nearest/current-frame policy",
            "the sibling law does not encode create/fail missing-name policy",
            "the sibling law does not allocate or move any D5/D6 coordinate",
            "human SET/SETQ names are diagnostics, not canonical identity",
        ],
    }

    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = [
        {
            "coordinate": SET_COORD,
            "sibling_bit": "0",
            "target_acquisition": result["varied_axis"][SET_COORD],
            "mutation_core": result["fixed_axes"]["mutation_core"],
            "decision": classification,
        },
        {
            "coordinate": SETQ_COORD,
            "sibling_bit": "1",
            "target_acquisition": result["varied_axis"][SETQ_COORD],
            "mutation_core": result["fixed_axes"]["mutation_core"],
            "decision": classification,
        },
    ]
    with (args.out / "result.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    report = [
        "# D5 SET/SETQ sibling law — #3005",
        "",
        f"Existing #2589 executable donor: **{'PASS' if donor_pass else 'SKIPPED'}**",
        "",
        "| coordinate | target acquisition | mutation core |",
        "|---|---|---|",
        f"| {SET_COORD} | evaluated/computed target | nearest-existing/fail shared-location |",
        f"| {SETQ_COORD} | syntax-fixed/literal target | nearest-existing/fail shared-location |",
        "",
        f"Decision: **{classification}**",
        "",
        "The one isolated semantic axis is target-symbol acquisition.",
        "Mutation/search/missing-binding policy is held equal by the donor witness.",
        "",
        "D4 printed-prefix parenthood (0011): **NOT-INFERRED**.",
        "Owner-map mutation: **NONE**.",
        "D6 law mutation: **NONE**.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
