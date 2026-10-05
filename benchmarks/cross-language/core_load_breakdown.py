#!/usr/bin/env python3
"""Measure current SENS Core loading mechanisms with the existing startup_bench.

The benchmark keeps process startup in every row and reports both absolute
Cachegrind I refs and deltas from the session-only baseline. Modes are:
session, bytes, decode, decode-lower, decoded-eval, parse, macro, core.

This does not change language semantics; it is diagnostic evidence for #3490.
"""

from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import time
from pathlib import Path

MODES = ("session", "bytes", "decode", "decode-lower", "decoded-eval", "parse", "macro", "core")


def cmd_for(runner: str, mode: str, fasl: str) -> list[str]:
    cmd = [runner, mode]
    if mode in {"bytes", "decode", "decode-lower", "decoded-eval"}:
        cmd.append(fasl)
    return cmd


def irefs(cmd: list[str]) -> int:
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
        raise RuntimeError(f"cachegrind failed: {' '.join(cmd)}\n{proc.stderr}")
    match = re.search(r"I\s+refs:\s*([\d,]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"missing I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def wall(cmd: list[str]) -> float:
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stderr}")
    return elapsed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runner", required=True)
    ap.add_argument("--fasl", default="lib/core.lisp.fasl")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")

    runner = str(Path(args.runner).resolve())
    fasl = str(Path(args.fasl).resolve())

    rows: list[dict[str, object]] = []
    for mode in MODES:
        cmd = cmd_for(runner, mode, fasl)
        # Viability before timing.
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"startup_bench mode {mode} failed: {proc.stdout}\n{proc.stderr}"
            )
        for rep in range(1, args.reps + 1):
            rows.append(
                {
                    "mode": mode,
                    "rep": rep,
                    "i_refs": irefs(cmd),
                    "wall_s": wall(cmd),
                }
            )
        print(f"[core-load] {mode}: OK")

    args.out.mkdir(parents=True, exist_ok=True)

    with (args.out / "core-load-rows.tsv").open("w", encoding="utf-8") as fh:
        fh.write("mode\trep\ti_refs\twall_s\n")
        for row in rows:
            fh.write(
                f"{row['mode']}\t{row['rep']}\t{row['i_refs']}\t{row['wall_s']}\n"
            )

    def med(mode: str, field: str) -> float:
        vals = [float(r[field]) for r in rows if r["mode"] == mode]
        return statistics.median(vals)

    base_i = med("session", "i_refs")
    base_w = med("session", "wall_s")

    lines = [
        "# Core-load breakdown",
        "",
        "Every mode is a fresh process. Delta subtracts the session-only process baseline.",
        "",
        "| mode | median I refs | delta vs session | median wall, ms | wall delta, ms |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        mi = med(mode, "i_refs")
        mw = med(mode, "wall_s")
        lines.append(
            f"| {mode} | {mi:,.0f} | {mi - base_i:,.0f} | {mw * 1000:.3f} | {(mw - base_w) * 1000:.3f} |"
        )

    lines += [
        "",
        "Mode meaning:",
        "- session: construct empty Session only;",
        "- bytes: read committed core.lisp.fasl bytes;",
        "- decode: read + decode FASL program;",
        "- decode-lower: read + decode + lower the FASL program;",
        "- decoded-eval: read + decode + lower + evaluate Core forms in a Core4 Session, without full loader peer-binding work;",
        "- parse: parse embedded textual Core source;",
        "- macro: load macro library into Session;",
        "- core: full load_core_library path.",
        "",
        "Interpret deltas as process-level diagnostic evidence, not exact nested phase subtraction.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "core-load-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
