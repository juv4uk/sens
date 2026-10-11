#!/usr/bin/env python3
"""Reproducible µCPU measurements: same physical T5; honest phase boundaries.

Do NOT compare cold decode+compile+execute to warmed slot replay as a language
speedup. Cross-runtime conclusions require identical process/language baselines.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import encode_words  # noqa: E402
from slot_cpu import compile_t5, run, visible  # noqa: E402


def call(*values):
    result = ["10"]
    for i, arg in enumerate(values):
        if i:
            result.append("00")
        result.extend(arg if isinstance(arg, list) else [arg])
    return [*result, "01"]


Q = call("001", "000")
P = call("111", Q, Q)
A = call("010", P)
E = call("101", Q, Q)
C = call("110", call(A, "0"), call(call("010", "000"), "1"))

CASES = {"d3-quote": Q, "d3-pair": P, "d3-eq": E, "d3-cond": C}


def p95(values: list[int]) -> int:
    seq = sorted(values)
    return seq[(95 * len(seq) + 99) // 100 - 1]


def median(values: list[int]) -> int:
    return int(statistics.median(values))


def paired_ratio_interval(numerator: list[int], denominator: list[int],
                          *, draws: int = 4096, seed: int = 20261010) -> dict:
    """Парний процентильний bootstrap раундів; пілот, НЕ повна модель K–J."""
    if len(numerator) != len(denominator) or len(numerator) < 7:
        raise ValueError("Потрібно щонайменше 7 парних раундів")
    if any(value <= 0 for value in numerator + denominator):
        raise ValueError("Нульовий час забороняє порівняння")
    rng = random.Random(seed)
    n = len(numerator)
    draws_ratio = []
    for _ in range(draws):
        picks = [rng.randrange(n) for _ in range(n)]
        draws_ratio.append(
            sum(numerator[i] for i in picks) /
            sum(denominator[i] for i in picks)
        )
    draws_ratio.sort()
    return {
        "ratio_of_means": sum(numerator) / sum(denominator),
        "bootstrap_percentile_ci95": [draws_ratio[int(0.025 * draws)],
                                      draws_ratio[int(0.975 * draws) - 1]],
        "paired_rounds": n, "bootstrap_draws": draws,
        "seed": seed,
        "scope": (
            "EXPLORATORY: same-process paired phase timings; "
            "not an end-to-end SENS language speedup, not a "
            "hierarchical multi-build/multi-host confidence interval"
        ),
    }


def cpu() -> str:
    path = Path("/proc/cpuinfo")
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    return platform.processor() or "unknown"


def git_sha() -> str:
    if os.getenv("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, check=False, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def bench(physical: bytes, *, samples: int, loops: int, warmup: int) -> dict:
    tape = compile_t5(physical)
    expected = visible(run(tape))
    methods = {
        "decode_compile_only": lambda: compile_t5(physical),
        "physical_compile_execute": lambda: run(compile_t5(physical)),
        "compiled_slot_replay": lambda: run(tape),
    }
    observations: dict[str, list[int]] = {key: [] for key in methods}
    for i in range(samples + warmup):
        # Rotate methods by observation round, minimizing systematic order bias.
        names = tuple(methods)
        order = names[i % len(names):] + names[:i % len(names)]
        for name in order:
            tick = perf_counter_ns()
            for _ in range(loops):
                result = methods[name]()
                if name != "decode_compile_only" and visible(result) != expected:
                    raise AssertionError("µCPU replay changed semantic result")
            delta = perf_counter_ns() - tick
            if i >= warmup:
                observations[name].append(delta // loops)
    return {
        "physical_bytes": len(physical),
        "physical_sha256": hashlib.sha256(physical).hexdigest(),
        "exact_word_count": tape.word_count,
        "compiled_slot_count": tape.slot_count,
        "forms": len(tape.forms),
        "result": expected,
        "timings_ns_per_operation": {
            name: {
                "p50": median(values), "p95": p95(values),
                "min": min(values), "max": max(values),
                "samples": len(values),
                "raw_ns_per_operation": values,
            }
            for name, values in observations.items()
        },
        "paired_phase_ratio": {
            "numerator": "physical_compile_execute",
            "denominator": "compiled_slot_replay",
            **paired_ratio_interval(
                observations["physical_compile_execute"],
                observations["compiled_slot_replay"],
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--samples", type=int, default=15)
    ap.add_argument("--loops", type=int, default=150)
    ap.add_argument("--warmup", type=int, default=4)
    args = ap.parse_args(argv)
    if args.samples < 7 or args.loops < 1 or args.warmup < 0:
        ap.error("samples >=7, loops >=1, warmup >=0 required")

    rows = {}
    for name, words in CASES.items():
        packed = encode_words(words)
        rows[name] = bench(packed, samples=args.samples, loops=args.loops,
                           warmup=args.warmup)
        print(f"{name}: T5={rows[name]['physical_bytes']} B, "
              f"slots={rows[name]['compiled_slot_count']}, "
              f"warm p50={rows[name]['timings_ns_per_operation']['compiled_slot_replay']['p50']} ns, "
              f"full p50={rows[name]['timings_ns_per_operation']['physical_compile_execute']['p50']} ns")
    report = {
        "schema": "sens-microcpu-d1-d3-bounded-benchmark/v1",
        "git_sha": git_sha(),
        "cpu": cpu(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "python_full": sys.version,
        "github_run_id": os.getenv("GITHUB_RUN_ID", ""),
        "github_runner_name": os.getenv("RUNNER_NAME", ""),
        "samples": args.samples,
        "loops": args.loops,
        "warmup": args.warmup,
        "methodology": (
            "in-process CPython perf_counter_ns, rotating method order, "
            "p50/p95 and raw per-round data; same T5 per case; "
            "exploratory paired percentile-bootstrap CI for full-phase/replay "
            "ratio (fixed 4096 resamples); not hierarchical Kalibera-Jones"
        ),
        "claim_boundary": (
            "Research microCPU restricted to D1-D3; no D4+, no arbitrary .sens. "
            "Warmed slot replay EXCLUDES physical T5 decoding and compilation; "
            "cold phase INCLUDES both. No SENS Rust-vs-Python language speedup "
            "inferred; shared-host noise and no hardware/FPGA verification."
        ),
        "cases": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
