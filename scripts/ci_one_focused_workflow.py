#!/usr/bin/env python3
"""Select one topical check on main push; never define SENS semantics."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
ON = re.compile(r"^['\"]?on['\"]?:\s*(.*)$")
EVENT = re.compile(r"^  ([\w-]+):")
FORBIDDEN = {"pull_request", "pull_request_target", "merge_group",
             "workflow_run", "check_run", "check_suite"}


def events(source):
    lines = source.splitlines()
    for i, line in enumerate(lines):
        match = ON.match(line)
        if not match:
            continue
        tail = match.group(1).split(" #", 1)[0].strip()
        if tail.startswith("[") and tail.endswith("]"):
            return {x.strip().strip("'\""): "" for x in tail[1:-1].split(",") if x.strip()}
        if tail:
            if re.fullmatch(r"[\w-]+", tail):
                return {tail: ""}
            raise ValueError("unsupported inline event syntax")
        result = {}
        current = None
        for row in lines[i + 1:]:
            if row.strip() and not row[0].isspace() and not row.startswith("#"):
                break
            found = EVENT.match(row)
            if found:
                current = found.group(1)
                result[current] = row
            elif current is not None:
                result[current] += "\n" + row
        return result
    raise ValueError("missing on: event")


def verify():
    errors = []
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not paths:
        raise RuntimeError("workflow directory empty")
    on_main = []
    for path in paths:
        try:
            e = events(path.read_text(encoding="utf-8"))
            if not e:
                raise ValueError("empty events")
            forbidden = FORBIDDEN & e.keys()
            if forbidden:
                errors.append(f"{path.name}: automatic fanout: {sorted(forbidden)}")
            if "push" in e:
                body = e["push"]
                if path.name == "ci.yml" and re.search(r"^\s+branches:\s*\[main\]", body, re.M) and "tags:" not in body:
                    on_main.append(path.name)
                elif path.name == "release.yml" and "tags:" in body and "branches:" not in body:
                    pass
                else:
                    errors.append(f"{path.name}: unwanted automatic push")
        except (ValueError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    if on_main != ["ci.yml"]:
        errors.append(f"expected precisely one main-commit workflow: {on_main}")
    for item in errors:
        print("SENS_CI_BUDGET_FAIL", item, flush=True)
    if errors:
        return False
    print("SENS_CI_BUDGET_PASS", json.dumps({"workflows": len(paths), "automatic_main": 1}), flush=True)
    return True


def changed():
    before = os.getenv("SENS_CI_BEFORE", "")
    if not re.fullmatch("[0-9a-f]{40}", before) or before == "0" * 40:
        before = "HEAD^"
    probe = subprocess.run(["git", "rev-parse", "--verify", before], cwd=ROOT, capture_output=True)
    if probe.returncode:
        raise RuntimeError("unavailable before SHA; refuse invented diff")
    diff = subprocess.run(["git", "diff", "--name-only", before, "HEAD", "--"],
                          cwd=ROOT, capture_output=True, text=True)
    if diff.returncode:
        raise RuntimeError(f"diff failed: {diff.stderr}")
    files = sorted(filter(None, diff.stdout.splitlines()))
    if not files:
        raise RuntimeError("empty diff is not a topical change")
    return files


ORDER = ("ci-policy", "red-cause", "d24-math", "d7-text", "domain-tables",
         "compiler", "sens-core", "sens-program", "docs", "general")
COMMANDS = {
    "red-cause": [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                  "-p", "test_red_cause_router.py", "-v"],
    "d24-math": [sys.executable, "scripts/check-numeric-domain-ratification.py"],
    "d7-text": [sys.executable, "scripts/check-d7-runtime-projection.py"],
    "domain-tables": [sys.executable, "scripts/check-domain-tables.py"],
    "compiler": ["cargo", "test", "--locked", "-p", "sens", "--test", "compiler_role_cutover"],
    "sens-core": ["cargo", "test", "--locked", "-p", "sens", "--test",
                  "sens_semantic_witnesses", "result_status_exact_d1_binary_self_verdict", "--", "--exact"],
    "sens-program": ["cargo", "test", "--locked", "-p", "sens", "--test", "binary_only_language"],
    "docs": ["git", "diff", "--check", "HEAD^", "HEAD"],
    "general": ["git", "diff", "--check", "HEAD^", "HEAD"],
}


def classify(path):
    if path.startswith(".github/workflows/") or path in {"AGENTS.md", "scripts/ci_one_focused_workflow.py"}:
        return "ci-policy"
    if "red_cause" in path or "aged_red" in path or "red-cause" in path:
        return "red-cause"
    if any(x in path for x in ("numeric", "number-width", "domain_numeric", "D24", "d24", "ratio")):
        return "d24-math"
    if any(x in path for x in ("d7", "text7", "keyboard-v2", "w7")):
        return "d7-text"
    if path.startswith("lib/domains/") or any(x in path for x in ("domain_tables", "domain-surfaces", "domain-ladder", "domain_width")):
        return "domain-tables"
    if any(x in path for x in ("compiler", "cml", "lower.rs")):
        return "compiler"
    if path.startswith(("crates/sens/src/", "crates/sens/tests/")):
        return "sens-core"
    if path.endswith((".sens", ".lisp", ".bits")):
        return "sens-program"
    if path.startswith("docs/") or path.endswith(".md"):
        return "docs"
    return "general"


def main():
    if not verify():
        return 1
    if sys.argv[1:] != ["--execute"]:
        return 0
    paths = changed()
    scopes = {classify(path) for path in paths}
    selected = next(name for name in ORDER if name in scopes)
    print("SENS_CI_FOCAL_ROUTE", json.dumps({
        "selected": selected, "changed_files": paths, "deferred_scopes": sorted(scopes - {selected})
    }, ensure_ascii=False), flush=True)
    if selected == "ci-policy":
        return 0  # The completed lightweight workflow guard is the one check.
    command = COMMANDS[selected]
    print("SENS_CI_ONE_TEST", json.dumps(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError) as exc:
        print("SENS_CI_ROUTE_BLOCKED", exc, file=sys.stderr, flush=True)
        sys.exit(2)
