#!/usr/bin/env python3
"""One topical CI decision per main push; binary SENS owns semantic truth."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github/workflows"
ON = re.compile(r"^['\"]?on['\"]?:\s*(.*)$")
EVENT = re.compile(r"^  ([\w-]+):")
FORBIDDEN = {
    "pull_request", "pull_request_target", "merge_group",
    "workflow_run", "check_run", "check_suite",
}

# Only existing, language-owned *physical* SENS programs.
# The host selects/executes ONE file; neither Python nor Rust asserts EQ/COND.
WITNESSES = {
    "core3": "tests/semantic/core3-executors-d3-law.sens",
    "domains": "tests/semantic/d4-selector-width-law.sens",
    "knowledge": "tests/semantic/knowledge-exact-arity-structure.sens",
    "narrate": "tests/semantic/narrate-d3-atom-eq-law.sens",
}


def events(source: str) -> dict[str, str]:
    lines = source.splitlines()
    for i, line in enumerate(lines):
        match = ON.match(line)
        if not match:
            continue
        tail = match.group(1).split(" #", 1)[0].strip()
        if tail.startswith("[") and tail.endswith("]"):
            return {v.strip().strip("'\""): "" for v in tail[1:-1].split(",") if v.strip()}
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


def verify() -> bool:
    errors = []
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not paths:
        raise RuntimeError("workflow directory empty")
    on_main = []
    for path in paths:
        try:
            found = events(path.read_text(encoding="utf-8"))
            if not found:
                raise ValueError("empty events")
            forbidden = FORBIDDEN & found.keys()
            if forbidden:
                errors.append(f"{path.name}: forbidden fan-out {sorted(forbidden)}")
            if "push" in found:
                block = found["push"]
                if path.name == "ci.yml" and re.search(
                    r"^\s+branches:\s*\[main\]", block, re.M
                ) and "tags:" not in block:
                    on_main.append(path.name)
                elif path.name == "release.yml" and "tags:" in block and "branches:" not in block:
                    # Release-tag trigger is independent of main-commit CI.
                    pass
                else:
                    errors.append(f"{path.name}: unwanted automatic push")
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
    if on_main != ["ci.yml"]:
        errors.append(f"expected exactly one main-push workflow ci.yml; found {on_main}")
    for message in errors:
        print("SENS_CI_BUDGET_FAIL", message, flush=True)
    if errors:
        return False
    print("SENS_CI_BUDGET_PASS", json.dumps({
        "workflow_files": len(paths), "automatic_main": on_main, "budget": 1,
        "semantic_authority": "physical_binary_SENS",
    }), flush=True)
    return True


def changed() -> tuple[str, list[str]]:
    before = os.getenv("SENS_CI_BEFORE", "")
    if not re.fullmatch(r"[0-9a-f]{40}", before) or before == "0" * 40:
        before = "HEAD^"
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", before], cwd=ROOT,
        capture_output=True, text=True, check=False
    )
    if probe.returncode and re.fullmatch(r"[0-9a-f]{40}", before):
        # Fetch only the exact old tip on a multi-commit main push.
        fetch = subprocess.run(
            ["git", "fetch", "--no-tags", "--depth=1", "origin", before],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if fetch.returncode:
            raise RuntimeError(f"cannot fetch before SHA {before}: {fetch.stderr[-600:]}")
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", before],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
    if probe.returncode:
        raise RuntimeError(f"missing before SHA {before}; refuse invented diff")
    diff = subprocess.run(
        ["git", "diff", "--name-only", before, "HEAD", "--"],
        cwd=ROOT, capture_output=True, text=True, check=False
    )
    if diff.returncode:
        raise RuntimeError(f"git diff failed: {diff.stderr[-600:]}")
    files = sorted(filter(None, diff.stdout.splitlines()))
    if not files:
        raise RuntimeError("empty main diff; no invented topical PASS")
    return before, files


def scope(path: str) -> str:
    if path.startswith(".github/workflows/") or path in {
        "scripts/ci_one_focused_workflow.py", "AGENTS.md"
    }:
        return "ci-policy"
    if path.startswith("lib/core3") or path.startswith(
        "tests/semantic/core3-executors-"
    ):
        return "core3"
    if path == "lib/knowledge.lisp" or path.startswith(
        "tests/semantic/knowledge-exact-arity-structure."
    ):
        return "knowledge"
    if path == "lib/narrate.lisp" or path.startswith(
        "tests/semantic/narrate-d3-atom-eq-"
    ):
        return "narrate"
    if path.startswith("lib/domains/") or path.startswith(
        "tests/semantic/domain-logic-2040/"
    ) or path in {
        "crates/sens/src/domain_ladder.rs",
        "crates/sens/src/domain_identity.rs",
    }:
        return "domains"
    return "unsupported"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def diagnostic(test_id: str, layer: str, path: str, command: list[str],
               code: int, output: bytes, stderr: bytes, reason: str) -> int:
    candidate = ROOT / path
    material = candidate.read_bytes() if candidate.is_file() else b""
    revision = os.environ.get("GITHUB_SHA") or subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
        text=True, check=False
    ).stdout.strip()
    record = {
        "test_id": test_id, "layer": layer, "fixture": path,
        "fixture_sha256": digest(material),
        # An exit-code gate is not an external SENS truth table.
        "expected_sha256": digest(b"1\n" if layer == "eval" else b"exit=0"),
        "actual_sha256": digest(output if layer == "eval" else
                                f"exit={code}".encode() + b"\n" + output),
        "stdout_sha256": digest(output), "stderr_sha256": digest(stderr),
        "first_difference": (
            {"byte_offset": next((i for i in range(max(len(b"1\n"), len(output)))
                                  if b"1\n"[i:i+1] != output[i:i+1]), 0),
             "kind": "D1_verdict_mismatch"}
            if layer == "eval" and code == 0 and output != b"1\n"
            else {"exit_expected": 0, "exit_actual": code}
        ),
        # Do not invent a historical first-bad commit without bisect evidence.
        "first_bad_sha": "UNRESOLVED",
        "first_observed_bad_sha": revision,
        "reproduce": shlex.join(command),
        "classification": "TEST_OR_IMPLEMENTATION_UNRESOLVED",
        "reason": reason, "stderr_tail": stderr.decode(errors="replace")[-1400:],
    }
    print("SENS_FAILURE_REPORT=" + json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)
    print(f"::error::SENS_UNRESOLVED test={test_id} layer={layer} "
          f"first_bad_sha=UNRESOLVED; details in SENS_FAILURE_REPORT", flush=True)
    return 1


def execute(before: str, files: list[str]) -> int:
    scopes = {scope(p) for p in files}
    # Policy integrity takes priority, then the smallest admitted native law.
    selected = next((x for x in ("knowledge", "ci-policy", "core3", "narrate", "domains") if x in scopes), "unsupported")
    deferred = sorted(scopes - {selected})
    print("SENS_CI_FOCAL_ROUTE " + json.dumps({
        "selected": selected, "changed_files": files,
        "deferred_scopes_NOT_VERIFIED": deferred,
    }, ensure_ascii=False, sort_keys=True), flush=True)

    if selected == "unsupported":
        # Run one real, narrow transport check; do not fabricate SENS semantics
        # or produce endless false REDs for a file without an admitted witness.
        command = ["git", "diff", "--check", before, "HEAD", "--"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
        if result.returncode:
            return diagnostic("unmapped-source-diff", "transport", files[0],
                              command, result.returncode, result.stdout, result.stderr,
                              "Mechanical diff check failed; SENS semantics NOT VERIFIED")
        print("::warning title=SENS-SEMANTICS-NOT-VERIFIED::"
              "No admitted one-file binary witness for this diff; "
              "only whitespace/patch integrity verified", flush=True)
        print("SENS_CI_ONE_TEST_PASS test_id=unmapped-source-diff "
              "layer=transport semantics=NOT_VERIFIED", flush=True)
        return 0

    if selected == "ci-policy":
        cmd = ["git", "diff", "--check", before, "HEAD", "--"]
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, check=False)
        if result.returncode:
            return diagnostic("ci-policy-diff", "transport", "scripts/ci_one_focused_workflow.py",
                              cmd, result.returncode, result.stdout, result.stderr,
                              "One-workflow policy diff failed")
        print("SENS_CI_ONE_TEST_PASS test_id=ci-policy-diff layer=transport", flush=True)
        return 0

    fixture = WITNESSES[selected]
    if not (ROOT / fixture).is_file():
        return diagnostic(f"{selected}-native-law", "transport", fixture,
                          ["target/debug/sens", fixture], 2, b"", b"",
                          "Physical binary SENS witness is missing")
    build = ["cargo", "build", "--locked", "-p", "sens-cli", "--bin", "sens"]
    print("SENS_CI_ONE_TEST " + json.dumps({
        "test_id": f"{selected}-native-law", "binary_fixture": fixture,
        "fixture_sha256": digest((ROOT / fixture).read_bytes()),
        "semantic_authority": "SENS; fail branch encoded in fixture",
        "build": build,
        "execute": ["target/debug/sens", fixture],
    }, ensure_ascii=False), flush=True)
    try:
        compilation = subprocess.run(build, cwd=ROOT, capture_output=True,
                                     check=False, timeout=480)
    except subprocess.TimeoutExpired as exc:
        return diagnostic(f"{selected}-native-law", "transport", fixture, build,
                          124, exc.stdout or b"", exc.stderr or b"", "Build timeout")
    if compilation.returncode:
        return diagnostic(f"{selected}-native-law", "transport", fixture, build,
                          compilation.returncode, compilation.stdout, compilation.stderr,
                          "Compiler/mechanism failed; semantic test NOT RUN")
    command = ["target/debug/sens", fixture]
    try:
        actual = subprocess.run(command, cwd=ROOT, capture_output=True,
                                check=False, timeout=90)
    except subprocess.TimeoutExpired as exc:
        return diagnostic(f"{selected}-native-law", "eval", fixture, command,
                          124, exc.stdout or b"", exc.stderr or b"", "SENS timeout")
    # The language evaluates its own law; transport must observe exact D1:1.
    # Exit=0 with empty output or D1:0 is NOT a semantic PASS.
    if actual.returncode or actual.stdout != b"1\n":
        return diagnostic(f"{selected}-native-law", "eval", fixture, command,
                          actual.returncode, actual.stdout, actual.stderr,
                          "SENS self-verdict must be exact D1:1 (one bit); "
                          "exit success alone is insufficient")
    print("SENS_CI_ONE_TEST_PASS " + json.dumps({
        "test_id": f"{selected}-native-law", "layer": "eval",
        "fixture": fixture, "fixture_sha256": digest((ROOT / fixture).read_bytes()),
        "stdout_sha256": digest(actual.stdout),
        "deferred_scopes_NOT_VERIFIED": deferred,
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


def main() -> int:
    if not verify():
        return 1
    if sys.argv[1:] != ["--execute"]:
        return 0
    before, files = changed()
    return execute(before, files)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, RuntimeError) as exc:
        print("SENS_CI_ROUTE_BLOCKED", str(exc), file=sys.stderr, flush=True)
        sys.exit(2)
