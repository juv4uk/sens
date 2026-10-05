#!/usr/bin/env python3
"""#1988 benchmark: flat lookup vs root+suffix generator/cached/compiled paths.

Research-only benchmark. It compiles a standalone mechanism model, checks
semantic parity first, then measures Cachegrind counters with preparation and
full phases separated.

For the current Contract 11.6 D6 experiment use --current-d6. That profile is
fixed to the 16 exact D6 selector descendants (two D3 roots × three suffix bits)
and treats the flat table as a benchmark-only control, never semantic authority.

Additive work counters (instruction references and branch count) are reported as:
    median(full counter - prepare counter)

Cache misses and branch mispredictions are stateful/non-additive across separate
Cachegrind processes, so they are reported as prepare/full totals only. This
keeps one-time table/cache construction visible without pretending that miss
deltas are an isolated execution measurement.
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

COUNTER_PATTERNS = {
    "i_refs": re.compile(r"I\s+refs:\s+([0-9,]+)"),
    "i1_misses": re.compile(r"I1\s+misses:\s+([0-9,]+)"),
    "d1_misses": re.compile(r"D1\s+misses:\s+([0-9,]+)"),
    "branches": re.compile(r"Branches:\s+([0-9,]+)"),
    "mispredicts": re.compile(r"Mispredicts:\s+([0-9,]+)"),
}

D6_SELECTOR_COORDINATES = tuple(
    [f"{raw:06b}" for raw in range(0b011000, 0b100000)]
    + [f"{raw:06b}" for raw in range(0b100000, 0b101000)]
)


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


def cachegrind_counters(
    binary: Path,
    mode: str,
    phase: str,
    depth: int,
    pattern: str,
    calls: int,
    cpu: int | None,
) -> dict[str, int]:
    with tempfile.NamedTemporaryFile(prefix="cg-1988-", delete=False) as tmp:
        cg_out = tmp.name
    os.unlink(cg_out)

    cmd = [
        "valgrind",
        "--tool=cachegrind",
        "--cache-sim=yes",
        "--branch-sim=yes",
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

    counters: dict[str, int] = {}
    for key, pattern_re in COUNTER_PATTERNS.items():
        match = pattern_re.search(proc.stderr)
        if not match:
            raise RuntimeError(f"Cachegrind counter {key!r} not found:\n{proc.stderr}")
        counters[key] = int(match.group(1).replace(",", ""))
    return counters


def environment(binary: Path, source_sha: str | None, current_d6: bool) -> dict:
    def output(args):
        try:
            return sh(args).stdout.strip()
        except Exception as exc:  # noqa: BLE001
            return f"unknown ({exc})"

    env = {
        "source_sha": source_sha or output(["git", "rev-parse", "HEAD"]),
        "source_file": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "binary_bytes": binary.stat().st_size,
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
    if current_d6:
        env.update({
            "authority_generation": "Contract 11.6 / #3572; D6 map #3393",
            "runtime_mechanism": "#3588 / #3394",
            "benchmark_issue": "#1988",
            "semantic_scope": "D6 selector DIRECT_LAW 16/64",
            "selector_depth": 3,
            "selector_coordinates": D6_SELECTOR_COORDINATES,
            "flat_control": "benchmark-only; never semantic authority",
        })
    return env


def parse_csv_ints(value: str):
    return tuple(int(part) for part in value.split(",") if part)


def parse_csv_words(value: str):
    return tuple(part for part in value.split(",") if part)


def med(samples: list[dict[str, int]], key: str) -> int:
    return int(statistics.median(sample[key] for sample in samples))


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
    ap.add_argument(
        "--current-d6",
        action="store_true",
        help="Contract 11.6 profile: exactly the current 16 D6 selector descendants",
    )
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

    if args.current_d6:
        # D6 selector = D3 root + three family-local suffix bits.
        depths = (3,)
        patterns = ("repeated", "random") if args.smoke else ("repeated", "random", "alternating")
        modes = ("flat", "cold", "compiled")
        calls = min(calls, 20_000) if args.smoke else calls

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

        env = environment(binary, args.source_sha, args.current_d6)
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
                            cachegrind_counters(
                                binary, mode, "prepare", depth, pattern, calls, args.cpu
                            )
                        )
                        full_samples.append(
                            cachegrind_counters(
                                binary, mode, "full", depth, pattern, calls, args.cpu
                            )
                        )

                    execute_samples = []
                    for prepare, full in zip(prepare_samples, full_samples, strict=True):
                        delta = {
                            "i_refs": full["i_refs"] - prepare["i_refs"],
                            "branches": full["branches"] - prepare["branches"],
                        }
                        if any(value < 0 for value in delta.values()):
                            raise RuntimeError(
                                f"negative additive differential counters: "
                                f"{mode=} {depth=} {pattern=} {delta=}"
                            )
                        execute_samples.append(delta)

                    row = {
                        "depth": depth,
                        "pattern": pattern,
                        "mode": mode,
                        "calls": calls,
                        "samples": samples,
                        "checksum": full_checksum,
                        "prepare_i_refs": med(prepare_samples, "i_refs"),
                        "full_i_refs": med(full_samples, "i_refs"),
                        "execute_i_refs": med(execute_samples, "i_refs"),
                        "i_refs_per_call": f"{med(execute_samples, 'i_refs') / calls:.3f}",
                        "prepare_i1_misses": med(prepare_samples, "i1_misses"),
                        "full_i1_misses": med(full_samples, "i1_misses"),
                        "prepare_d1_misses": med(prepare_samples, "d1_misses"),
                        "full_d1_misses": med(full_samples, "d1_misses"),
                        "prepare_branches": med(prepare_samples, "branches"),
                        "full_branches": med(full_samples, "branches"),
                        "execute_branches": med(execute_samples, "branches"),
                        "prepare_mispredicts": med(prepare_samples, "mispredicts"),
                        "full_mispredicts": med(full_samples, "mispredicts"),
                        "prepare_i_refs_raw": ",".join(str(x["i_refs"]) for x in prepare_samples),
                        "full_i_refs_raw": ",".join(str(x["i_refs"]) for x in full_samples),
                        "execute_i_refs_raw": ",".join(str(x["i_refs"]) for x in execute_samples),
                        "authority_generation": "contract-11.6" if args.current_d6 else "research-general",
                        "semantic_scope": "d6-selector-16" if args.current_d6 else "research-selector-model",
                    }
                    row.update(metrics)
                    rows.append(row)
                    print(
                        f"depth={depth:2d} {pattern:11s} {mode:8s} "
                        f"exec-Irefs={row['execute_i_refs']:12d} "
                        f"Irefs/call={float(row['i_refs_per_call']):9.3f} "
                        f"full-I1miss={row['full_i1_misses']:7d} "
                        f"full-D1miss={row['full_d1_misses']:7d} "
                        f"full-mispred={row['full_mispredicts']:7d}"
                    )

        keys = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        for row in rows:
            for key in keys:
                row.setdefault(key, 0)
        with (out_dir / "instructions.tsv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        print(f"wrote {out_dir / 'instructions.tsv'}")
        print(f"wrote {out_dir / 'environment.json'}")


if __name__ == "__main__":
    main()
