#!/usr/bin/env python3
"""Fail-closed validator for an archival Lisp 1.5 provenance ledger.

The ledger may preserve historical coordinates only under an explicitly historical
field. It cannot select/ratify any current D8/D10 identity.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from d10_historical_snapshot_compat import pinned_inventory_git_blob

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "knowledge/lisp15-appendix-a-provenance-v1.json"
FOUNDATION_PATH = ROOT / "knowledge/d1-d9-foundation.json"
D8_PATH = ROOT / "knowledge/d8-ratified.json"
D10_PATH = ROOT / "knowledge/d10-v1-semantic-inventory.json"


def fail(message: str) -> None:
    raise ValueError(message)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(name: object) -> str:
    return re.sub(r"[^A-Z0-9?!+*/<>=.-]", "", str(name).strip().upper())


def git_blob_sha(path: Path) -> str:
    if path == D10_PATH:
        return pinned_inventory_git_blob(path)
    rel = str(path.relative_to(ROOT))
    try:
        result = subprocess.run(
            ["git", "rev-parse", f"HEAD:{rel}"],
            cwd=ROOT, check=True, capture_output=True, text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        fail(f"cannot resolve authority blob SHA for {rel}: {exc}")
    return result.stdout.strip()


def build_lower_names(foundation):
    result = {}
    for domain, spec in foundation["domains"].items():
        for name in spec.get("residents", {}).values():
            key = normalize(name)
            if key:
                result.setdefault(key, set()).add(domain)
    return result


def build_d10_names(inventory):
    result = {}
    for row in inventory["rows"]:
        key = normalize(row.get("semantic_name", ""))
        if key:
            result.setdefault(key, []).append(row)
    return result


def validate(data, foundation, d8, inventory):
    errors = []
    if data.get("schema") != "lisp15-appendix-a-provenance/v1":
        errors.append("wrong schema")
    if data.get("status") != "HISTORICAL-PROVENANCE-ONLY-REQUIRES-BEHAVIORAL-REVIEW":
        errors.append("artifact is not explicitly archival")
    auth = data.get("current_authority_snapshot", {})
    for key, path in (
        ("d1_d9_foundation_blob_sha", FOUNDATION_PATH),
        ("d8_ratified_blob_sha", D8_PATH),
        ("d10_inventory_blob_sha", D10_PATH),
    ):
        actual = git_blob_sha(path)
        if auth.get(key) != actual:
            errors.append(f"{key} is stale: recorded={auth.get(key)} current={actual}")
    if d8.get("status") != "owner-ratified" or d8.get("occupancy") != 256:
        errors.append("current D8 is not the expected owner-ratified 256/256 basis")
    accounting = data.get("current_exact_name_dedup", {})
    if accounting.get("rule") != "Normalized exact-name scan only; it is not proof of semantic equivalence or novelty.":
        errors.append("missing exact-name-only disclaimer")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != 30:
        errors.append("expected exactly 30 historical families")
        return errors
    fams = [row.get("family") for row in rows]
    if len(fams) != len(set(fams)):
        errors.append("duplicate family key")
    lower_names = build_lower_names(foundation)
    d10_names = build_d10_names(inventory)
    lower_families = d10_families = both_families = neither_families = 0
    for row in rows:
        family = row.get("family", "<missing-family>")
        names = row.get("names")
        if not isinstance(names, list) or not names:
            errors.append(f"{family}: names must be a non-empty list")
            continue
        if row.get("coordinate", "MISSING") is not None:
            errors.append(f"{family}: current coordinate must be null")
        if row.get("selected_d10_candidate") is not False:
            errors.append(f"{family}: selected_d10_candidate must be false")
        if row.get("ratified") is not False:
            errors.append(f"{family}: ratified must be false")
        hist = row.get("historical_snapshot", {})
        if "provisional_coordinates_before_D8_ratification" not in hist:
            errors.append(f"{family}: historical coordinates must be explicitly historical")
        matches = row.get("current_exact_name_matches", {})
        exp_lower = {normalize(entry.get("name")) for entry in matches.get("d1_d9", [])}
        act_lower = {normalize(n) for n in names if normalize(n) in lower_names}
        if exp_lower != act_lower:
            errors.append(f"{family}: D1-D9 exact-name matches drifted")
        for entry in matches.get("d1_d9", []):
            domains = set(entry.get("domains", []))
            if domains != lower_names.get(normalize(entry.get("name")), set()):
                errors.append(f"{family}: domain list stale for {entry.get('name')}")
        exp_d10 = {normalize(entry.get("name")) for entry in matches.get("d10_selected", [])}
        act_d10 = {normalize(n) for n in names if normalize(n) in d10_names}
        if exp_d10 != act_d10:
            errors.append(f"{family}: D10 exact-name matches drifted")
        for entry in matches.get("d10_selected", []):
            if not any(r.get("stable_id") == entry.get("stable_id") for r in d10_names.get(normalize(entry.get("name")), [])):
                errors.append(f"{family}: D10 selected row identity is stale for {entry.get('name')}")
        has_lower = bool(act_lower)
        has_d10 = bool(act_d10)
        lower_families += int(has_lower)
        d10_families += int(has_d10)
        both_families += int(has_lower and has_d10)
        neither_families += int(not has_lower and not has_d10)
        expected_unmatched = {
            normalize(n) for n in names if normalize(n) not in lower_names and normalize(n) not in d10_names
        }
        actual_unmatched = {normalize(n) for n in row.get("unmatched_names_needing_review", [])}
        if expected_unmatched != actual_unmatched:
            errors.append(f"{family}: unmatched name list drifted")
        if not row.get("behavior") or not row.get("law_hypothesis"):
            errors.append(f"{family}: missing historical behavior/law provenance")
        if not row.get("evidence"):
            errors.append(f"{family}: missing historical evidence references")
    expected_summary = {
        "families_with_d1_d9_name_overlap": lower_families,
        "families_with_selected_d10_name_overlap": d10_families,
        "families_with_both_overlap_types": both_families,
        "families_with_no_exact_name_overlap_to_either": neither_families,
        "families_with_any_overlap": len(rows) - neither_families,
    }
    for key, value in expected_summary.items():
        if accounting.get(key) != value:
            errors.append(f"summary {key} stale: expected {value}, got {accounting.get(key)}")
    return errors


def main() -> int:
    data = load(ARTIFACT)
    foundation = load(FOUNDATION_PATH)
    d8 = load(D8_PATH)
    inventory = load(D10_PATH)
    errors = validate(data, foundation, d8, inventory)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("LISP 1.5 Appendix A archival provenance: 30 families, current dedup, no selection/coordinate/ratification PASS")
    if "--self-test" in sys.argv:
        bads = []
        mutations = []
        wrong_coord = copy.deepcopy(data)
        wrong_coord["rows"][0]["coordinate"] = "00000000"
        mutations.append(("current coordinate", wrong_coord))
        wrong_select = copy.deepcopy(data)
        wrong_select["rows"][0]["selected_d10_candidate"] = True
        mutations.append(("selected candidate", wrong_select))
        wrong_ratify = copy.deepcopy(data)
        wrong_ratify["rows"][0]["ratified"] = True
        mutations.append(("ratified candidate", wrong_ratify))
        wrong_dedup = copy.deepcopy(data)
        wrong_dedup["rows"][0]["current_exact_name_matches"]["d1_d9"] = []
        mutations.append(("dedup drift", wrong_dedup))
        for name, mutated in mutations:
            if not validate(mutated, foundation, d8, inventory):
                bads.append(name)
        if bads:
            print("FAIL: negative controls were accepted: " + ", ".join(bads), file=sys.stderr)
            return 1
        print("4 negative admission/dedup controls: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
