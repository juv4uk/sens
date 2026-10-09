#!/usr/bin/env python3
"""Verify D10 historical CLOS donor observations; never claims SENS runtime parity."""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/d10-clos-slot-observation-v1.json"
SOURCE = ROOT / "tests/oracles/d10_clos_slot_states.lisp"
HISTORY = ROOT / "knowledge/d10-clos-slot-state-historical-review-v1.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"
NAMES = {"SLOT-EXISTS-P", "SLOT-BOUNDP", "SLOT-MAKUNBOUND", "CLASS-OF"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_static():
    manifest, history = read(MANIFEST), read(HISTORY)
    foundation, inventory, state = read(FOUNDATION), read(INVENTORY), read(STATE)
    assert manifest["schema"] == "d10-clos-slot-observation/v1"
    assert manifest["status"] == "INDEPENDENT-DONOR-ORACLE-RESEARCH-PENDING-OWNER-REVIEW"
    assert manifest["geometry"] == {
        "coordinate": None, "coordinate_basis": "UNPLACED", "ratified": False
    }
    assert manifest["historical_functions"] and len(manifest["historical_functions"]) == 4
    assert {r["name"] for r in manifest["historical_functions"]} == NAMES
    assert len(manifest["observed_case_ids"]) == 17
    assert len(set(manifest["observed_case_ids"])) == 17
    assert manifest["oracle_path"] == str(SOURCE.relative_to(ROOT))
    assert inventory["accounting"]["selected_semantic_candidates"] == len(inventory["rows"])
    assert state["target"]["selected_semantic_candidates"] == len(inventory["rows"])
    assert state["target"]["ratified_residents"] == 0
    assert len(inventory["rows"]) >= manifest["canonical_baseline"]["selected"]
    assert manifest["canonical_baseline"] == {
        "selected": 625, "ratified": 0, "width": 10, "forced_selector_coordinates": 256
    }
    ratified_lower = {
        str(name).upper()
        for domain in foundation["domains"].values()
        for name in domain["residents"].values()
    }
    selected_upper = {r["semantic_name"].upper() for r in inventory["rows"]}
    assert not NAMES.intersection(ratified_lower), "D1-D9 already has donor spelling"
    assert not NAMES.intersection(selected_upper), "Already selected: owner review must update oracle"
    old_rows = {r["historical_name"]: r for r in history["rows"]}
    assert NAMES <= set(old_rows), "Every donor law must have merged historical provenance"
    for function in manifest["historical_functions"]:
        assert function["intake"] == "PENDING-OWNER-REVIEW"
        assert function["source_url"] == old_rows[function["name"]]["primary_url"]
        assert function["surface_uk"] == old_rows[function["name"]]["surface_uk"]
        assert function["surface_ukr"] == old_rows[function["name"]]["surface_ukr"]
        assert function["surface_uk"] and function["surface_ukr"]
    observed = re.findall(r'\(d10-observe\s+"([A-Z0-9_]+)"', SOURCE.read_text(encoding="utf-8"))
    assert observed == manifest["observed_case_ids"], "Lisp assertions differ from manifest"
    return manifest


def run_oracle(sbcl, manifest):
    result = subprocess.run(
        [sbcl, "--script", str(SOURCE)], cwd=ROOT, capture_output=True, text=True,
        timeout=90, check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Real Common Lisp donor oracle exit {result.returncode}:\n"
            f"{result.stdout}\n{result.stderr}"
        )
    observed = []
    summary = []
    for line in result.stdout.strip().splitlines():
        if line.startswith("OBS\t"):
            parts = line.split("\t")
            assert len(parts) == 3 and parts[2] == "PASS", f"bad oracle row: {line}"
            observed.append(parts[1])
        elif line.startswith("SUMMARY\t"):
            summary.append(line)
        elif line.strip():
            raise AssertionError(f"unrecognized donor output: {line}")
    assert observed == manifest["observed_case_ids"], "incomplete/reordered donor observations"
    assert summary == [f"SUMMARY\tD10-CLOS-SLOT-ORACLE-V1\t{len(observed)}"]
    print(f"D10 CLOS independent donor SBCL oracle: PASS {len(observed)}/{len(observed)}")
    print("SENS implementation parity: NOT TESTED; selected additions: 0; ratified: 0")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--sbcl", default="sbcl")
    args = parser.parse_args()
    manifest = verify_static()
    print("D10 CLOS oracle provenance, law set and dedup: PASS")
    if not args.static_only:
        run_oracle(args.sbcl, manifest)


if __name__ == "__main__":
    main()
