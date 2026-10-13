#!/usr/bin/env python3
"""Mechanical runner and diagnostic evidence only: semantics belongs to binary SENS."""
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
PROOF = "tests/semantic/domain-logic-2040/proof.sens"
MUTANT = "tests/semantic/domain-logic-2040/mutant.sens"
TEST_ID = "domain-logic-2040-binary-self-verdict"
ON = re.compile(r"^['\"]?on['\"]?:\s*(.*)$")
EVENT = re.compile(r"^  ([\w-]+):")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_events(text: str) -> dict[str, str]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        found = ON.match(line)
        if not found:
            continue
        inline = found.group(1).split(" #", 1)[0].strip()
        if inline.startswith("[") and inline.endswith("]"):
            return {item.strip().strip("'\""): "" for item in inline[1:-1].split(",")}
        if inline:
            if re.fullmatch(r"[\w-]+", inline):
                return {inline: ""}
            raise ValueError("unsupported trigger form")
        answer: dict[str, str] = {}
        current = None
        for row in lines[i+1:]:
            if row.strip() and not row[0].isspace() and not row.startswith("#"):
                break
            match = EVENT.match(row)
            if match:
                current = match.group(1)
                answer[current] = row
            elif current is not None:
                answer[current] += "\n" + row
        return answer
    raise ValueError("missing trigger")


def verify_single_automatic() -> None:
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not paths:
        raise ValueError("empty workflow directory")
    automatic = []
    failures = []
    for path in paths:
        try:
            triggers = parse_events(path.read_text(encoding="utf-8"))
            if not triggers:
                raise ValueError("empty triggers")
            active = set(triggers) - {"workflow_dispatch"}
            if active:
                automatic.append((path.name, tuple(sorted(active))))
            if path.name == "ci.yml":
                if active != {"push"}:
                    raise ValueError(f"expected only push; actual {active}")
                push = triggers["push"]
                if not re.search(r"^\s+branches:\s*\[main\]\s*$", push, re.M):
                    raise ValueError("not scoped to main")
                if "paths:" not in push or "tags:" in push:
                    raise ValueError("missing narrow paths or extra tag trigger")
            elif active:
                raise ValueError(f"unauthorized automatic events {active}")
        except (ValueError, OSError) as exc:
            failures.append(f"{path.name}: {exc}")
    if automatic != [("ci.yml", ("push",))]:
        failures.append(f"automatic workflow set incorrect: {automatic}")
    for fault in failures:
        print("SENS_CI_BUDGET_FAIL " + fault, flush=True)
    if failures:
        raise ValueError("multiple or invalid automatic workflows")
    print("SENS_CI_SINGLE_AUTOMATIC " + json.dumps({
        "workflow_count": len(paths),
        "authorized": "ci.yml only: main push scoped to SENS files",
        "semantic_authority": "physical SENS only"
    }, ensure_ascii=False), flush=True)


def run(command: list[str], timeout: int) -> tuple[int, bytes, bytes]:
    try:
        out = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout, check=False)
        return out.returncode, out.stdout, out.stderr
    except subprocess.TimeoutExpired as err:
        return 124, err.stdout or b"", err.stderr or b"TIMEOUT"


def failure(layer: str, path: str, command: list[str], rc: int, out: bytes,
            stderr: bytes, wanted: str) -> int:
    raw = (ROOT / path).read_bytes() if (ROOT / path).is_file() else b""
    record = {
        "test_id": TEST_ID, "layer": layer, "fixture": path,
        "fixture_sha256": sha256(raw),
        "expected_sha256": sha256(wanted.encode("ascii")),
        "actual_sha256": sha256(f"exit={rc}".encode("ascii")),
        "stdout_sha256": sha256(out), "stderr_sha256": sha256(stderr),
        "first_difference": {"exit_expected": wanted.removeprefix("exit="),
                             "exit_actual": rc},
        "first_bad_sha": "UNRESOLVED",
        "first_observed_bad_sha": os.getenv("GITHUB_SHA", "UNRESOLVED"),
        "classification": "UNRESOLVED",
        "reproduce": "python3 scripts/ci_one_focused_workflow.py --execute",
        "failed_command": shlex.join(command),
        "stderr_tail": stderr.decode(errors="replace")[-1500:],
    }
    print("SENS_FAILURE_REPORT=" + json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)
    print("::error title=UNINFORMATIVE-OUTPUT::First-bad SHA not proven; "
          "fail closed, do not guess or silently quarantine.", flush=True)
    return 1


def execute() -> int:
    verify_single_automatic()
    for fixture in [PROOF, MUTANT]:
        if not (ROOT / fixture).is_file():
            return failure("transport", fixture, ["test", "-f", fixture],
                           2, b"", b"missing exact SENS fixture", "exit=0")
    print("SENS_CI_TARGET " + json.dumps({
        "test_id": TEST_ID,
        "proof": PROOF, "proof_sha256": sha256((ROOT / PROOF).read_bytes()),
        "mutant": MUTANT, "mutant_sha256": sha256((ROOT / MUTANT).read_bytes()),
        "law": "SENS's own fail-closed binary logic; no host truth table",
        "one_program_checks": 2040
    }, ensure_ascii=False, sort_keys=True), flush=True)
    build = ["cargo", "build", "--locked", "-p", "sens-cli", "--bin", "sens"]
    rc, out, err = run(build, 540)
    if rc:
        return failure("transport", PROOF, build, rc, out, err, "exit=0")
    positive = ["target/debug/sens", PROOF]
    rc, out, err = run(positive, 90)
    if rc:
        return failure("eval", PROOF, positive, rc, out, err, "exit=0")
    negative = ["target/debug/sens", MUTANT]
    bad_rc, bad_out, bad_err = run(negative, 90)
    if bad_rc in (0, 124):
        return failure("eval", MUTANT, negative, bad_rc, bad_out, bad_err, "exit=nonzero")
    print("SENS_CI_ONE_TEST_PASS " + json.dumps({
        "test_id": TEST_ID, "layer": "eval",
        "proof_sha256": sha256((ROOT / PROOF).read_bytes()),
        "mutant_sha256": sha256((ROOT / MUTANT).read_bytes()),
        "positive_output_sha256": sha256(out),
        "negative_error_sha256": sha256(bad_err),
        "mutant_exit": bad_rc,
        "semantic_authority": "binary SENS"
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


def main() -> int:
    if sys.argv[1:] not in ([], ["--execute"]):
        print("usage: ci_one_focused_workflow.py [--execute]", file=sys.stderr)
        return 2
    if sys.argv[1:] == ["--execute"]:
        return execute()
    verify_single_automatic()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print("SENS_CI_UNINFORMATIVE_OUTPUT " + str(error), file=sys.stderr, flush=True)
        sys.exit(2)
