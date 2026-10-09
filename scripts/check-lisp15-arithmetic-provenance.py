#!/usr/bin/env python3
"""Fail-closed archive guard for Lisp 1.5 arithmetic provenance."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from check_d10_historical_admission_batch1 import check_growth, read as read_growth, BASE as GROWTH_BASE

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "knowledge/lisp15-arithmetic-history-provenance-v1.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"


def norm(value):
    return re.sub(r"[^A-Z0-9?!+*/<>=.-]", "", str(value).strip().upper())


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    rel = str(path.relative_to(ROOT))
    return subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, check=True,
        capture_output=True, text=True
    ).stdout.strip()


def validate(data, foundation, inventory):
    errors = []
    if data.get("schema") != "lisp15-arithmetic-history-provenance/v1":
        errors.append("wrong schema")
    snap = data.get("current_authority_snapshot", {})
    for field, path in (
        ("d1_d9_foundation_blob_sha", FOUNDATION),
        ("d10_inventory_blob_sha", INVENTORY),
    ):
        if field == "d10_inventory_blob_sha":
            if snap.get(field) != read_growth(GROWTH_BASE)["origin_inventory_git_blob"]:
                errors.append("historical D10 origin hash drift")
            try: check_growth(inventory)
            except AssertionError: errors.append("current D10 mutated protected historical 625 laws")
        else:
            actual = sha(path)
            if snap.get(field) != actual:
                errors.append(f"stale authority hash: {field}")
    if data.get("status") != "HISTORICAL-NUMERIC-PROVENANCE-ONLY":
        errors.append("status must remain archival-only")
    low = {}
    for dom, spec in foundation["domains"].items():
        for name in spec.get("residents", {}).values():
            low.setdefault(norm(name), []).append(dom)
    high = {}
    for row in inventory["rows"]:
        high.setdefault(norm(row.get("semantic_name")), []).append(row)
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != 26:
        errors.append("expected 26 historical numeric rows")
        return errors
    if len({r.get("history_id") for r in rows}) != 26:
        errors.append("history IDs must be unique")
    if len({norm(r.get("historical_name")) for r in rows}) != 26:
        errors.append("historical names must be unique")
    lo_count = hi_count = neither = 0
    for row in rows:
        name = norm(row.get("historical_name"))
        lm = row.get("current_d1_d9_exact_name_matches", [])
        hm = row.get("current_d10_exact_name_matches", [])
        if {norm(m.get("semantic_name")) for m in lm} != ({name} if name in low else set()):
            errors.append(f"{name}: D1-D9 exact-name drift")
        if {norm(m.get("semantic_name")) for m in hm} != ({name} if name in high else set()):
            errors.append(f"{name}: D10 exact-name drift")
        if row.get("selected_d10_candidate") is not False:
            errors.append(f"{name}: must not select D10")
        if row.get("coordinate", "MISSING") is not None:
            errors.append(f"{name}: coordinate must be null")
        if row.get("ratified") is not False:
            errors.append(f"{name}: ratification must be false")
        if not row.get("historical_behavior") or not row.get("historical_partiality"):
            errors.append(f"{name}: missing historical behavior/partiality evidence")
        if lm:
            lo_count += 1
        if hm:
            hi_count += 1
        if not lm and not hm:
            neither += 1
    accounting = data.get("current_exact_name_dedup", {})
    if accounting.get("families_with_d1_d9_exact_name_overlap") != lo_count:
        errors.append("D1-D9 overlap summary drift")
    if accounting.get("families_with_d10_exact_name_overlap") != hi_count:
        errors.append("D10 overlap summary drift")
    if accounting.get("families_with_no_exact_name_overlap_to_either") != neither:
        errors.append("no-overlap summary drift")
    return errors


def main():
    data = load(ARTIFACT)
    foundation = load(FOUNDATION)
    inventory = load(INVENTORY)
    errors = validate(data, foundation, inventory)
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("LISP 1.5 arithmetic historical provenance: 26 rows, current dedup, no D10 admission PASS")
    if "--self-test" in sys.argv:
        cases = []
        for field, value in (("selected_d10_candidate", True), ("coordinate", "010101"), ("ratified", True)):
            bad = copy.deepcopy(data)
            bad["rows"][0][field] = value
            cases.append((field, bad))
        failures = [name for name, bad in cases if not validate(bad, foundation, inventory)]
        if failures:
            print("FAIL: negative controls accepted: " + ", ".join(failures), file=sys.stderr)
            return 1
        print("3 negative admission controls: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
