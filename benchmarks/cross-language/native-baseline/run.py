#!/usr/bin/env python3
"""Fair native-baseline comparison: C, Rust, CPython and Node.js.

This is a host-language baseline, not a SENS-vs-language ranking. Compilation
is measured separately from cold process execution. Correctness is checked
before any timing row is emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAMS = Path(__file__).resolve().parent / "programs"


def expected(n: int) -> int:
    return n * (n + 1) * (2 * n + 1) // 6


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_programs(build: Path) -> dict[str, dict]:
    rustc = shutil.which("rustc")
    if rustc is None:
        candidates = sorted(Path("/usr/local/rustup/toolchains").glob("*/bin/rustc"))
        if candidates:
            rustc = str(candidates[-1])
    if rustc is None:
        raise SystemExit("rustc unavailable; install a Rust toolchain rather than substituting another language")
    tools = {
        "c-gcc-o2": (["gcc", "-O2", "-std=c11", str(PROGRAMS / "workload.c"), "-o", str(build / "workload-c")], build / "workload-c"),
        "rustc-o": ([rustc, "-O", str(PROGRAMS / "workload.rs"), "-o", str(build / "workload-rust")], build / "workload-rust"),
    }
    results: dict[str, dict] = {}
    for name, (command, artifact) in tools.items():
        start = time.perf_counter_ns()
        proc = subprocess.run(command, capture_output=True, text=True, timeout=120)
        elapsed = time.perf_counter_ns() - start
        if proc.returncode != 0:
            raise SystemExit(f"compile failed for {name}: {proc.stderr}")
        results[name] = {"compile_command": command, "compile_wall_ns": elapsed, "artifact": str(artifact), "artifact_bytes": artifact.stat().st_size, "artifact_sha256": sha256(artifact)}
    return results


def command_for(name: str, build: Path) -> list[str]:
    if name == "c-gcc-o2": return [str(build / "workload-c")]
    if name == "rustc-o": return [str(build / "workload-rust")]
    if name == "python3": return ["python3", str(PROGRAMS / "workload.py")]
    if name == "node22": return ["node", str(PROGRAMS / "workload.js")]
    raise ValueError(name)


def measure(name: str, build: Path, n: int, reps: int, warmups: int) -> dict:
    command = command_for(name, build) + [str(n)]
    for _ in range(warmups):
        proc = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            raise SystemExit(f"warmup failed for {name}: {proc.stderr}")
    samples: list[int] = []
    outputs: list[str] = []
    for _ in range(reps):
        start = time.perf_counter_ns()
        proc = subprocess.run(command, capture_output=True, text=True, timeout=120)
        elapsed = time.perf_counter_ns() - start
        if proc.returncode != 0:
            raise SystemExit(f"run failed for {name}: {proc.stderr}")
        samples.append(elapsed)
        outputs.append(proc.stdout.strip())
    if len(set(outputs)) != 1 or outputs[0] != str(expected(n)):
        raise SystemExit(f"parity failed for {name}: outputs={outputs[:3]} expected={expected(n)}")
    samples.sort()
    return {
        "implementation": name,
        "command": command,
        "n": n,
        "expected": str(expected(n)),
        "parity": True,
        "reps": reps,
        "warmups": warmups,
        "samples_ns": samples,
        "median_ns": samples[len(samples) // 2],
        "p95_ns": samples[min(len(samples) - 1, int(len(samples) * 0.95))],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200000)
    parser.add_argument("--reps", type=int, default=9)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.n < 1 or args.reps < 3 or args.warmups < 0:
        raise SystemExit("require n>=1, reps>=3 and warmups>=0")
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sens-native-baseline-") as tmp:
        build = Path(tmp)
        compile_meta = compile_programs(build)
        results = [measure(name, build, args.n, args.reps, args.warmups) for name in ("c-gcc-o2", "rustc-o", "python3", "node22")]
        source_by_impl = {
            "c-gcc-o2": (PROGRAMS / "workload.c").stat().st_size,
            "rustc-o": (PROGRAMS / "workload.rs").stat().st_size,
            "python3": (PROGRAMS / "workload.py").stat().st_size,
            "node22": (PROGRAMS / "workload.js").stat().st_size,
        }
        for row in results:
            row["source_bytes"] = source_by_impl[row["implementation"]]
            if row["implementation"] in compile_meta:
                row.update({k: v for k, v in compile_meta[row["implementation"]].items() if k != "artifact"})
    result = {
        "schema": "sens-cross-language-native-baseline/v1",
        "workload": "sum-of-squares-0-to-n",
        "n": args.n,
        "expected": str(expected(args.n)),
        "implementations": results,
        "source_bytes": {row["implementation"]: row["source_bytes"] for row in results},
        "environment": {"python": shutil.which("python3"), "node": shutil.which("node"), "gcc": shutil.which("gcc"), "rustc": shutil.which("rustc"), "cpu": next((line.strip() for line in open('/proc/cpuinfo', encoding='utf-8') if line.startswith('model name')), "unknown")},
        "fairness": ["parity before timing", "same n and mathematical function", "compile cost separate", "cold process wall time", "C/Rust u64 is safe for selected n; Python/Node use arbitrary precision"],
        "scope": "host-language native baseline; not a universal language ranking and not SENS runtime evidence",
    }
    (args.out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Cross-language native baseline", "", "Workload: `sum(i² for i=0..n)`, parity checked before timing.", "", "| Implementation | Median cold process ns | p95 ns | Source bytes | Compiled artifact bytes | Compile ns |", "|---|---:|---:|---:|---:|---:|"]
    for row in results:
        size = row.get("artifact_bytes", row["source_bytes"])
        compile_ns = row.get("compile_wall_ns", "n/a")
        compiled = row.get("artifact_bytes", "n/a")
        lines.append(f"| {row['implementation']} | {row['median_ns']} | {row['p95_ns']} | {row['source_bytes']} | {compiled} | {compile_ns} |")
    lines += ["", "> These are concrete implementations on one machine. They do not establish that one programming language is universally faster.", "", f"n = {args.n}; expected = `{expected(args.n)}`", ""]
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
