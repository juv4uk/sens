#!/usr/bin/env python3
"""Live CUDA leg for the SENS numeric-buffer-map benchmark.

This preserves the already-admitted benchmark kernel exactly:

    #i32(0 ... 0)  -- numeric-buffer-map (lambda (x) (+ x 1)) --> #i32(1 ... 1)

The SENS surface/FASL benchmark remains the language-path measurement.
This file measures the heterogeneous execution leg only: file-backed i32
payload -> persistent cml-gpu-worker -> CUDA -> file-backed result.

No silent CPU fallback is allowed. If the worker/socket/GPU path is unavailable,
the command fails.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import struct
import subprocess
import tempfile
import time
from pathlib import Path

DEFAULT_SIZES = (1_000, 100_000, 1_000_000)


def checked(command: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def best_effort_output(command: list[str], *, env: dict[str, str]) -> str:
    try:
        return checked(command, env=env).stdout.strip()
    except RuntimeError as error:
        return f"unavailable ({error})"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_zero_i32(path: Path, size: int) -> None:
    if size < 1:
        raise ValueError(f"size must be positive: {size}")
    with path.open("wb") as target:
        target.truncate(size * 4)


def verify_all_ones(path: Path, size: int) -> None:
    expected_bytes = size * 4
    actual_bytes = path.stat().st_size
    if actual_bytes != expected_bytes:
        raise RuntimeError(
            f"wrong output size: expected {expected_bytes}, got {actual_bytes}"
        )

    seen = 0
    with path.open("rb") as source:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            if len(chunk) % 4:
                raise RuntimeError("output byte count is not divisible by i32 width")
            for (value,) in struct.iter_unpack("<i", chunk):
                if value != 1:
                    raise RuntimeError(
                        f"CUDA result mismatch at element {seen}: expected 1, got {value}"
                    )
                seen += 1
    if seen != size:
        raise RuntimeError(f"verified {seen} elements, expected {size}")


def gpu_info(env: dict[str, str]) -> str:
    command = [
        "/usr/lib/wsl/lib/nvidia-smi",
        "--query-gpu=name,driver_version,compute_cap,memory.total",
        "--format=csv,noheader",
    ]
    try:
        return checked(command, env=env).stdout.strip()
    except (FileNotFoundError, RuntimeError) as error:
        return f"unavailable ({error})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worker",
        type=Path,
        default=Path("/home/agents/.local/bin/cml-gpu-worker"),
    )
    parser.add_argument(
        "--socket",
        type=Path,
        default=Path("/run/cml-gpu-worker/worker.sock"),
    )
    parser.add_argument("--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES))
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.reps < 1:
        parser.error("--reps must be positive")
    if any(size < 1 for size in args.sizes):
        parser.error("--sizes must all be positive")
    if not args.worker.is_file():
        parser.error(f"GPU worker not found: {args.worker}")

    out = args.out or Path(tempfile.mkdtemp(prefix="sens-gpu-numeric-buffer-map-"))
    out.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["CML_GPU_WORKER_SOCKET"] = str(args.socket)

    if checked([str(args.worker), "ping"], env=env).stdout.strip() != "pong":
        raise RuntimeError("persistent GPU worker did not answer pong")
    probe = checked([str(args.worker), "probe"], env=env).stdout.strip()

    facts: dict[str, object] = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": best_effort_output(["git", "rev-parse", "HEAD"], env=env),
        "python": platform.python_version(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "worker": str(args.worker),
        "socket": str(args.socket),
        "worker_probe": probe,
        "gpu": gpu_info(env),
        "kernel_semantics": "i32 x -> x + 1",
        "fallback": "forbidden",
    }

    rows: list[dict[str, object]] = []
    for size in args.sizes:
        input_path = out / f"input-{size}.i32"
        output_path = out / f"output-{size}.i32"
        write_zero_i32(input_path, size)

        for repetition in range(1, args.reps + 1):
            output_path.unlink(missing_ok=True)
            command = [
                str(args.worker),
                "chain-file-i32",
                str(input_path),
                str(output_path),
                "1",
            ]
            started = time.perf_counter_ns()
            result = checked(command, env=env)
            elapsed_ns = time.perf_counter_ns() - started

            verify_all_ones(output_path, size)
            throughput = size / (elapsed_ns / 1_000_000_000)
            row = {
                "size": size,
                "repetition": repetition,
                "elapsed_ns": elapsed_ns,
                "elements_per_second": throughput,
                "worker_evidence": result.stdout.strip(),
                "output_sha256": sha256(output_path),
            }
            rows.append(row)
            print(
                "[cuda] "
                f"size={size} repetition={repetition} "
                f"elapsed_ns={elapsed_ns} elements_per_second={throughput:.0f} "
                "oracle=all-ones PASS"
            )

    (out / "environment.json").write_text(
        json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "gpu.tsv").write_text(
        "size\trepetition\telapsed_ns\telements_per_second\toutput_sha256\tworker_evidence\n"
        + "".join(
            f"{row['size']}\t{row['repetition']}\t{row['elapsed_ns']}\t"
            f"{row['elements_per_second']:.3f}\t{row['output_sha256']}\t"
            f"{str(row['worker_evidence']).replace(chr(9), ' ')}\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    print(f"artifacts={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
