#!/usr/bin/env python3
"""Fail-closed archive guard for the early Lisp post-D4 ingest ledger."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from check_d10_historical_admission_batch1 import check_growth, read as read_growth, BASE as GROWTH_BASE

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "knowledge/early-lisp-post-d4-history-provenance-v1.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"


def norm(value):
    return re.sub(r"[^A-Z0-9?!+*/<>=.-]", "", str(value).strip().upper())


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    rel = str(path.relative_to(ROOT))
    return subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, check=True,
        capture_output=True, text=True
    ).stdout.strip()


def validate(data, foundation, inventory):
    errors = []
    if data.get("schema") != "early-lisp-post-d4-history-provenance/v1":
        errors.append("wrong schema")
    if data.get("status") != "HISTORICAL-INGEST-PROVENANCE-ONLY":
        errors.append("artifact must remain provenance-only")
    snapshot = data.get("current_authority_snapshot", {})
    for key, path in (("d1_d9_foundation_blob_sha", FOUNDATION), ("d10_inventory_blob_sha", INVENTORY)):
        if key == "d10_inventory_blob_sha":
            if snapshot.get(key) != read_growth(GROWTH_BASE)["origin_inventory_git_blob"]:
                errors.append("historical D10 origin hash drift")
            try: check_growth(inventory)
            except AssertionError: errors.append("current D10 mutated protected historical 625 laws")
        elif snapshot.get(key) != blob_sha(path):
            errors.append(f"stale authority hash: {key}")
    lower = {}
    for domain, spec in foundation["domains"].items():
        for name in spec.get("residents", {}).values():
            lower.setdefault(norm(name), []).append(domain)
    high = {}
    for row in inventory["rows"]:
        high.setdefault(norm(row.get("semantic_name")), []).append(row)
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != 19:
        errors.append("expected 19 historical operations")
        return errors
    if len({r.get("history_id") for r in rows}) != 19:
        errors.append("history IDs must be unique")
    if len({norm(r.get("historical_operation")) for r in rows}) != 19:
        errors.append("historical operation names must be unique")
    lo_count = hi_count = both_count = neither_count = 0
    for row in rows:
        name = norm(row.get("historical_operation"))
        if not row.get("original_snapshot", {}).get("binary_object"):
            errors.append(f"{name}: missing historic placement claim")
        if row.get("coordinate", "MISSING") is not None:
            errors.append(f"{name}: current coordinate must be null")
        if row.get("selected_d10_candidate") is not False:
            errors.append(f"{name}: must not be selected into D10")
        if row.get("ratified") is not False:
            errors.append(f"{name}: must not be ratified")
        lm = row.get("current_d1_d9_exact_name_matches", [])
        hm = row.get("current_d10_exact_name_matches", [])
        exp_l = {norm(v.get("semantic_name")) for v in lm}
        exp_h = {norm(v.get("semantic_name")) for v in hm}
        act_l = {name} if name in lower else set()
        act_h = {name} if name in high else set()
        if exp_l != act_l:
            errors.append(f"{name}: current D1-D9 overlap drift")
        if exp_h != act_h:
            errors.append(f"{name}: current D10 overlap drift")
        for match in lm:
            if set(match.get("domain", "").split(",")) - set(lower.get(name, [])):
                errors.append(f"{name}: D1-D9 domains contain invalid value")
        lo_count += bool(act_l)
        hi_count += bool(act_h)
        both_count += bool(act_l and act_h)
        neither_count += bool(not act_l and not act_h)
        if not row.get("historical_behavior") or not row.get("source_provenance"):
            errors.append(f"{name}: missing behavior/source provenance")
    a = data.get("current_exact_name_dedup", {})
    expected = {
        "families_with_d1_d9_exact_name_overlap": lo_count,
        "families_with_selected_d10_exact_name_overlap": hi_count,
        "families_with_both_overlap_types": both_count,
        "families_with_no_exact_name_overlap_to_either": neither_count,
        "families_with_any_overlap": len(rows) - neither_count
    }
    for key, value in expected.items():
        if a.get(key) != value:
            errors.append(f"summary drift: {key}")
    return errors


def main():
    data, foundation, inventory = load(ARTIFACT), load(FOUNDATION), load(INVENTORY)
    errors = validate(data, foundation, inventory)
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print("Early Lisp historical ledger: 19 rows, current D1-D9/D10 dedup, no admission PASS")
    if "--self-test" in sys.argv:
        cases = []
        for field, value in (("coordinate", "10101"), ("selected_d10_candidate", True), ("ratified", True)):
            bad = copy.deepcopy(data)
            bad["rows"][0][field] = value
            cases.append((field, bad))
        failures = [label for label, bad in cases if not validate(bad, foundation, inventory)]
        if failures:
            print("FAIL: negative controls accepted: " + ", ".join(failures), file=sys.stderr)
            return 1
        print("3 negative admission controls: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
