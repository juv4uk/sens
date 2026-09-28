#!/usr/bin/env python3
"""#1567: bare-SENS/FASL benchmark for `01011001` numeric-buffer-map.

The program maps exact `x -> x + 1` over an i32 buffer of zeroes and reads
its last element.  The final answer stays a small independent oracle (`1`),
while the map must traverse and allocate the complete input buffer.

Run inside the repository's pinned Guix environment after building `ci_bench`:

    python3 benchmarks/sens-surface/numeric_buffer_map.py \
      --sens-bench target/release/examples/ci_bench --size 1000 --check-only

Use `--measure` only after `wsm-agent bench-ready` reports no contention.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
from pathlib import Path

SIZES = (1_000, 100_000, 1_000_000)


def program_for(size: int) -> tuple[str, str]:
    """Return bare-SENS source and its exact expected answer for one size."""
    if size < 1:
        raise ValueError(f"numeric-buffer-map size must be positive: {size}")
    input_values = " ".join("0" for _ in range(size))
    source = (
        "(01011000\n"
        "  (01011001 (00001000 (x) (00001100 x 1))\n"
        f"    #i32({input_values}))\n"
        f"  {size - 1})\n"
    )
    return source, "1"


def case_name(size: int) -> str:
    return f"numeric-buffer-map-{size}"


def write_case(directory: Path, size: int) -> tuple[str, str]:
    """Materialize the ci_bench input files and return (name, expected)."""
    directory.mkdir(parents=True, exist_ok=True)
    name = case_name(size)
    call, expected = program_for(size)
    (directory / f"{name}-sens.setup.lisp").write_text("", encoding="utf-8")
    (directory / f"{name}-sens.call.lisp").write_text(call, encoding="utf-8")
    (directory / f"{name}.expected").write_text(expected + "\n", encoding="utf-8")
    return name, expected


def checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def instruction_refs(command: list[str]) -> int:
    result = checked([
        "valgrind", "--tool=cachegrind", "--cache-sim=no",
        "--cachegrind-out-file=/dev/null", *command,
    ])
    match = re.search(r"I\s+refs:\s*([\d,]+)", result.stderr)
    if match is None:
        raise RuntimeError(f"cachegrind did not print I refs:\n{result.stderr}")
    return int(match.group(1).replace(",", ""))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def environment(sens_bench: Path) -> dict[str, object]:
    def output(command: list[str]) -> str:
        try:
            return checked(command).stdout.strip()
        except RuntimeError as error:
            return f"unknown ({error})"

    return {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": output(["git", "rev-parse", "HEAD"]),
        "git_dirty": output(["git", "status", "--porcelain", "--untracked-files=no"]) != "",
        "sens_bench": str(sens_bench.resolve()),
        "sens_bench_sha256": sha256(sens_bench),
        "python": platform.python_version(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "load1": os.getloadavg()[0],
        "guix_environment": os.environ.get("GUIX_ENVIRONMENT", "not-set"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens-bench", required=True, type=Path)
    parser.add_argument("--size", required=True, type=int, choices=SIZES)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--measure", action="store_true")
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()
    if args.check_only and args.measure:
        parser.error("choose at most one of --check-only and --measure")
    if args.reps < 1:
        parser.error("--reps must be positive")
    if not args.sens_bench.is_file():
        parser.error(f"ci_bench not found: {args.sens_bench}")

    out = args.out or Path(tempfile.mkdtemp(prefix="sens-numeric-buffer-map-"))
    name, expected = write_case(out, args.size)
    base = [str(args.sens_bench), str(out), name, "sens"]
    checked([*base, "encode"])
    checked([*base, "full"])
    print(f"[check] size={args.size} expected={expected} form=sens-fasl OK")

    facts = environment(args.sens_bench)
    facts.update({
        "size": args.size,
        "expected": expected,
        "mode": "check-only",
        "fasl_sha256": {
            "setup": sha256(out / f"{name}-sens.setup.fasl"),
            "call": sha256(out / f"{name}-sens.call.fasl"),
        },
    })
    rows: list[dict[str, int]] = []
    if args.measure:
        facts["mode"] = "cachegrind"
        for repetition in range(1, args.reps + 1):
            refs = instruction_refs([*base, "full"])
            rows.append({"repetition": repetition, "instruction_refs": refs})
            print(f"[measure] size={args.size} repetition={repetition} I_refs={refs}")

    (out / "environment.json").write_text(
        json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if rows:
        (out / "instructions.tsv").write_text(
            "repetition\tinstruction_refs\n" + "".join(
                f"{row['repetition']}\t{row['instruction_refs']}\n" for row in rows
            ),
            encoding="utf-8",
        )
    print(f"artifacts={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
