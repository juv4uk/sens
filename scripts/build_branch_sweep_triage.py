#!/usr/bin/env python3
"""Fail-closed full branch triage: produces evidence only, never writes git refs."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re

VERDICTS = {"MERGED-IN", "OBSOLETE", "ALIVE", "CONFLICT"}
MERGED = {"ALREADY_INCLUDED", "CONTENT_EQUIVALENT"}
CONFLICT = {"CONFLICT_REBASE", "REVIEW_UNRELATED"}
EVIDENCE = re.compile(r"^https://github\.com/juv4uk/[\w.-]+/(?:issues|pull|commit|actions)/")
RISK = ("truth", "equal", "eq-", "structural", "ontology", "predicate",
        "cond", "retire", "sid8", "sens8", "d10", "canon")


def review_is_valid(review: dict, row: dict) -> None:
    verdict, reason, url = (review.get(k) for k in ("verdict", "reason", "evidence_url"))
    if verdict not in VERDICTS or not isinstance(reason, str) or len(reason.strip()) < 20:
        raise ValueError("Reviewed verdict requires a substantive reason")
    if not isinstance(url, str) or not EVIDENCE.match(url):
        raise ValueError("Reviewed verdict requires GitHub evidence link")
    if review.get("head_sha") != row.get("head"):
        raise ValueError("Evidence stale: branch head SHA changed")
    if verdict == "ALIVE":
        if row.get("status") != "MERGEABLE_NEEDS_CI":
            raise ValueError("ALIVE only allowed after clean merge-tree analysis")
        if not all(review.get(k) for k in
                   ("semantic_contract_reviewed", "oracle_reviewed", "current_head_ci_green")):
            raise ValueError("ALIVE requires semantic review, oracle and green CI")
        if not EVIDENCE.match(str(review.get("ci_url", ""))):
            raise ValueError("ALIVE requires exact GitHub CI run")
    if verdict == "MERGED-IN" and row.get("ahead", 1) != 0 and not review.get("content_equivalence_verified"):
        raise ValueError("MERGED-IN with ahead commits requires content equivalence proof")


def build(census: dict, reviews: dict) -> dict:
    if census.get("schema") != "historical-merge-census/v1":
        raise ValueError("Unsupported census")
    refs = census.get("branches", [])
    if len(refs) != census.get("branches_count") or not isinstance(reviews, dict):
        raise ValueError("Census/reviews malformed")
    seen, rows = set(), []
    for item in refs:
        branch = item.get("branch")
        if not branch or branch in seen:
            raise ValueError(f"Duplicate/missing branch: {branch}")
        seen.add(branch)
        status = item.get("status")
        candidate = bool(item.get("recent_72h") or item.get("research") or
                         status == "MERGEABLE_NEEDS_CI")
        if status in MERGED:
            verdict, reason = "MERGED-IN", f"Git census: {status}"
        elif status in CONFLICT:
            verdict, reason = "CONFLICT", f"Git census: {status}; replay separately"
        else:
            verdict, reason = "HOLD", "Pending semantic, oracle and CI verification"
        evidence = ""
        if branch in reviews:
            review_is_valid(reviews[branch], item)
            verdict = reviews[branch]["verdict"]
            reason = reviews[branch]["reason"]
            evidence = reviews[branch]["evidence_url"]
        affected = item.get("examples", [])
        rows.append({
            "branch": branch, "head_sha": item.get("head", ""), "base_sha": census["base_sha"],
            "last_commit_utc": item.get("latest_commit_utc", ""),
            "recent_72h": bool(item.get("recent_72h")), "research": bool(item.get("research")),
            "candidate": candidate, "status": status, "ahead": item.get("ahead"),
            "behind": item.get("behind"), "verdict": verdict, "reason": reason,
            "evidence_url": evidence, "unique_paths": item.get("unique_content_paths"),
            "path_examples": affected, "semantic_risk": any(
                term in value.lower() for term in RISK for value in [branch, *affected]),
        })
    unknown = sorted(set(reviews) - seen)
    if unknown:
        raise ValueError(f"Review refers to vanished branches: {unknown[:5]}")
    selected = [r for r in rows if r["candidate"]]
    counts = dict(Counter(row["verdict"] for row in selected))
    ready = bool(selected) and all(
        row["verdict"] in ("MERGED-IN", "OBSOLETE", "ALIVE") for row in selected)
    return {"schema": "safe-branch-sweep-triage/v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "base_sha": census["base_sha"],
            "census_generated_utc": census.get("generated_utc"),
            "branches_count": len(rows), "candidate_count": len(selected),
            "candidate_verdict_counts": counts,
            "semantic_risk_open": sum(r["candidate"] and r["semantic_risk"] and
                                      r["verdict"] not in ("MERGED-IN", "OBSOLETE") for r in rows),
            "ready_for_final_review": ready, "main_merge_authorized": False,
            "warning": "HOLD is not ALIVE; no CI skipping, implicit semantics or automatic merge.",
            "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--overrides", type=Path,
                        default=Path("docs/merge/branch-sweep-overrides-20261009.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("artifacts/branch-sweep-triage-20261009.json"))
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    census = json.loads(args.census.read_text(encoding="utf-8"))
    overrides = json.loads(args.overrides.read_text(encoding="utf-8")) if args.overrides.exists() else {}
    outcome = build(census, overrides)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outcome, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = ["branch", "head_sha", "base_sha", "candidate", "recent_72h", "research",
              "status", "ahead", "behind", "verdict", "semantic_risk", "reason", "evidence_url"]
    with args.output.with_suffix(".tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", delimiter="\t")
        writer.writeheader()
        writer.writerows(outcome["rows"])
    print(json.dumps({k: v for k, v in outcome.items() if k != "rows"}, ensure_ascii=False))
    if args.require_ready and not outcome["ready_for_final_review"]:
        raise SystemExit("NO MERGE: unresolved HOLD/CONFLICT in candidate catalog")


if __name__ == "__main__":
    main()
