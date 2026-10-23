#!/usr/bin/env python3
"""Paired fresh-process wall benchmark for physical SENS vs Python µCPU.

RESEARCH_NON_GATE: this compares two concrete implementations, not languages.
Each timed child reads the same tracked .sens file and returns its verified
result. Parent wall time includes process creation through output/exit; it is
not a cold-disk-cache or isolated interpreter-startup measurement.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from time import perf_counter_ns

from run import contract_version, load_physical, run_checked

ROOT = Path(__file__).resolve().parents[4]
PYTHON_CLI = ROOT / "benchmarks/microcpu/physical_cli.py"


def pair_order(index: int) -> tuple[str, str]:
    """Reverse the first implementation every pair to limit order bias."""
    if index % 2:
        return ("python_microcpu", "native_sens")
    return ("native_sens", "python_microcpu")


def invoke(command: list[str], expected: str, *, timeout: int = 30) -> tuple[int, str]:
    started = perf_counter_ns()
    try:
        result = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"child timed out after {timeout}s: {command!r}") from exc
    elapsed = perf_counter_ns() - started
    if result.returncode:
        raise RuntimeError(
            f"child failed ({result.returncode}): {command!r}\n{result.stderr.strip()}"
        )
    output = result.stdout.strip()
    if output != expected:
        raise ValueError(
            f"parity failure for {command!r}: expected={expected!r}, actual={output!r}"
        )
    return elapsed, output


def measure_case(commands: dict[str, list[str]], *, expected: str,
                 reps: int, warmup: int, timeout: int = 30) -> dict:
    required = {"native_sens", "python_microcpu"}
    if set(commands) != required:
        raise ValueError(f"commands must be exactly {sorted(required)}")
    if reps < 1 or warmup < 0:
        raise ValueError("reps must be positive and warmup must be non-negative")

    # Validate both implementations before collecting any timed sample.
    correctness = {
        name: invoke(command, expected, timeout=timeout)[1]
        for name, command in commands.items()
    }
    for index in range(warmup):
        for name in pair_order(index):
            invoke(commands[name], expected, timeout=timeout)

    pairs = []
    for index in range(reps):
        elapsed: dict[str, int] = {}
        outputs: dict[str, str] = {}
        order = pair_order(index)
        for name in order:
            elapsed[name], outputs[name] = invoke(
                commands[name], expected, timeout=timeout
            )
        pairs.append({"index": index, "order": list(order),
                      "elapsed_ns": elapsed, "outputs": outputs})

    native = [pair["elapsed_ns"]["native_sens"] for pair in pairs]
    python = [pair["elapsed_ns"]["python_microcpu"] for pair in pairs]
    return {
        "parity": "pass", "correctness_gate_outputs": correctness,
        "warmup_pairs": warmup, "measured_pairs": reps,
        "native_sens": {"p50_ns": int(statistics.median(native)),
                        "p95_ns": percentile95(native), "samples_ns": native},
        "python_microcpu": {"p50_ns": int(statistics.median(python)),
                            "p95_ns": percentile95(python), "samples_ns": python},
        "python_over_native_p50_ratio": statistics.median(python) / statistics.median(native),
        "pairs": pairs,
    }


def percentile95(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cpu_model() -> str:
    info = Path("/proc/cpuinfo")
    if info.is_file():
        for line in info.read_text(errors="replace").splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    return platform.processor() or "unknown"


def run(args: argparse.Namespace) -> dict:
    sens_cli = args.sens_cli.resolve(strict=True)
    python = str(Path(args.python).resolve(strict=True))
    measured_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    load_average = list(os.getloadavg()) if hasattr(os, "getloadavg") else None
    cpu_affinity = (
        sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    )
    workloads = (
        ("d3-selftest-positive", args.positive, "1"),
        ("d3-selftest-negative-one-bit", args.negative, "0"),
    )
    cases = {}
    for name, path, expected in workloads:
        item = load_physical(path)
        command_vectors = {
            "native_sens": [str(sens_cli), str(item.path)],
            "python_microcpu": [python, str(PYTHON_CLI), str(item.path)],
        }
        measured = measure_case(command_vectors, expected=expected,
                                reps=args.reps, warmup=args.warmup,
                                timeout=args.timeout)
        cases[name] = {
            "physical_path": item.path.relative_to(ROOT).as_posix(),
            "physical_bytes": len(item.data), "physical_sha256": item.sha256,
            "expected_result": expected, "commands": command_vectors,
            **measured,
        }
    return {
        "schema": "sens-physical-d3-paired-fresh-process-wall/v1",
        "research_status": "RESEARCH_NON_GATE",
        "measured_at_utc": measured_at,
        "repository_head": run_checked(["git", "rev-parse", "HEAD"], timeout=10).stdout.strip(),
        "tracked_worktree_status": run_checked(
            ["git", "status", "--porcelain", "--untracked-files=no"], timeout=10
        ).stdout,
        "contract_version": contract_version(),
        "process_bench_sha256": sha256(Path(__file__)),
        "native_sens_binary_sha256": sha256(sens_cli),
        "python_executable": python,
        "python_executable_sha256": sha256(Path(python)),
        "python_version": run_checked([python, "--version"], timeout=10).stdout.strip(),
        "source_sha256": {
            "process_bench.py": sha256(Path(__file__)),
            "physical_cli.py": sha256(PYTHON_CLI),
            "slot_cpu.py": sha256(ROOT / "benchmarks/microcpu/slot_cpu.py"),
            "sens_t5_t5m_codec.py": sha256(ROOT / "scripts/sens_t5_t5m_codec.py"),
            "benchmark_helpers_run.py": sha256(Path(__file__).with_name("run.py")),
        },
        "cpu": cpu_model(), "platform": platform.platform(),
        "architecture": platform.machine(),
        "load_average_before_measurement": load_average,
        "cpu_affinity": cpu_affinity,
        "reps_per_workload": args.reps, "warmup_pairs": args.warmup,
        "measurement_boundary": (
            "Parent monotonic wall clock from immediately before subprocess.run "
            "until child exit and stdout/stderr capture. Includes fresh child "
            "process creation, runtime/module startup, physical file read, T5 "
            "decode, D2/µCPU compile, execution, output capture and exit. "
            "Build and pre-timing correctness gate excluded. Warmups make OS "
            "file cache warm; cold disk-cache behavior is uncontrolled."
        ),
        "interpretation": (
            "Descriptive end-to-end comparison of native SENS CLI and the "
            "CPython-hosted bounded D1-D3 µCPU on identical physical bytes. "
            "The ratio is specific to these implementations, fixtures, host "
            "and fresh-process boundary; it is not a language-level speedup."
        ),
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens-cli", required=True, type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--positive", type=Path,
                        default=ROOT / "tests/fixtures/semantic/d3-selftest.sens")
    parser.add_argument("--negative", type=Path,
                        default=ROOT / "tests/fixtures/semantic/d3-selftest-negative.sens")
    parser.add_argument("--reps", type=int, default=21)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.reps < 15 or args.warmup < 1 or args.timeout < 1:
        parser.error("reps >= 15, warmup >= 1, timeout >= 1 required")
    report = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    for name, case in report["cases"].items():
        print(f"{name}: parity=PASS pairs={args.reps} "
              f"native-p50={case['native_sens']['p50_ns']}ns "
              f"python-microcpu-p50={case['python_microcpu']['p50_ns']}ns "
              f"python/native={case['python_over_native_p50_ratio']:.2f}x")
    print(f"wrote {args.out}; process-level implementation comparison only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
