#!/usr/bin/env python3
"""Fail-closed exploratory SENS process measurements; never a language-law oracle.

Exact stdout bytes, clean stderr, and both exit codes are checked here. The native SENS witness suite is separate.
No physical energy sensor is used; energy is always ENERGY_NOT_MEASURED.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tempfile

FORMAT = "sens-native-exploratory-measurement/v1"
RECORD = re.compile(r"^(WALL_SECONDS|MAX_RSS_KIB|CHILD_EXIT)=([^\n]+)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(65536), b""):
            digest.update(data)
    return digest.hexdigest()


def parse_time(text: str) -> dict[str, float | int]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = RECORD.fullmatch(line)
        if match is None or match.group(1) in values:
            raise ValueError("time output contains invalid or duplicate field")
        values[match.group(1)] = match.group(2)
    if set(values) != {"WALL_SECONDS", "MAX_RSS_KIB", "CHILD_EXIT"}:
        raise ValueError("time output has missing fields")
    elapsed = float(values["WALL_SECONDS"])
    # GNU /usr/bin/time reports hundredths of a second: 0.00 is not a
    # defensible measurement at this resolution (run a larger workload).
    if not math.isfinite(elapsed) or elapsed <= 0:
        raise ValueError("elapsed is not positive and finite at timer resolution")
    if not re.fullmatch(r"[0-9]+", values["MAX_RSS_KIB"]):
        raise ValueError("RSS is not an integer")
    if not re.fullmatch(r"[0-9]+", values["CHILD_EXIT"]):
        raise ValueError("child exit is not an integer")
    rss = int(values["MAX_RSS_KIB"])
    if rss <= 0:
        raise ValueError("RSS is missing or nonpositive")
    return {"elapsed_wall_s": elapsed, "max_rss_kib": rss,
            "child_exit": int(values["CHILD_EXIT"])}


def checkout_head(root: Path) -> str:
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
                          capture_output=True, text=True, timeout=5, check=True)
    head = proc.stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ValueError("git HEAD is not a full commit SHA")
    return head


def measure(binary: Path, program: Path, expected: str, time_tool: Path,
            timeout_s: float, runs: int, git_head: str, task_id: str) -> dict:
    command = [str(binary.resolve()), str(program.resolve())]
    result = {
        "schema": FORMAT,
        "status": "BLOCKED_NOT_RUN",
        "evidence_level": "exploratory_output_check_only",
        "semantic_laws": "NOT_TESTED_BY_THIS_TOOL",
        "phase": "independent_cold_process_startup_included",
        "task_id": task_id,
        "checkout_head_sha": git_head,
        "executable_sha256": sha256(binary),
        "program_sha256": sha256(program),
        "command": command,
        "time_tool": str(time_tool),
        "expected_stdout": expected,
        "timeout_s": timeout_s,
        "energy_status": "ENERGY_NOT_MEASURED",
        "energy_joules": None,
        "host": {"system": platform.system(), "release": platform.release(),
                 "machine": platform.machine(), "processor": platform.processor()},
        "samples": [],
        "limitations": [
            "Matching final output does not prove every algorithmic step or a SENS language law.",
            "A shared runner has uncontrolled workload, temperature, and CPU frequency.",
            "Independent process starts on one machine are not independent lab sessions.",
            "GNU time gives kernel-reported peak RSS for the timed child; not a guaranteed peak for the entire process tree.",
            "Build/mint time is excluded; process startup is included; JIT/GC may be inside.",
        ],
    }
    for index in range(1, runs + 1):
        with tempfile.TemporaryDirectory(prefix="sens-native-time-") as temp:
            out = Path(temp) / "time.txt"
            cmd = [str(time_tool), "-f",
                   "WALL_SECONDS=%e\nMAX_RSS_KIB=%M\nCHILD_EXIT=%x",
                   "-o", str(out), *command]
            sample: dict = {"repeat": index, "admitted": False}
            try:
                # Read unmodified bytes: text=True silently normalizes CRLF to LF,
                # and splitlines() admits missing or extra newline variants.
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        start_new_session=True)
                try:
                    stdout, stderr = proc.communicate(timeout=timeout_s)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.communicate()
                    raise
                sample["wrapper_exit"] = proc.returncode
                sample["stdout"] = stdout[:512].decode("utf-8", errors="replace")
                sample["stdout_sha256"] = hashlib.sha256(stdout).hexdigest()
                sample["stderr_excerpt"] = stderr[:1024].decode("utf-8", errors="replace")
                sample["stderr_sha256"] = hashlib.sha256(stderr).hexdigest()
                metric = parse_time(out.read_text(encoding="utf-8"))
                sample.update(metric)
                # A numeric value hidden among warnings or missing its final LF
                # cannot be admitted as the defined physical workload result.
                sample["output_matches"] = stdout == (expected + "\n").encode("utf-8")
                sample["stderr_clean"] = stderr == b""
                sample["admitted"] = (proc.returncode == 0 and
                                      metric["child_exit"] == 0 and
                                      sample["output_matches"] and
                                      sample["stderr_clean"])
                if not sample["admitted"]:
                    sample["rejection"] = "CHILD_EXIT_OR_NONCANONICAL_OUTPUT_OR_STDERR"
            except subprocess.TimeoutExpired:
                sample["rejection"] = "TIMEOUT"
            except (OSError, ValueError, UnicodeError) as exc:
                sample["rejection"] = f"METER_FAILURE:{type(exc).__name__}"
            result["samples"].append(sample)
            if not sample["admitted"]:
                result["status"] = "BLOCKED_PARITY_OR_MEASUREMENT"
                break
    else:
        result["status"] = "EXPLORATORY_OUTPUT_VERIFIED"
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True, help="already-built native SENS interpreter")
    p.add_argument("--program", type=Path, required=True, help="already-minted .sens program")
    p.add_argument("--expected", required=True, help="exactly one expected stdout line")
    p.add_argument("--task-id", required=True, help="predefined workload identifier")
    p.add_argument("--repo-root", type=Path, required=True, help="checkout containing exact Git HEAD")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--timeout-s", type=float, default=30)
    p.add_argument("--time-tool", type=Path, default=Path("/usr/bin/time"))
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(argv)
    if not (1 <= a.runs <= 5) or not (0 < a.timeout_s <= 120):
        p.error("run count 1..5 and timeout 0..120 seconds are required")
    if not a.expected or "\n" in a.expected or "\r" in a.expected:
        p.error("expected output must be one nonempty line")
    if not a.task_id or any(ch.isspace() for ch in a.task_id):
        p.error("task id must be nonempty and contain no whitespace")
    if not a.binary.is_file() or not os.access(a.binary, os.X_OK):
        p.error("native binary missing or not executable")
    if not a.program.is_file():
        p.error("minted SENS program missing")
    if not a.time_tool.is_file() or not os.access(a.time_tool, os.X_OK):
        p.error("GNU time binary missing or not executable")
    try:
        head = checkout_head(a.repo_root)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        p.error(f"cannot resolve exact checkout commit: {exc}")
    data = measure(a.binary, a.program, a.expected, a.time_tool,
                   a.timeout_s, a.runs, head, a.task_id)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{data['status']}: {len(data['samples'])} sample(s), raw={a.output}")
    return 0 if data["status"] == "EXPLORATORY_OUTPUT_VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
