#!/usr/bin/env python3
"""Read-only all-ref census: no merging, checkout, force push or branch deletion."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess


def git(*args: str, timeout: int = 45, check: bool = True):
    result = subprocess.run(["git", *args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f"git {args[:3]}: {result.stderr[:400]!r}")
    return result


def blob(ref: str, path: str):
    result = git("rev-parse", "--verify", f"{ref}:{path}", check=False)
    return result.stdout.decode().strip() if result.returncode == 0 else None


def classify(main: str, branch: str, now: datetime, max_paths: int) -> dict:
    name = branch.removeprefix("origin/")
    commit_time = int(git("log", "-1", "--format=%ct", branch).stdout)
    latest = datetime.fromtimestamp(commit_time, timezone.utc)
    result = {
        "branch": name,
        "head": git("rev-parse", branch).stdout.decode().strip(),
        "latest_commit_utc": latest.isoformat(),
        "recent_72h": latest >= now - timedelta(hours=72),
        "research": name.lower().startswith(("research/", "experiment/", "experiments/", "proof/"))
                    or "/research/" in name.lower(),
    }
    divergence = git("rev-list", "--left-right", "--count", f"{main}...{branch}",
                     check=False)
    if divergence.returncode:
        return {**result, "status": "REVIEW_UNRELATED"}
    behind, ahead = map(int, divergence.stdout.split())
    result.update(ahead=ahead, behind=behind)
    if ahead == 0:
        return {**result, "status": "ALREADY_INCLUDED"}
    base = git("merge-base", main, branch, check=False)
    if base.returncode:
        return {**result, "status": "REVIEW_UNRELATED"}
    fork = base.stdout.decode().strip()
    paths = git("diff", "--name-only", "-z", fork, branch).stdout.decode(
        "utf-8", errors="surrogateescape").split("\0")
    paths = [path for path in paths if path]
    result["branch_modified_paths"] = len(paths)
    if len(paths) > max_paths:
        return {**result, "status": "REVIEW_TOO_LARGE"}
    different = [path for path in paths if blob(main, path) != blob(branch, path)]
    result["unique_content_paths"] = len(different)
    result["examples"] = different[:12]
    if not different:
        return {**result, "status": "CONTENT_EQUIVALENT"}
    try:
        merge = git("merge-tree", "--write-tree", main, branch,
                    check=False, timeout=30)
    except subprocess.TimeoutExpired:
        return {**result, "status": "REVIEW_TIMEOUT"}
    if merge.returncode == 0:
        return {**result, "status": "MERGEABLE_NEEDS_CI"}
    if merge.returncode == 1:
        return {**result, "status": "CONFLICT_REBASE"}
    return {**result, "status": "REVIEW_ERROR",
            "reason": merge.stderr.decode(errors="replace")[-300:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--output", type=Path,
                        default=Path("artifacts/historical-branch-merge-census.json"))
    parser.add_argument("--max-paths", type=int, default=300)
    args = parser.parse_args()
    git("rev-parse", "--verify", args.main_ref)
    now = datetime.now(timezone.utc)
    refs = git("for-each-ref", "--format=%(refname:short)",
               "refs/remotes/origin/").stdout.decode().splitlines()
    branches = sorted(ref for ref in refs
                      if ref not in ("origin/HEAD", args.main_ref))
    records = []
    for ref in branches:
        try:
            records.append(classify(args.main_ref, ref, now, args.max_paths))
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            records.append({"branch": ref.removeprefix("origin/"),
                            "status": "REVIEW_ERROR", "reason": str(exc)[:240]})
    records.sort(key=lambda item: (not item.get("recent_72h", False),
                                   not item.get("research", False),
                                   item["branch"]))
    result = {
        "schema": "historical-merge-census/v1",
        "generated_utc": now.isoformat(),
        "base_ref": args.main_ref,
        "base_sha": git("rev-parse", args.main_ref).stdout.decode().strip(),
        "branches_count": len(records),
        "recent_72h_count": sum(bool(x.get("recent_72h")) for x in records),
        "research_count": sum(bool(x.get("research")) for x in records),
        "statuses": dict(Counter(x["status"] for x in records)),
        "warning": "A clean Git tree merge is not CI approval. Single-writer, current-head required checks and review remain mandatory.",
        "branches": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "branches"},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
