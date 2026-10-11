#!/usr/bin/env python3
"""Fail-closed triage of a pinned historical branch census; never merges Git refs."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

CENSUS_SCHEMA = "historical-merge-census/v1"
VERDICTS = {"MERGED-IN", "OBSOLETE", "ALIVE", "CONFLICT"}


def initial_verdict(item: dict) -> tuple[str, str, bool]:
    status = item["status"]
    if status == "ALREADY_INCLUDED" and item.get("ahead") == 0:
        return "MERGED-IN", "ancestor-at-census-base", True
    if (status == "CONTENT_EQUIVALENT"
            and item.get("unique_content_paths") == 0
            and item.get("ahead", 0) > 0):
        return "MERGED-IN", "blob-equal-at-census-base", True
    return "CONFLICT", "not-proven-admissible; manual-review-required", False


def make_catalog(census: dict, overrides: dict | None = None) -> dict:
    """No name-based obsolete guesses, and never auto-classify a live candidate."""
    if census.get("schema") != CENSUS_SCHEMA:
        raise ValueError("unknown census schema")
    entries = census.get("branches")
    if not isinstance(entries, list) or len(entries) != census.get("branches_count"):
        raise ValueError("census size mismatch")
    base_sha = census.get("base_sha")
    if not isinstance(base_sha, str) or len(base_sha) != 40:
        raise ValueError("invalid pinned main SHA")
    overrides = overrides or {}
    seen, rows = set(), []
    for item in entries:
        name, head = item.get("branch"), item.get("head")
        if not isinstance(name, str) or not name or name in seen:
            raise ValueError(f"missing/duplicate branch: {name!r}")
        if not isinstance(head, str) or len(head) != 40:
            raise ValueError(f"missing SHA: {name}")
        seen.add(name)
        verdict, evidence, reviewed = initial_verdict(item)
        decision = overrides.get(name)
        if decision is not None:
            if decision.get("head") != head or decision.get("main_sha") != base_sha:
                raise ValueError(f"stale decision SHA for {name}")
            if decision.get("verdict") not in VERDICTS:
                raise ValueError(f"invalid verdict for {name}")
            if not decision.get("evidence_url") or not decision.get("reviewer"):
                raise ValueError(f"missing reviewer/evidence for {name}")
            verdict = decision["verdict"]
            evidence = decision["evidence_url"]
            reviewed = True
            if verdict == "ALIVE" and (decision.get("ci") != "SUCCESS"
                                        or not decision.get("oracle_url")):
                raise ValueError(f"ALIVE without green CI/oracle: {name}")
            if verdict == "OBSOLETE" and not decision.get("current_contract_url"):
                raise ValueError(f"OBSOLETE without current contract: {name}")
        rows.append({
            "branch": name, "source_head_sha": head, "census_main_sha": base_sha,
            "recent_72h": bool(item.get("recent_72h")), "research": bool(item.get("research")),
            "ahead": item.get("ahead"), "behind": item.get("behind"),
            "census_status": item["status"], "changed_paths": item.get("examples", []),
            "verdict": verdict, "evidence": evidence, "reviewed": reviewed
        })
    if set(overrides) - seen:
        raise ValueError("decisions contain branches outside the census")
    counts = Counter(row["verdict"] for row in rows)
    unresolved = sum(not row["reviewed"] for row in rows)
    return {
        "schema": "safe-branch-sweep-triage/v1",
        "census_generated_utc": census.get("generated_utc"),
        "census_main_sha": base_sha,
        "records": len(rows), "verdict_counts": dict(counts),
        "manual_review_pending": unresolved, "admission_authorized": False,
        "warning": "Snapshot only: recheck all heads against fresh main, semantic oracles and exact-head CI before promotion.",
        "branches": rows
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-main-sha")
    parser.add_argument("--require-admissible", action="store_true")
    args = parser.parse_args()
    census = json.loads(args.census.read_text(encoding="utf-8"))
    decisions = (json.loads(args.decisions.read_text(encoding="utf-8"))
                 if args.decisions else None)
    catalog = make_catalog(census, decisions)
    if args.expected_main_sha and catalog["census_main_sha"] != args.expected_main_sha:
        raise SystemExit("BLOCK: stale census main SHA; regenerate against fresh main")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: v for k, v in catalog.items() if k != "branches"}))
    if args.require_admissible:
        raise SystemExit("BLOCK: no automated promotion; human semantic audit and current-head green CI required")


if __name__ == "__main__":
    main()
