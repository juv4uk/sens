#!/usr/bin/env python3
"""Steady-phase harness — synergy with #3601 / #3608.

Measures CPython (always) and optional SENS runner with phases:
  full | ready | repeat
Derives steady = (repeat − ready) / inner_reps when both present.

Correctness is mandatory before timing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from corpus import CASES, EXPECTED, PARAMS, python_source, sens_source

HERE = Path(__file__).resolve().parent
PHASES_DRIVER = HERE / "cpython_phases.py"


def git_fact(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception as exc:  # noqa: BLE001
        return f"unknown ({exc})"


def final_line(stdout: str) -> str:
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def run_cmd(cmd: list[str], *, expected: str | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"fail ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    if expected is not None:
        got = final_line(proc.stdout)
        if got != expected:
            raise RuntimeError(
                f"wrong answer: {' '.join(cmd)}: expected={expected!r} got={got!r}"
            )
    return proc


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
        raise RuntimeError(
            f"cachegrind fail ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    match = re.search(r"I\s+refs:\s*([\d,]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"no I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def wall_seconds(cmd: list[str]) -> float:
    start = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(
            f"fail ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    return elapsed


def geomean(values: list[float]) -> float:
    return math.exp(sum(math.log(v) for v in values) / len(values))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens-runner", type=Path, help="SENS current_exact_domain_bench binary")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--python-only", action="store_true", help="skip SENS even if runner given")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--inner-reps", type=int, default=5, help="N for repeat phase")
    ap.add_argument("--only", default=",".join(CASES))
    ap.add_argument("--cachegrind", action="store_true", help="measure I refs via Valgrind")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    selected = tuple(x for x in args.only.split(",") if x)
    unknown = sorted(set(selected) - set(CASES))
    if unknown:
        ap.error(f"unknown workloads: {', '.join(unknown)}")
    if args.reps < 1 or args.inner_reps < 1:
        ap.error("reps and inner-reps must be >= 1")

    want_sens = args.sens_runner is not None and not args.python_only
    if want_sens and not args.sens_runner.is_file():
        ap.error(f"SENS runner not found: {args.sens_runner}")

    work = Path(tempfile.mkdtemp(prefix="sens-steady-"))
    py_files: dict[str, Path] = {}
    sens_files: dict[str, Path] = {}
    for name in selected:
        p = work / f"{name}.py"
        p.write_text(python_source(name), encoding="utf-8")
        py_files[name] = p
        s = work / f"{name}.lisp"
        s.write_text(sens_source(name), encoding="utf-8")
        sens_files[name] = s

    # --- correctness gate ---
    for name in selected:
        run_cmd(
            [args.python, str(PHASES_DRIVER), str(py_files[name]), "full"],
            expected=EXPECTED[name],
        )
        print(f"[check] cpython/{name}: OK expected={EXPECTED[name]}")
        if want_sens:
            run_cmd(
                [str(args.sens_runner.resolve()), str(sens_files[name])],
                expected=EXPECTED[name],
            )
            print(f"[check] sens-exact/{name}: OK expected={EXPECTED[name]}")

    if args.check_only:
        return 0

    rows: list[dict[str, object]] = []

    def measure(runtime: str, name: str, phase: str, cmd: list[str], rep: int) -> None:
        row: dict[str, object] = {
            "semantic_generation": (
                "contract-11-6-exact-d1-d7"
                if runtime == "sens-exact"
                else "external-control-v2"
            ),
            "runtime": runtime,
            "workload": name,
            "phase": phase,
            "rep": rep,
            "expected": EXPECTED[name],
            "inner_reps": args.inner_reps if phase == "repeat" else "",
            "i_refs": "",
            "wall_s": "",
        }
        if args.cachegrind:
            row["i_refs"] = instruction_count(cmd)
        row["wall_s"] = f"{wall_seconds(cmd):.9f}"
        rows.append(row)

    for rep in range(1, args.reps + 1):
        for name in selected:
            py = str(py_files[name])
            measure(
                "cpython",
                name,
                "full",
                [args.python, str(PHASES_DRIVER), py, "full"],
                rep,
            )
            measure(
                "cpython",
                name,
                "ready",
                [args.python, str(PHASES_DRIVER), py, "ready"],
                rep,
            )
            measure(
                "cpython",
                name,
                "repeat",
                [
                    args.python,
                    str(PHASES_DRIVER),
                    py,
                    "repeat",
                    str(args.inner_reps),
                ],
                rep,
            )
            if want_sens:
                runner = str(args.sens_runner.resolve())
                measure(
                    "sens-exact",
                    name,
                    "full",
                    [runner, str(sens_files[name])],
                    rep,
                )
        print(f"[measure] rep {rep}/{args.reps}")

    args.out.mkdir(parents=True, exist_ok=True)
    fields = [
        "semantic_generation",
        "runtime",
        "workload",
        "phase",
        "rep",
        "expected",
        "inner_reps",
        "i_refs",
        "wall_s",
    ]
    tsv_path = args.out / "steady-full.tsv"
    with tsv_path.open("w", encoding="utf-8") as fh:
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[f]) for f in fields) + "\n")

    steady_lines = [
        "# Derived steady = (median(repeat) − median(ready)) / inner_reps",
        "",
        "Only rows where both ready and repeat exist. Primary metric follows --cachegrind.",
        "",
        "| workload | runtime | ready | repeat | steady/call | metric |",
        "|---|---|---:|---:|---:|---|",
    ]
    metric = "i_refs" if args.cachegrind else "wall_s"
    steady_ratios: list[float] = []

    for name in selected:
        for runtime in ("cpython", "sens-exact"):
            ready_vals = [
                float(r[metric])
                for r in rows
                if r["runtime"] == runtime
                and r["workload"] == name
                and r["phase"] == "ready"
                and r[metric] != ""
            ]
            repeat_vals = [
                float(r[metric])
                for r in rows
                if r["runtime"] == runtime
                and r["workload"] == name
                and r["phase"] == "repeat"
                and r[metric] != ""
            ]
            if not ready_vals or not repeat_vals:
                continue
            ready_m = statistics.median(ready_vals)
            repeat_m = statistics.median(repeat_vals)
            delta = repeat_m - ready_m
            if delta <= 0:
                steady_lines.append(
                    f"| {name} | {runtime} | {ready_m:.0f} | {repeat_m:.0f} | "
                    f"INVALID delta={delta} | {metric} |"
                )
                continue
            per_call = delta / args.inner_reps
            steady_lines.append(
                f"| {name} | {runtime} | {ready_m:.4g} | {repeat_m:.4g} | "
                f"{per_call:.4g} | {metric} |"
            )
            if runtime == "cpython":
                steady_ratios.append(per_call)

    report = "\n".join(steady_lines) + "\n"
    (args.out / "steady-derived.md").write_text(report, encoding="utf-8")

    env = {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": git_fact("rev-parse", "HEAD"),
        "agent": "grok-bench-coord",
        "suite": "sens-bench-steady",
        "purpose": "matched ready/repeat; complements #3601 full-only lane",
        "python": sys.version,
        "platform": platform.platform(),
        "cachegrind": args.cachegrind,
        "reps": args.reps,
        "inner_reps": args.inner_reps,
        "cases": list(selected),
        "params": {n: PARAMS[n] for n in selected},
        "sens_runner": str(args.sens_runner) if want_sens else None,
        "note": (
            "SENS multi-mode ready/repeat not in #3601 binary; "
            "sens-exact rows are phase=full only until runner grows modes."
        ),
    }
    (args.out / "environment.json").write_text(
        json.dumps(env, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(report)
    print(f"results: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
