#!/usr/bin/env python3
"""Fail-closed SENS branch-history census. Read-only. Never creates branches.

The six exact-SHA manifests live on main. This tool distinguishes:
* IN_MAIN_ANCESTRY: original head commit is an ancestor of current main;
* TREE_EQUIVALENT_NOT_ANCESTRY: same current tree, not proof of past evidence;
* NEEDS_CONTENT_REVIEW: current tree differs from main; semantic review needed;
* MISSING_SOURCE_OBJECT: exact historical SHA unavailable in local git object DB.

Use GitHub Rulesets to PREVENT new branches. CI can DETECT, not prohibit, creations.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "research" / "branch-history" / "20261011"
PARTS = ("01-08", "09-16", "17-24", "25-32", "33-40", "41-42")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def call(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)


def load_snapshot() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for n in PARTS:
        path = SOURCE_DIR / ("live-heads-pages-" + n + ".json")
        part = json.loads(path.read_text(encoding="utf-8"))
        if part["schema"] != "sens.git-branch-heads-part/v1":
            raise ValueError("Unknown schema: " + str(path))
        if part["count"] != len(part["branches"]):
            raise ValueError("Part count mismatch: " + str(path))
        rows.extend(part["branches"])
    index = json.loads((SOURCE_DIR / "index.json").read_text(encoding="utf-8"))
    if index["total_live_branch_refs"] != len(rows) or len(rows) != 4133:
        raise ValueError("Historical census incomplete")
    names = [row["name"] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate source branch names")
    if len({row["sha"] for row in rows}) != index["distinct_head_commits"]:
        raise ValueError("Distinct commit SHA count mismatch")
    if any(not SHA_RE.fullmatch(row["sha"]) for row in rows):
        raise ValueError("Malformed source commit SHA")
    return rows


def live_remote_heads() -> dict[str, str]:
    result = call("git", "ls-remote", "--heads", "origin")
    if result.returncode:
        raise RuntimeError("Cannot enumerate live origin branch refs: "
                           + result.stderr[:1000])
    live: dict[str, str] = {}
    for line in result.stdout.splitlines():
        sha, name = line.split("\t", 1)
        if not name.startswith("refs/heads/") or not SHA_RE.fullmatch(sha):
            raise ValueError("Invalid Git ref response")
        live[name.removeprefix("refs/heads/")] = sha
    return live


def git_main_sha() -> str:
    r = call("git", "rev-parse", "HEAD")
    if r.returncode or not SHA_RE.fullmatch(r.stdout.strip()):
        raise RuntimeError("Cannot identify exact HEAD of main")
    return r.stdout.strip()


def classify_snapshot(rows: list[dict[str, str]], current_main: str) -> list[dict[str, str]]:
    classifications: list[dict[str, str]] = []
    unique_shas: dict[str, str] = {}
    for row in rows:
        sha = row["sha"]
        if sha not in unique_shas:
            present = call("git", "cat-file", "-e", sha + "^{commit}")
            if present.returncode:
                state = "MISSING_SOURCE_OBJECT"
            elif call("git", "merge-base", "--is-ancestor", sha, current_main).returncode == 0:
                state = "IN_MAIN_ANCESTRY"
            else:
                compare = call("git", "diff", "--quiet", current_main, sha, "--")
                state = ("TREE_EQUIVALENT_NOT_ANCESTRY" if compare.returncode == 0
                         else "NEEDS_CONTENT_REVIEW" if compare.returncode == 1
                         else "DIFF_ERROR")
            unique_shas[sha] = state
        classifications.append({"name": row["name"], "head_sha": sha,
                                "status": unique_shas[sha]})
    return classifications


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-new", action="store_true",
                    help="Fail if origin has newly created branches absent in the snapshot")
    ap.add_argument("--classify", action="store_true",
                    help="Read-only ancestry/tree comparison of each recorded head")
    ap.add_argument("--output", default="")
    args = ap.parse_args()
    rows = load_snapshot()
    known = {x["name"] for x in rows}
    report: dict = {
        "schema": "sens.branch-consolidation-verdicts/v1",
        "status": "AUDIT-ONLY-NOT-CONSOLIDATED",
        "snapshot_branches": len(rows),
        "snapshot_unique_commits": len({x["sha"] for x in rows}),
        "branches_created": [],
        "warning": ("Ancestry or matching file tree is not a semantic dedup verdict. "
                    "Historical deleted refs and old PRs require separate review."),
    }
    if args.check_new:
        live = live_remote_heads()
        report["live_branches"] = len(live)
        report["branches_created"] = sorted(set(live) - known)
        report["removed_since_snapshot"] = sorted(known - set(live))
    if args.classify:
        report["main_sha"] = git_main_sha()
        report["results"] = classify_snapshot(rows, report["main_sha"])
        report["counts"] = dict(Counter(x["status"] for x in report["results"]))
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("results", "removed_since_snapshot")},
                     ensure_ascii=False))
    if report["branches_created"]:
        print("FAIL: new branch creation detected; this job CANNOT prevent creation", file=sys.stderr)
        return 1
    if args.classify and any(x["status"] in ("DIFF_ERROR", "MISSING_SOURCE_OBJECT")
                             for x in report["results"]):
        print("BLOCKED: source evidence incomplete", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
