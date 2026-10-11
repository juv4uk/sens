#!/usr/bin/env python3
"""Повний read-only аудит refs: що вже в main, а що потребує перенесення.

НІКОЛИ не створює Git-гілок, PR, комітів і не видаляє refs.
Перед запуском у CI отримати всі гілки:
  git fetch --no-tags origin '+refs/heads/*:refs/remotes/origin/*'
  python3 scripts/audit_historical_branches.py --output /tmp/sens-branches.jsonl

ALREADY_ANCESTOR: історія гілки досяжна з main.
TREE_IDENTICAL: поточний вміст ідентичний main, проте не вся історія досяжна.
UNMERGED: коміти або вміст відрізняються; потрібні dedup і semantic review.
ERROR: Git не довів статус; блокувати автоматичну класифікацію.
"""
from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, errors="replace",
    )


def required(root: Path, *args: str) -> str:
    p = git(root, *args)
    if p.returncode != 0:
        raise RuntimeError(
            f"git {args[0]} failed ({p.returncode}): {p.stderr[:600]}"
        )
    return p.stdout.rstrip("\n")


def get_refs(root: Path, remote: str) -> list[dict[str, str]]:
    # Git ref names cannot contain tabs/newlines; %09 separates all three fields.
    raw = required(
        root, "for-each-ref",
        "--format=%(refname)%09%(objectname)%09%(committerdate:iso8601-strict)",
        f"refs/remotes/{remote}/",
    )
    refs = []
    for line in raw.splitlines():
        fields = line.split("\t")
        if len(fields) != 3:
            raise RuntimeError("malformed git for-each-ref result")
        full, head, last_commit = fields
        if full == f"refs/remotes/{remote}/HEAD":
            continue
        if len(head) != 40:
            raise RuntimeError("non-full Git commit sha")
        refs.append({
            "branch": full.removeprefix(f"refs/remotes/{remote}/"),
            "head_sha": head,
            "head_commit_date": last_commit,
        })
    return sorted(refs, key=lambda x: x["branch"])


def classify(root: Path, head: str, main: str, main_tree: str) -> dict:
    ancestor = git(root, "merge-base", "--is-ancestor", head, main)
    if ancestor.returncode == 0:
        return {"status": "ALREADY_ANCESTOR", "ahead": 0, "behind": 0,
                "changed_paths_sample": []}
    if ancestor.returncode != 1:
        return {"status": "ERROR", "reason": ancestor.stderr[:350]}

    try:
        other_tree = required(root, "rev-parse", f"{head}^{{tree}}")
        revcounts = required(root, "rev-list", "--left-right", "--count", f"{main}...{head}")
        behind, ahead = map(int, revcounts.replace("\t", " ").split())
        if other_tree == main_tree:
            return {"status": "TREE_IDENTICAL", "ahead": ahead, "behind": behind,
                    "changed_paths_sample": []}
        # File inventory is an indicator only; it is not semantic dedup.
        files = required(root, "diff", "--name-only", f"{main}...{head}")
        paths = files.splitlines()
        return {"status": "UNMERGED", "ahead": ahead, "behind": behind,
                "changed_paths_count": len(paths),
                "changed_paths_sample": paths[:30]}
    except (RuntimeError, ValueError) as exc:
        return {"status": "ERROR", "reason": str(exc)[:350]}


def audit(root: Path, remote: str, limit: int) -> tuple[list[dict], dict]:
    main = required(root, "rev-parse", f"refs/remotes/{remote}/main")
    main_tree = required(root, "rev-parse", f"{main}^{{tree}}")
    refs = get_refs(root, remote)
    if not any(r["branch"] == "main" for r in refs):
        raise RuntimeError(f"{remote}/main missing; fetch all refs first")
    all_count = len(refs)
    if limit:
        refs = refs[:limit]
    # Different branch labels sharing one commit are classified once.
    cache: dict[str, dict] = {}
    rows = []
    for ref in refs:
        head = ref["head_sha"]
        if head not in cache:
            cache[head] = classify(root, head, main, main_tree)
        rows.append({**ref, **cache[head]})
    counts = collections.Counter(row["status"] for row in rows)
    summary = {
        "schema": "sens-full-branch-main-audit/v1",
        "read_only": True,
        "repository_remote": remote,
        "main_sha": main,
        "scanned_refs": len(refs),
        "available_refs": all_count,
        "distinct_branch_heads": len(cache),
        "full_scan": limit == 0,
        "statuses": dict(sorted(counts.items())),
        "interpretation": (
            "UNMERGED is not automatically an admissible Core change; "
            "review content, donor SHA, dedup, oracles and current contract."
        ),
    }
    return rows, summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if args.limit < 0:
        ap.error("--limit must be >= 0")
    try:
        rows, summary = audit(args.root.resolve(), args.remote, args.limit)
    except RuntimeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        out.write(json.dumps({"_meta": summary}, ensure_ascii=False) + "\n")
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if summary["statuses"].get("ERROR", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
