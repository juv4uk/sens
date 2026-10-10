#!/usr/bin/env python3
"""Reproducible, parity-gated paired A/B subprocess wall-time measurements.

Strict scope: one host + one build per lane + repeated *process launches*.
The session bootstrap is EXPLORATORY and must never be labeled a full
Kalibera–Jones cross-build/host confidence interval or used as a required CI
performance threshold. A separate instruction-count gate owns instructions.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import time


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def command(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"command must be JSON argv: {exc}") from exc
    if (not isinstance(value, list) or not value or
            any(not isinstance(x, str) or not x for x in value)):
        raise ValueError("command must be a nonempty JSON array of nonempty strings")
    return value


def percentile(values: list[float], fraction: float) -> float:
    if not values or not 0 <= fraction <= 1:
        raise ValueError("invalid quantile input")
    ordered = sorted(values)
    point = (len(ordered) - 1) * fraction
    low = math.floor(point)
    high = math.ceil(point)
    return ordered[low] + (ordered[high] - ordered[low]) * (point - low)


def balanced_orders(count: int, rng: random.Random) -> list[str]:
    # Randomize the position of A and B without letting one lane always
    # receive the warm cache. This is balanced allocation, not a fixed ABAB.
    orders = ["AB"] * (count // 2) + ["BA"] * (count // 2)
    if count % 2:
        orders.append(rng.choice(("AB", "BA")))
    rng.shuffle(orders)
    return orders


def session_bootstrap(
    session_log_ratios: list[list[float]], *, draws: int, seed: int
) -> dict[str, object]:
    """Resample whole sessions, then paired trials within selected sessions.

    Distinct sessions here are consecutive blocks on ONE hosted runner, not
    independent OS boots, recompilations, processors, or platform replicates.
    """
    if len(session_log_ratios) < 3 or any(len(x) < 5 for x in session_log_ratios):
        raise ValueError("at least 3 sessions with 5 paired trials each required")
    if draws < 400:
        raise ValueError("at least 400 bootstrap resamples required")
    if any(not math.isfinite(x) for v in session_log_ratios for x in v):
        raise ValueError("nonfinite log wall-time ratio")
    means = [statistics.mean(v) for v in session_log_ratios]
    effect = statistics.mean(means)
    rng = random.Random(seed)
    boot = []
    for _ in range(draws):
        selected = [rng.randrange(len(session_log_ratios))
                    for _ in range(len(session_log_ratios))]
        average = statistics.mean(
            statistics.mean(
                rng.choice(session_log_ratios[session])
                for _ in range(len(session_log_ratios[session]))
            )
            for session in selected
        )
        boot.append(average)
    lo = math.exp(percentile(boot, 0.025))
    hi = math.exp(percentile(boot, 0.975))
    ratio = math.exp(effect)
    verdict = ("EXPLORATORY_B_FASTER" if hi < 1.0 else
               "EXPLORATORY_A_FASTER" if lo > 1.0 else
               "INCONCLUSIVE")
    return {
        "ratio_definition": "geometric mean of B wall_ns / A wall_ns",
        "B_over_A_ratio": ratio,
        "B_over_A_95pct_exploratory_CI": [lo, hi],
        "B_faster_pct_point_estimate": (1.0 - ratio) * 100.0,
        "exploratory_single_host_verdict": verdict,
        "publishable_kalibera_jones_verdict": "BLOCKED_SINGLE_BUILD_SINGLE_HOST",
        "bootstrap_unit": "sessions then paired trials (NOT independent host replicates)",
        "bootstrap_draws": draws,
        "bootstrap_seed": seed,
    }


def host_facts() -> dict[str, object]:
    cpuinfo = Path("/proc/cpuinfo")
    cpu_model = platform.processor() or "unknown"
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu_model = line.partition(":")[2].strip()
                break
    governor_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    turbo_path = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
    return {
        "platform": platform.platform(),
        "cpu_model": cpu_model,
        "logical_cpus": os.cpu_count(),
        "affinity_cpus": sorted(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity") else None,
        "cpu0_governor_observed": governor_path.read_text().strip()
        if governor_path.is_file() else "unknown",
        "intel_pstate_no_turbo_observed": turbo_path.read_text().strip()
        if turbo_path.is_file() else "unknown",
        "governor_or_turbo_changed_by_benchmark": False,
        "python": platform.python_version(),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "github_sha": os.getenv("GITHUB_SHA"),
        "github_runner_name": os.getenv("RUNNER_NAME"),
        "github_runner_environment": os.getenv("RUNNER_ENVIRONMENT"),
    }


def run(argv: list[str], *, timeout: int) -> tuple[int, bytes]:
    started = time.perf_counter_ns()
    process = subprocess.run(argv, check=False, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=timeout)
    elapsed = time.perf_counter_ns() - started
    if process.returncode or process.stderr or not process.stdout:
        raise RuntimeError(
            f"unstable/nonclean A/B workload {argv!r}; rc={process.returncode}; "
            f"stderr={process.stderr[:400]!r}; stdout_empty={not process.stdout}"
        )
    if elapsed <= 0:
        raise RuntimeError("nonpositive elapsed wall time")
    return elapsed, process.stdout


def read_input_hashes(a: list[str], b: list[str], payload: Path) -> dict[str, str]:
    if not payload.is_file() or not payload.read_bytes():
        raise ValueError("input payload must exist and not be empty")
    result = {str(payload.resolve()): sha256(payload.read_bytes())}
    for argv in (a, b):
        executable = Path(argv[0]).resolve()
        if not executable.is_file():
            raise ValueError(f"command executable must be an existing file: {argv[0]}")
        result[str(executable)] = sha256(executable.read_bytes())
    return dict(sorted(result.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a-json", required=True, help='argv as JSON, e.g. ["./sens","file.sens"]')
    parser.add_argument("--b-json", required=True)
    parser.add_argument("--payload", required=True, type=Path, help="exact same physical input file")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--sessions", type=int, default=5)
    parser.add_argument("--pairs-per-session", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--pin-first-allowed-core", action="store_true")
    args = parser.parse_args()
    if (args.sessions < 3 or args.pairs_per_session < 5 or args.warmups < 0 or
            args.bootstrap < 400 or args.bootstrap > 50000 or args.timeout < 1):
        parser.error("require >=3 sessions, >=5 pairs/session, >=0 warmups, "
                     "400..50000 bootstraps and positive timeout")
    try:
        a, b = command(args.a_json), command(args.b_json)
        input_hashes = read_input_hashes(a, b, args.payload)
    except ValueError as exc:
        parser.error(str(exc))

    # Optional, explicit pin inside the allowed cpuset; never change system
    # governor or turbo on GitHub's shared hosted hardware.
    pinned = None
    if args.pin_first_allowed_core:
        if not hasattr(os, "sched_getaffinity"):
            parser.error("CPU affinity is unsupported on this platform")
        permitted = os.sched_getaffinity(0)
        if not permitted:
            parser.error("allowed CPU affinity set is empty")
        pinned = min(permitted)
        os.sched_setaffinity(0, {pinned})

    root = Path(__file__).resolve().parents[2]
    git_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True,
        check=True, timeout=15
    ).stdout.strip()
    # Refuse to overwrite evidence of another exact-head run.
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("out directory is not empty; old evidence cannot be overwritten")
    args.out.mkdir(parents=True, exist_ok=True)

    expected = run(a, timeout=args.timeout)[1]
    if expected != run(b, timeout=args.timeout)[1]:
        raise RuntimeError("B output differs from A output before timings")
    rng = random.Random(args.seed)
    rows: list[dict[str, object]] = []
    log_ratios: list[list[float]] = []
    for session in range(args.sessions):
        for order in balanced_orders(args.warmups, rng):
            for lane in order:
                _, output = run(a if lane == "A" else b, timeout=args.timeout)
                if output != expected:
                    raise RuntimeError(f"warmup output drift in {lane} session {session}")
        session_logs = []
        for pair, order in enumerate(balanced_orders(args.pairs_per_session, rng), 1):
            elapsed: dict[str, int] = {}
            for lane in order:
                ns, output = run(a if lane == "A" else b, timeout=args.timeout)
                if output != expected:
                    raise RuntimeError(
                        f"output changed during {lane} session={session}, pair={pair}"
                    )
                elapsed[lane] = ns
            ratio = math.log(elapsed["B"] / elapsed["A"])
            session_logs.append(ratio)
            rows.append({
                "session": session + 1,
                "pair": pair,
                "order": order,
                "A_wall_ns": elapsed["A"],
                "B_wall_ns": elapsed["B"],
                "B_over_A_ratio": math.exp(ratio),
            })
        log_ratios.append(session_logs)

    after_hashes = read_input_hashes(a, b, args.payload)
    if after_hashes != input_hashes:
        raise RuntimeError("executable or input payload changed during run")
    report = {
        "schema": "sens-paired-wall-evidence/v1",
        "result": "PARITY_PASS_EXPLORATORY_TIMING_ONLY",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "git_checkout_sha": git_sha,
        "benchmark_script_sha256": sha256(Path(__file__).read_bytes()),
        "A_argv": a,
        "B_argv": b,
        "input_sha256": input_hashes,
        "output_sha256": sha256(expected),
        "host": host_facts(),
        "pinned_cpu": pinned,
        "sessions": args.sessions,
        "paired_trials_per_session": args.pairs_per_session,
        "warmups_per_lane_per_session": args.warmups,
        "seed": args.seed,
        "metric": "per-subprocess wall ns, includes spawn, read, decode, evaluation, stdout",
        "instruction_refs_measured": False,
        "independent_Lisp_oracle": False,
        "same_host_repeated_sessions_not_independent_machine_runs": True,
        "caveats": [
            "Both commands must have byte-identical stdout on exactly the same payload.",
            "Shared hosted runner can vary governor, interrupts, turbo, background contention.",
            "No coordinated omission correction; only closed-loop subprocess invocations.",
            "One host/build does not support formal cross-host/build Kalibera-Jones claims.",
            "An exploratory interval excludes 1 by chance sometimes; never fail CI on it.",
        ],
        "statistics": session_bootstrap(
            log_ratios, draws=args.bootstrap, seed=args.seed ^ 0x5A5A
        ),
    }
    (args.out / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (args.out / "raw.tsv").open("w", encoding="utf-8", newline="") as file:
        fields = ["session", "pair", "order", "A_wall_ns", "B_wall_ns", "B_over_A_ratio"]
        writer = csv.DictWriter(file, fieldnames=fields, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    stat = report["statistics"]
    print("PARITY=PASS; experimental paired wall subprocess evidence.")
    print(f"SHA={git_sha}; sessions={args.sessions}; "
          f"pairs/session={args.pairs_per_session}; seed={args.seed}")
    print(f"B/A ratio={stat['B_over_A_ratio']:.5f}; "
          f"exploratory 95% interval={stat['B_over_A_95pct_exploratory_CI']}")
    print("Kalibera-Jones formal verdict=BLOCKED_SINGLE_BUILD_SINGLE_HOST")
    print(f"Observed single-host classification={stat['exploratory_single_host_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
