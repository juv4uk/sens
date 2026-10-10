#!/usr/bin/env python3
"""Run every registered SENS benchmark reproduction command, without fail-fast.

Each stand is isolated in its own CI matrix job by .github/workflows/benchmark-sweep.yml.
Manifest commands are executed verbatim from the repository root and logged as artifacts.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "benchmarks"
RESULTS = ROOT / "benchmark-sweep-results"
REQUIRED = {
    "schema", "stand", "wing", "roles", "question", "claim",
    "witness", "status", "generation", "axis", "reproduce",
}
SCHEMA = "sens-benchmark-manifest/v1"


def load_manifests() -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in sorted(BENCHMARKS.glob("*/bench.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
            continue
        if not isinstance(item, dict):
            errors.append(f"{path.relative_to(ROOT)}: manifest must be an object")
            continue
        missing = REQUIRED - item.keys()
        if missing:
            errors.append(f"{path.relative_to(ROOT)}: missing {', '.join(sorted(missing))}")
            continue
        stand = item.get("stand")
        command = item.get("reproduce")
        if item.get("schema") != SCHEMA:
            errors.append(f"{path.relative_to(ROOT)}: unsupported schema {item.get('schema')!r}")
        if stand != path.parent.name:
            errors.append(f"{path.relative_to(ROOT)}: stand must match directory name")
        if not isinstance(command, str) or not command.strip():
            errors.append(f"{path.relative_to(ROOT)}: reproduce must be non-empty")
        if not isinstance(item.get("roles"), list) or not item["roles"]:
            errors.append(f"{path.relative_to(ROOT)}: roles must be a non-empty list")
        if not isinstance(item.get("witness"), list) or not item["witness"]:
            errors.append(f"{path.relative_to(ROOT)}: witness must be a non-empty list")
        manifests.append(item)
    if not manifests:
        errors.append("no benchmarks/*/bench.json manifests found")
    if errors:
        raise ValueError("\n".join(errors))
    stands = [item["stand"] for item in manifests]
    if len(stands) != len(set(stands)):
        raise ValueError("duplicate stand names in benchmark manifests")
    return manifests


def terminate_process_group(proc: subprocess.Popen[Any]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


def run_stand(manifests: list[dict[str, Any]], stand: str, timeout_s: int) -> int:
    item = next((x for x in manifests if x["stand"] == stand), None)
    if item is None:
        print(f"Unknown benchmark stand: {stand}", file=sys.stderr)
        return 2

    directory = RESULTS / stand
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / "console.log"
    result_path = directory / "result.json"
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    command = item["reproduce"]

    print(f"STAND={stand}")
    print(f"COMMAND={command}")
    print(f"TIMEOUT_SECONDS={timeout_s}")
    print(f"LOG={log_path.relative_to(ROOT)}")

    timed_out = False
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"stand: {stand}\ncommand: {command}\nstarted_at: {started_at}\n")
        log.write(f"timeout_seconds: {timeout_s}\n\n--- command output ---\n")
        log.flush()
        proc = subprocess.Popen(
            ["/bin/bash", "-e", "-u", "-o", "pipefail", "-c", command],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            returncode = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate_process_group(proc)
            returncode = 124
            log.write(f"\nTIMEOUT: stand exceeded {timeout_s} seconds; process group terminated.\n")
        log.flush()

    elapsed_s = round(time.monotonic() - start, 3)
    status = "timeout" if timed_out else ("passed" if returncode == 0 else "failed")
    result = {
        "stand": stand,
        "status": status,
        "return_code": returncode,
        "timeout_seconds": timeout_s,
        "duration_seconds": elapsed_s,
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": os.environ.get("GITHUB_SHA", "local"),
        "command": command,
        "log": str(log_path.relative_to(ROOT)),
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(f"## Benchmark: \u0060{stand}\u0060\n\n")
            summary.write(f"- **Status:** {status}\n")
            summary.write(f"- **Duration:** {elapsed_s:.3f}s\n")
            summary.write(f"- **Return code:** {returncode}\n")
            summary.write(f"- **Command:** \u0060{command}\u0060\n")
            summary.write(f"- **Log:** \u0060{log_path.relative_to(ROOT)}\u0060\n")

    print(json.dumps(result, ensure_ascii=False))
    return 0 if returncode == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-json", action="store_true", help="emit all registered stands as a CI matrix")
    parser.add_argument("--stand", help="run one named stand")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=int(os.environ.get("BENCHMARK_SWEEP_TIMEOUT_SECONDS", "2700")),
        help="per-stand command timeout (default: 2700 seconds)",
    )
    args = parser.parse_args()

    try:
        manifests = load_manifests()
    except ValueError as exc:
        print(f"benchmark sweep discovery failed: {exc}", file=sys.stderr)
        return 2

    if args.list_json:
        matrix = {
            "include": [
                {"stand": item["stand"], "reproduce": item["reproduce"]}
                for item in manifests
            ]
        }
        print(json.dumps(matrix, ensure_ascii=False, separators=(",", ":")))
        return 0
    if not args.stand:
        parser.error("choose --list-json or --stand STAND")
    if args.timeout_seconds < 1:
        parser.error("--timeout-seconds must be positive")
    return run_stand(manifests, args.stand, args.timeout_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
