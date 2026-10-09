#!/usr/bin/env python3
"""Empty-process startup isolation bench.

No workload. Separates cold-start cost from steady execution.
Primary optional metric: Cachegrind I refs. Wall is always recorded.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path


def instruction_count(cmd: list[str]) -> int:
    proc = subprocess.run(
        [
            "valgrind",
            "--tool=cachegrind",
            "--cache-sim=no",
            "--cachegrind-out-file=/dev/null",
            *cmd,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"cachegrind fail: {' '.join(cmd)}\n{proc.stderr}")
    match = re.search(r"I\s+refs:\s*([\d,]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"no I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def wall_seconds(cmd: list[str]) -> float:
    start = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(f"fail ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}")
    return elapsed


def candidates(python: str) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = [
        ("cpython", [python, "-c", "pass"]),
    ]
    for name, args in (
        ("lua54", ["lua5.4", "-e", ""]),
        ("lua", ["lua", "-e", ""]),
    ):
        if shutil.which(args[0]):
            out.append((name, args))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--cachegrind", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.reps < 1:
        ap.error("--reps >= 1")

    runtimes = candidates(args.python)
    rows: list[dict[str, object]] = []

    for rep in range(1, args.reps + 1):
        for runtime, cmd in runtimes:
            row: dict[str, object] = {
                "runtime": runtime,
                "phase": "startup",
                "workload": "empty",
                "rep": rep,
                "cmd": " ".join(cmd),
                "i_refs": "",
                "wall_s": f"{wall_seconds(cmd):.9f}",
            }
            if args.cachegrind:
                row["i_refs"] = instruction_count(cmd)
            rows.append(row)
        print(f"[measure] rep {rep}/{args.reps}")

    args.out.mkdir(parents=True, exist_ok=True)
    fields = ["runtime", "phase", "workload", "rep", "cmd", "i_refs", "wall_s"]
    with (args.out / "startup.tsv").open("w", encoding="utf-8") as fh:
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[f]) for f in fields) + "\n")

    lines = [
        "# Startup isolation (empty process)",
        "",
        "| runtime | median wall, s | median I refs | samples |",
        "|---|---:|---:|---:|",
    ]
    for runtime, _cmd in runtimes:
        sample = [r for r in rows if r["runtime"] == runtime]
        walls = [float(r["wall_s"]) for r in sample]
        irefs = [int(r["i_refs"]) for r in sample if r["i_refs"] != ""]
        w = statistics.median(walls)
        ir = f"{statistics.median(irefs):,.0f}" if irefs else "N/A"
        lines.append(f"| {runtime} | {w:.6f} | {ir} | {len(sample)} |")
    lines += [
        "",
        "These rows are **startup only**. Do not mix with steady execution ratios.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report + "\n", encoding="utf-8")
    (args.out / "environment.json").write_text(
        json.dumps(
            {
                "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "agent": "grok-bench-coord",
                "suite": "startup-isolation",
                "python": sys.version,
                "platform": platform.platform(),
                "cachegrind": args.cachegrind,
                "reps": args.reps,
                "runtimes": [r for r, _ in runtimes],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(report)
    print(f"results: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
