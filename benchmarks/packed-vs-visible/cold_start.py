#!/usr/bin/env python3
"""New-process SENS startup benchmark, on the SAME hosted CPU and executable.

Each sample launches an independent Rust process. Inner time is separately
reported by that process; external wall time includes OS launch, loader, Rust
runtime and output capture. Neither mode measures a cold page cache.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "sens-cold-process-bootstrap/v1"
MODES = ("noop", "bare-session", "session", "bare-d3", "d3", "bare-core", "bare-core-reuse", "core", "core-d3")
EXPECTED = {
    "noop": "NONE",
    "bare-session": "BARE_SESSION",
    "session": "SESSION",
    "bare-d3": "BARE_D3_EMPTY",
    "d3": "D3_EMPTY",
    "bare-core": "BARE_CORE_LOADED",
    "bare-core-reuse": "BARE_CORE_REUSED",
    "core": "CORE_LOADED",
    "core-d3": "CORE_AND_D3_EMPTY",
}


def run_once(binary: Path, mode: str) -> dict:
    started = time.perf_counter_ns()
    try:
        proc = subprocess.run(
            [str(binary), mode],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": repr(exc)}
    wall_ns = time.perf_counter_ns() - started
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": f"exit={proc.returncode}; {proc.stderr.strip()[:900]}",
        }
    kv = dict(
        line.split("=", 1)
        for line in proc.stdout.splitlines()
        if "=" in line
    )
    if kv.get("VALUE") != EXPECTED[mode]:
        return {
            "ok": False,
            "error": f"wrong independent output for {mode}: {kv.get('VALUE')!r}",
        }
    try:
        inner_ns = int(kv["INNER_NS"])
    except (KeyError, ValueError) as exc:
        return {"ok": False, "error": f"invalid Rust timing: {exc}"}
    if inner_ns < 0 or wall_ns < inner_ns:
        return {"ok": False, "error": "internal timer exceeds process wall time"}
    return {"ok": True, "process_wall_ns": wall_ns, "inner_ns": inner_ns}


def median_int(values: list[int]) -> int:
    return round(statistics.median(values))


def cpu_description() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--samples", type=int, default=11)
    ap.add_argument("--warmup", type=int, default=2)
    args = ap.parse_args()
    if args.samples < 5 or args.samples > 51 or args.samples % 2 == 0:
        ap.error("--samples must be odd between 5 and 51")
    if args.warmup < 0 or args.warmup > 10:
        ap.error("--warmup must be between 0 and 10")
    binary = args.probe.resolve()
    if not binary.is_file():
        ap.error(f"release binary missing: {binary}")

    rows: dict[str, dict] = {
        mode: {"mode": mode, "status": "MEASURED", "samples": []}
        for mode in MODES
    }
    # Interleaving modes avoids always measuring session after noisier Core
    # bootstrap. Rotating sequence changes order every round deterministically.
    for rep in range(args.warmup + args.samples):
        order = MODES[rep % len(MODES):] + MODES[:rep % len(MODES)]
        for mode in order:
            row = rows[mode]
            if row["status"] != "MEASURED":
                continue
            sample = run_once(binary, mode)
            if not sample["ok"]:
                row["status"] = "BLOCKED"
                row["reason"] = sample["error"]
                row["samples"] = []
                continue
            if rep >= args.warmup:
                row["samples"].append(
                    {"process_wall_ns": sample["process_wall_ns"], "inner_ns": sample["inner_ns"]}
                )

    for mode, row in rows.items():
        if row["status"] != "MEASURED":
            continue
        if len(row["samples"]) != args.samples:
            row["status"] = "BLOCKED"
            row["reason"] = f"only {len(row['samples'])} of {args.samples} expected samples"
            row["samples"] = []
            continue
        for axis in ("process_wall_ns", "inner_ns"):
            row[f"median_{axis}"] = median_int([s[axis] for s in row["samples"]])

    report = {
        "schema": SCHEMA,
        "source_sha": os.environ.get("GITHUB_SHA", "local"),
        "cpu": cpu_description(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "samples_per_mode": args.samples,
        "warmup_per_mode": args.warmup,
        "qualification": (
            "Fresh process each invocation, warm page cache, external OS+loader+capture wall "
            "versus internal Rust phase; not cold disk, not a memory footprint benchmark"
        ),
        "rows": [rows[mode] for mode in MODES],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "## SENS: cold process / Session / Core4 startup measurements",
        "",
        f"Hosted CPU: `{report['cpu']}`; {args.samples} new processes per mode.",
        "",
        "| Mode | Process wall median (µs) | Inner Rust phase median (µs) | Status |",
        "|---|---:|---:|---|",
    ]
    for row in report["rows"]:
        if row["status"] == "MEASURED":
            lines.append(
                f"| `{row['mode']}` | {row['median_process_wall_ns']/1000:.2f} "
                f"| {row['median_inner_ns']/1000:.2f} | MEASURED |"
            )
        else:
            lines.append(
                f"| `{row['mode']}` | — | — | BLOCKED: {row['reason'].replace('|', '/')} |"
            )
    if all(rows[mode]["status"] == "MEASURED" for mode in ("bare-session", "session")):
        raw_default = rows["session"]["median_inner_ns"]
        raw_bare = rows["bare-session"]["median_inner_ns"]
        if raw_bare > 0:
            lines.extend([
                "",
                f"Observed per-process **inner phase ratio** default/bare: "
                f"{raw_default / raw_bare:.2f}× "
                "(two separately sampled modes, not an OS startup speedup).",
            ])
    if all(rows[mode]["status"] == "MEASURED" for mode in ("bare-core", "core")):
        raw_default = rows["core"]["median_inner_ns"]
        raw_bare = rows["bare-core"]["median_inner_ns"]
        if raw_bare > 0:
            lines.append(
                f"Observed Core4 bootstrap ratio default-session/bare-session: "
                f"{raw_default / raw_bare:.2f}× (both load the same Lisp-owned Core4)."
            )
    lines.extend([
        "",
        "The `bare-core-reuse` inner timer covers **only the second** fresh "
        "Core4 Session within its process after a successful first bootstrap. "
        "Its process-wall metric includes BOTH loads and is not comparable "
        "as a one-load process startup time. Both sessions execute Lisp Core4 "
        "independently; only verified binary decode/lowering may be cached.",
    ])
    lines.extend([
        "",
        "Each process was freshly launched, but **Linux page cache was not cleared**. "
        "Process wall includes OS scheduling, executable loader and pipe capture.",
        "The inner Rust clock excludes those costs. Do not subtract medians to "
        "claim an exact loader cost.",
        "Core4 cases only report MEASURED when the Lisp-owned bootstrap succeeds; "
        "failures are preserved as BLOCKED, not disguised as a timing of an error.",
        "Bare Session skips Lisp macro bootstrap by explicit opt-in; Session::default "
        "still loads the language-owned macro library. Both D3 cases execute "
        "the same exact-domain QUOTE; Core4 loader initializes macros itself.",
        "",
    ])
    summary = "\n".join(lines)
    args.out.with_name("cold-start-summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    if any(rows[mode]["status"] != "MEASURED" for mode in (
        "noop", "bare-session", "session", "bare-d3", "d3"
    )):
        print("BLOCKED: even the fundamental no-op/Session/D3 cold path failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
