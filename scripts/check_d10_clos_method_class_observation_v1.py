#!/usr/bin/env python3
"""Check historical CLOS method/class donor behavior; never asserts SENS parity."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/d10-clos-method-class-observation-v1.json"
SOURCE = ROOT / "tests/oracles/d10_clos_method_class.lisp"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_static():
    manifest = read(MANIFEST)
    foundation = read(FOUNDATION)
    inventory = read(INVENTORY)
    state = read(STATE)

    assert manifest["schema"] == "d10-clos-method-class-observation/v1"
    assert manifest["status"] == "HISTORICAL-DONOR-ORACLE-RESEARCH-ONLY"
    assert set(manifest["source_urls"]) == {"FIND-METHOD", "REMOVE-METHOD", "CHANGE-CLASS"}
    assert len(manifest["functions"]) == 3
    assert {r["name"] for r in manifest["functions"]} == set(manifest["source_urls"])
    for row in manifest["functions"]:
        assert manifest["source_urls"][row["name"]].startswith("https://")
        assert row["law"].strip() and row["positive_witness"].strip()
        assert len(row["falsifiers"]) >= 2 and all(s.strip() for s in row["falsifiers"])
    assert manifest["boundary"] == {
        "changes_inventory": False,
        "assigns_coordinate": False,
        "ratifies_d10": False,
        "authorizes_physical_t5": False,
        "selected_count_at_creation_is_historical_snapshot_only": True,
    }

    assert len(inventory["rows"]) == inventory["accounting"]["selected_semantic_candidates"]
    assert state["target"]["selected_semantic_candidates"] == len(inventory["rows"])
    assert state["target"]["remaining_semantic_candidates"] == 1024 - len(inventory["rows"])
    assert inventory["accounting"]["remaining_semantic_inventory"] == 1024 - len(inventory["rows"])
    assert len(inventory["rows"]) >= manifest["selected_count_at_creation"]
    assert inventory["width"] == 10 and inventory["capacity"] == 1024
    assert state["target"]["domain"] == "D10"

    lower = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain.get("residents", {}).values()
    }
    names = set(manifest["source_urls"])
    assert not names.intersection(lower), "CLOS donor names collided with ratified D1-D9"
    # A candidate may be selected by a serialized peer PR after this oracle was
    # authored. Such selection does not invalidate the independent source oracle.
    selected = {row["semantic_name"].upper(): row for row in inventory["rows"]}
    selected_names = names.intersection(selected)
    for name in selected_names:
        assert selected[name]["ratified_resident"] is False, (
            "oracle dossier is not a license to ratify " + name
        )

    source = SOURCE.read_text(encoding="utf-8")
    observed = re.findall(r'\(d10-method-class-observe\s+"([A-Z0-9_]+)"', source)
    assert observed == manifest["observed_case_ids"], "Lisp assertions differ from pinned manifest"
    assert len(observed) == 23 and len(set(observed)) == 23
    return manifest, selected_names


def run_oracle(sbcl: str, manifest: dict):
    result = subprocess.run(
        [sbcl, "--script", str(SOURCE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"SBCL donor oracle exit {result.returncode}:\n{result.stdout}\n{result.stderr}"
        )
    observed = []
    summaries = []
    for line in result.stdout.strip().splitlines():
        if line.startswith("OBS\t"):
            parts = line.split("\t")
            assert len(parts) == 3 and parts[2] == "PASS", f"bad oracle row: {line}"
            observed.append(parts[1])
        elif line.startswith("SUMMARY\t"):
            summaries.append(line)
        elif line.strip():
            raise AssertionError(f"unrecognized donor output: {line}")
    assert observed == manifest["observed_case_ids"], "incomplete/reordered donor observations"
    assert summaries == [f"SUMMARY\tD10-CLOS-METHOD-CLASS-ORACLE-V1\t{len(observed)}"]
    print(f"D10 CLOS method/class donor oracle: PASS {len(observed)}/{len(observed)}")
    print("SENS runtime parity: NOT TESTED; inventory additions: 0; coordinate assignments: 0")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--sbcl", default="sbcl")
    args = parser.parse_args()
    manifest, selected = verify_static()
    print(
        "D10 CLOS method/class provenance and live-count-tolerant dedup: PASS; "
        f"currently-selected-peer-names={','.join(sorted(selected)) or 'none'}"
    )
    if not args.static_only:
        run_oracle(args.sbcl, manifest)


if __name__ == "__main__":
    main()
