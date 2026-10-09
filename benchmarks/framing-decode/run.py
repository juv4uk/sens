#!/usr/bin/env python3
"""#1993 framing decode benchmark.

Measures CPU instruction cost of finding exact bounded word spans and message
boundaries. It deliberately stops before identity-carrier construction (#1989).

Matrix:
  word codec: A Width3+escape, B gamma-only, S current outer-record candidate
  message boundary: raw exact-bits, stop-bit, outer gamma length,
                    container valid-bits metadata

Candidate S follows #3155 exactly for the word classes exercised here:
D1..D7 use the three-bit width prefix, D8 uses 1110, and widths >8 are
carried as canonical BinaryNumber records under 11110 + gamma0(width).
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
IREF_RE = re.compile(r"I\s+refs:\s+([0-9,]+)")

CODECS = ("a", "b", "s")
WRAPPERS = ("raw", "stop", "gamma", "container")
WIDTHS = (1,2,3,4,5,6,7,8,9,16,32,64,65,128)
PROGRAM_CASES = ("repeated3", "mixed", "corpus")


def sh(args, *, check=True):
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=True)


def compile_bench(out: Path) -> None:
    sh(["rustc", "-O", "-C", "debuginfo=0", str(SOURCE), "-o", str(out)])


def verify(binary: Path) -> None:
    proc = sh([str(binary), "verify"])
    if "VERIFY\tPASS" not in proc.stdout:
        raise RuntimeError(proc.stdout + proc.stderr)


def run_metrics(binary: Path, codec: str, wrapper: str, case: str, iterations: int):
    mode = "invalid" if case == "invalid" else "valid"
    proc = sh([str(binary), "full", codec, wrapper, case, str(iterations), mode])
    metrics = {}
    checksum = None
    for line in proc.stdout.splitlines():
        if line.startswith("METRIC\t"):
            _, key, value = line.split("\t", 2)
            metrics[key] = int(value)
        elif line.startswith("CHECKSUM\t"):
            checksum = int(line.split("\t", 1)[1])
    return checksum, metrics


def cachegrind(binary: Path, phase: str, codec: str, wrapper: str, case: str,
               iterations: int, cpu: int | None) -> int:
    mode = "invalid" if case == "invalid" else "valid"
    with tempfile.NamedTemporaryFile(prefix="cg-1993-", delete=False) as tmp:
        out = tmp.name
    os.unlink(out)
    cmd = [
        "valgrind", "--tool=cachegrind", "--cache-sim=no", "--branch-sim=no",
        f"--cachegrind-out-file={out}",
        str(binary), phase, codec, wrapper, case, str(iterations), mode,
    ]
    if cpu is not None:
        cmd = ["taskset", "-c", str(cpu)] + cmd
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env)
    try:
        os.unlink(out)
    except FileNotFoundError:
        pass
    if proc.returncode != 0:
        raise RuntimeError(f"cachegrind rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}")
    match = IREF_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(f"I refs missing\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def environment(binary: Path, source_sha: str | None) -> dict:
    def output(args):
        try:
            return sh(args).stdout.strip()
        except Exception as exc:  # noqa: BLE001
            return f"unknown ({exc})"

    cpu = "unknown"
    try:
        cpu = next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        )
    except Exception:
        pass
    return {
        "source_sha": source_sha or output(["git", "rev-parse", "HEAD"]),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "rustc": output(["rustc", "--version"]),
        "valgrind": output(["valgrind", "--version"]),
        "python": platform.python_version(),
        "kernel": platform.release(),
        "cpu": cpu,
    }


def iterations_for(case: str, default: int) -> int:
    if case.startswith("single-"):
        return default
    if case == "repeated3":
        return max(1000, default // 8)
    if case in ("mixed", "corpus"):
        return max(1000, default // 4)
    if case == "invalid":
        return default
    raise ValueError(case)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--iterations", type=int, default=20000)
    ap.add_argument("--cpu", type=int, default=None)
    ap.add_argument("--widths", default=None, help="comma-separated single-word widths")
    ap.add_argument("--codecs", default=",".join(CODECS))
    ap.add_argument("--wrappers", default=",".join(WRAPPERS))
    ap.add_argument("--singles-only", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--source-sha", default=None)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    widths = (
        tuple(int(part) for part in args.widths.split(",") if part)
        if args.widths
        else (WIDTHS if not args.smoke else (3,8,16,65))
    )
    codecs = tuple(part for part in args.codecs.split(",") if part)
    wrappers = tuple(part for part in args.wrappers.split(",") if part)
    if set(codecs) - set(CODECS):
        raise SystemExit("unknown codec")
    if set(wrappers) - set(WRAPPERS):
        raise SystemExit("unknown wrapper")
    program_cases = () if args.singles_only else (PROGRAM_CASES if not args.smoke else ("corpus",))
    cases = tuple(f"single-{w}" for w in widths) + program_cases
    if not args.singles_only:
        cases += ("invalid",)

    out_dir = Path(args.out) if args.out else ROOT / "benchmarks/framing-decode/results"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="sens-1993-") as td:
        binary = Path(td) / "framing-bench"
        compile_bench(binary)
        verify(binary)
        if args.check_only:
            print("framing correctness: PASS")
            return

        env = environment(binary, args.source_sha)
        (out_dir / "environment.json").write_text(
            json.dumps(env, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        rows = []
        for codec in codecs:
            for wrapper in wrappers:
                for case in cases:
                    iterations = iterations_for(case, args.iterations)
                    _, metrics = run_metrics(binary, codec, wrapper, case, iterations)
                    prepare_samples = []
                    full_samples = []
                    for _ in range(args.samples):
                        prepare_samples.append(cachegrind(
                            binary, "prepare", codec, wrapper, case, iterations, args.cpu
                        ))
                        full_samples.append(cachegrind(
                            binary, "full", codec, wrapper, case, iterations, args.cpu
                        ))
                    execute_samples = [
                        full - prepare
                        for prepare, full in zip(prepare_samples, full_samples, strict=True)
                    ]
                    if min(execute_samples) < 0:
                        raise RuntimeError("negative differential I refs")

                    execute = int(statistics.median(execute_samples))
                    words_per_message = metrics["words_per_message"]
                    valid = case != "invalid"
                    denom_words = iterations * words_per_message if valid else 0

                    row = {
                        "codec": codec,
                        "wrapper": wrapper,
                        "case": case,
                        "iterations": iterations,
                        "samples": args.samples,
                        "prepare_i_refs": int(statistics.median(prepare_samples)),
                        "full_i_refs": int(statistics.median(full_samples)),
                        "execute_i_refs": execute,
                        "execute_i_refs_min": min(execute_samples),
                        "execute_i_refs_max": max(execute_samples),
                        "i_refs_per_message": f"{execute / iterations:.3f}",
                        "i_refs_per_word": f"{execute / denom_words:.3f}" if denom_words else "",
                        "prepare_i_refs_raw": ",".join(map(str, prepare_samples)),
                        "full_i_refs_raw": ",".join(map(str, full_samples)),
                        "execute_i_refs_raw": ",".join(map(str, execute_samples)),
                    }
                    row.update(metrics)
                    rows.append(row)
                    print(
                        f"{codec} {wrapper:9s} {case:10s} "
                        f"Irefs/msg={execute/iterations:9.3f} "
                        f"wire={metrics['total_wire_bits']:4d} bits"
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
