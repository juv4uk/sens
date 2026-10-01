#!/usr/bin/env python3
"""#1988 benchmark: flat lookup vs root+suffix vs cached vs hybrid.

The benchmark is research-only. It compiles a standalone Rust mechanism model,
checks exact semantic parity first, then measures Cachegrind instruction
references with preparation and full phases separated.

Execution I-refs are reported as:
    median(full I refs) - median(prepare I refs)

This keeps one-time table/cache construction visible instead of hiding it.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).with_name("bench.rs")
DEFAULT_DEPTHS = (0, 1, 2, 4, 8, 16)
DEFAULT_PATTERNS = ("repeated", "random")
DEFAULT_MODES = ("flat", "cold", "compiled", "cached", "hybrid")
IREF_RE = re.compile(r"I\s+refs:\s+([0-9,]+)")


def sh(args, *, check=True, capture=True, env=None):
    return subprocess.run(
        args,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture,
        env=env,
    )


def compile_bench(out: Path) -> None:
    sh(["rustc", "-O", "-C", "debuginfo=0", str(SOURCE), "-o", str(out)])


def run_binary(binary: Path, mode: str, phase: str, depth: int, pattern: str, calls: int):
    proc = sh([str(binary), mode, phase, str(depth), pattern, str(calls)])
    metrics = {}
    checksum = None
    for line in proc.stdout.splitlines():
        if line.startswith("METRIC\t"):
            _, key, value = line.split("\t", 2)
            metrics[key] = int(value)
        elif line.startswith("CHECKSUM\t"):
            checksum = int(line.split("\t", 1)[1])
    return checksum, metrics


def verify(binary: Path, depths, patterns, calls: int) -> None:
    verify_calls = min(calls, 5000)
    for depth in depths:
        for pattern in patterns:
            proc = sh([
                str(binary), "verify", "full", str(depth), pattern, str(verify_calls)
            ])
            if "VERIFY\tPASS" not in proc.stdout:
                raise RuntimeError(proc.stdout + proc.stderr)


def cachegrind_irefs(
    binary: Path,
    mode: str,
    phase: str,
    depth: int,
    pattern: str,
    calls: int,
    cpu: int | None,
) -> int:
    with tempfile.NamedTemporaryFile(prefix="cg-1988-", delete=False) as tmp:
        cg_out = tmp.name
    os.unlink(cg_out)

    cmd = [
        "valgrind",
        "--tool=cachegrind",
        "--cache-sim=no",
        "--branch-sim=no",
        f"--cachegrind-out-file={cg_out}",
        str(binary),
        mode,
        phase,
        str(depth),
        pattern,
        str(calls),
    ]
    if cpu is not None:
        cmd = ["taskset", "-c", str(cpu)] + cmd

    env = os.environ.copy()
    env["LC_ALL"] = "C"
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env)
    try:
        os.unlink(cg_out)
    except FileNotFoundError:
        pass
    if proc.returncode != 0:
        raise RuntimeError(
            f"cachegrind failed rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    match = IREF_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(f"Cachegrind I refs not found:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def environment(binary: Path, source_sha: str | None) -> dict:
    def output(args):
        try:
            return sh(args).stdout.strip()
        except Exception as exc:  # noqa: BLE001
            return f"unknown ({exc})"

    return {
        "source_sha": source_sha or output(["git", "rev-parse", "HEAD"]),
        "source_file": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "rustc": output(["rustc", "--version"]),
        "valgrind": output(["valgrind", "--version"]),
        "python": platform.python_version(),
        "kernel": platform.release(),
        "cpu": next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "unknown",
        ),
    }


def parse_csv_ints(value: str):
    return tuple(int(part) for part in value.split(",") if part)


def parse_csv_words(value: str):
    return tuple(part for part in value.split(",") if part)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--depths", default=",".join(map(str, DEFAULT_DEPTHS)))
    ap.add_argument("--patterns", default=",".join(DEFAULT_PATTERNS))
    ap.add_argument("--modes", default=",".join(DEFAULT_MODES))
    ap.add_argument("--calls", type=int, default=100_000)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--cpu", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--source-sha", default=None)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    depths = parse_csv_ints(args.depths)
    patterns = parse_csv_words(args.patterns)
    modes = parse_csv_words(args.modes)
    calls = args.calls
    samples = args.samples

    if args.smoke:
        depths = (0, 4, 16)
        patterns = ("repeated",)
        calls = min(calls, 20_000)
        samples = 1

    bad_modes = set(modes) - set(DEFAULT_MODES)
    if bad_modes:
        raise SystemExit(f"unknown modes: {sorted(bad_modes)}")

    out_dir = Path(args.out) if args.out else ROOT / "benchmarks/semantic-tree/results"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="sens-1988-") as td:
        binary = Path(td) / "semantic-tree-bench"
        compile_bench(binary)
        verify(binary, depths, patterns, calls)

        if args.check_only:
            print("semantic parity: PASS")
            return

        env = environment(binary, args.source_sha)
        (out_dir / "environment.json").write_text(
            json.dumps(env, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        rows = []
        for depth in depths:
            for pattern in patterns:
                for mode in modes:
                    full_checksum, metrics = run_binary(
                        binary, mode, "full", depth, pattern, calls
                    )
                    prepare_samples = []
                    full_samples = []
                    for _ in range(samples):
                        prepare_samples.append(
                            cachegrind_irefs(
                                binary, mode, "prepare", depth, pattern, calls, args.cpu
                            )
                        )
                        full_samples.append(
                            cachegrind_irefs(
                                binary, mode, "full", depth, pattern, calls, args.cpu
                            )
                        )

                    execute_samples = [
                        full - prepare
                        for prepare, full in zip(prepare_samples, full_samples, strict=True)
                    ]
                    if min(execute_samples) < 0:
                        raise RuntimeError(
                            f"negative differential I refs: {mode=} {depth=} {pattern=}"
                        )

                    prepare_median = int(statistics.median(prepare_samples))
                    full_median = int(statistics.median(full_samples))
                    execute_median = int(statistics.median(execute_samples))

                    row = {
                        "depth": depth,
                        "pattern": pattern,
                        "mode": mode,
                        "calls": calls,
                        "samples": samples,
                        "checksum": full_checksum,
                        "prepare_i_refs": prepare_median,
                        "prepare_i_refs_min": min(prepare_samples),
                        "prepare_i_refs_max": max(prepare_samples),
                        "full_i_refs": full_median,
                        "full_i_refs_min": min(full_samples),
                        "full_i_refs_max": max(full_samples),
                        "execute_i_refs": execute_median,
                        "execute_i_refs_min": min(execute_samples),
                        "execute_i_refs_max": max(execute_samples),
                        "prepare_i_refs_raw": ",".join(map(str, prepare_samples)),
                        "full_i_refs_raw": ",".join(map(str, full_samples)),
                        "execute_i_refs_raw": ",".join(map(str, execute_samples)),
                        "i_refs_per_call": f"{execute_median / calls:.3f}",
                    }
                    row.update(metrics)
                    rows.append(row)
                    print(
                        f"depth={depth:2d} {pattern:9s} {mode:8s} "
                        f"exec-Irefs={execute_median:12d} "
                        f"[{min(execute_samples)},{max(execute_samples)}] "
                        f"Irefs/call={execute_median / calls:9.3f}"
                    )

        keys = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        with (out_dir / "instructions.tsv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        print(f"wrote {out_dir / 'instructions.tsv'}")
        print(f"wrote {out_dir / 'environment.json'}")


if __name__ == "__main__":
    main()
