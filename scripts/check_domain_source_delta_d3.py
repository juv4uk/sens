#!/usr/bin/env python3
"""Fail-closed D3 semantic regression guard for all modified active Lisp sources.

Checks introduced malformed D3 COND, host truth, and incorrect ATOM/EQ
arity. A change is reviewed regardless of whether its earlier source used
any retired historical function identity. This is not runtime parity proof.
"""
from __future__ import annotations
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_d3_legacy_logic.py"
SPEC = importlib.util.spec_from_file_location("sens_d3_delta_guard", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("canonical D3 scanner missing")
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)

SEMANTIC = {"COND_NOT_TWO_FIELDS", "COND_HOST_TRUTH", "D3_WRONG_ARITY"}


def newly_introduced(before: str, after: str, path: str) -> dict:
    old = Counter((f.rule, f.operation, f.detail) for f in guard.scan_lisp(before, path)
                  if f.rule in SEMANTIC)
    new = Counter((f.rule, f.operation, f.detail) for f in guard.scan_lisp(after, path)
                  if f.rule in SEMANTIC)
    delta = new - old
    return {
        "path": path,
        "before_semantic_findings": sum(old.values()),
        "after_semantic_findings": sum(new.values()),
        "introduced": [{"rule": key[0], "operation": key[1], "detail": key[2],
                         "count": count} for key, count in sorted(delta.items())],
    }


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args],
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("git " + " ".join(args) + ": " +
                           result.stderr.decode(errors="replace")[:400])
    return result.stdout


def audit(root: Path, base: str, head: str) -> dict:
    paths = git(root, "diff", "--name-only", "--diff-filter=M", "-z",
                base, head, "--", "*.lisp").split(b"\0")
    reviewed, skipped, errors = [], [], []
    for raw in paths:
        if not raw:
            continue
        path = raw.decode("utf-8")
        if path.startswith(("research/", "docs/", "tests/fixtures/",
                            "knowledge/d10-source-snapshots/", "lib/generated/")):
            skipped.append(path)
            continue
        before = git(root, "show", base + ":" + path).decode("utf-8")
        after = git(root, "show", head + ":" + path).decode("utf-8")
        try:
            item = newly_introduced(before, after, path)
        except (guard.Unscannable, RecursionError, UnicodeError) as e:
            errors.append({"path": path, "reason": "incomplete D3 parsing: " + str(e)})
            continue
        reviewed.append(item)
    total = sum(sum(item["count"] for item in r["introduced"]) for r in reviewed)
    return {"schema": "domain-source-d3-delta/v2",
            "status": "BLOCKED" if total or errors else "PASS",
            "semantic_regressions": total, "parse_errors": errors,
            "reviewed": reviewed, "skipped": skipped,
            "scope": "all modified active .lisp files",
            "admission": "D3 delta only; not a full runtime/parity proof"}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="HEAD^")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    try:
        result = audit(args.root.resolve(), args.base, args.head)
    except (RuntimeError, UnicodeError, OSError) as e:
        result = {"schema": "domain-source-d3-delta/v2", "status": "BLOCKED",
                  "semantic_regressions": 0, "parse_errors": [{"reason": str(e)}]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["status"] == "PASS" else 1)
