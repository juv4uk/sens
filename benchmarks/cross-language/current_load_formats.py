#!/usr/bin/env python3
"""Current Contract 11.5 load comparison: exact-domain SENS vs CPython.

This replaces the historical Function8 load claim for the shared five-workload
corpus. It compares concrete implementation phases on one host:

SENS:
  startup          process only
  core             current Core bootstrap
  load             exact-domain source read + parse + lower, no execution
  cold-ready       Core bootstrap + setup definitions, no benchmark call

CPython source:
  startup          process only
  load             UTF-8 read + compile(), no module execution
  cold-ready       load + execute module definitions, no bench() call

CPython pyc:
  load             header validation + marshal code-object decode
  cold-ready       load + execute module definitions, no bench() call

Cachegrind I refs are primary. Wall time is auxiliary. All process-level load
and ready rows are reported both raw and startup-subtracted.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import platform
import py_compile
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import current_sens as sens
import current_sens_phases as sens_phases

ROOT = Path(__file__).resolve().parents[2]
RUN_PY = ROOT / "benchmarks" / "cross-language" / "run.py"
CPYTHON_DRIVER = ROOT / "benchmarks" / "cross-language" / "cpython_driver.py"
PYC_DRIVER = ROOT / "benchmarks" / "cross-language" / "cpython_pyc_driver.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module(RUN_PY, "cross_language_run")


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
        raise RuntimeError(
            f"cachegrind failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    match = re.search(r"I\s+refs:\s*([\d,]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"missing Cachegrind I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def wall(cmd: list[str]) -> float:
    started = time.perf_counter()
    proc = subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    return elapsed


def checked(cmd: list[str], expected: str | None = None) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    if expected is not None:
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        got = lines[-1] if lines else ""
        if got != expected:
            raise RuntimeError(
                f"wrong answer: {' '.join(cmd)} expected={expected!r} got={got!r}"
            )


def median(rows: list[dict[str, object]], runtime: str, workload: str, phase: str, field: str) -> float:
    values = [
        float(row[field])
        for row in rows
        if row["runtime"] == runtime
        and row["workload"] == workload
        and row["phase"] == phase
    ]
    if not values:
        raise KeyError((runtime, workload, phase, field))
    return statistics.median(values)


def geomean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens-runner", required=True)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")

    runner = str(Path(args.sens_runner).resolve())
    workdir = Path(tempfile.mkdtemp(prefix="sens-current-load-"))

    files: dict[str, dict[str, Path]] = {}
    for name in sens.CASES:
        setup, call = sens_phases.setup_call(name)
        expected = sens.EXPECTED[name]

        setup_path = workdir / f"{name}.setup.lisp"
        call_path = workdir / f"{name}.call.lisp"
        py_path = workdir / f"{name}.py"
        pyc_path = workdir / f"{name}.pyc"

        setup_path.write_text(setup, encoding="utf-8")
        call_path.write_text(call, encoding="utf-8")
        py_path.write_text(
            base.python_source(name, {"N": sens.PARAMS[name]}),
            encoding="utf-8",
        )
        py_compile.compile(str(py_path), cfile=str(pyc_path), doraise=True, optimize=0)

        files[name] = {
            "setup": setup_path,
            "call": call_path,
            "py": py_path,
            "pyc": pyc_path,
        }

        checked([runner, "steady", str(setup_path), str(call_path), "1"], expected)
        checked([args.python, str(py_path)], expected)
        checked([args.python, str(PYC_DRIVER), str(pyc_path), "full"], expected)
        print(f"[check] {name}: sens/source/pyc OK expected={expected}")

    rows: list[dict[str, object]] = []

    def measure(runtime: str, workload: str, phase: str, cmd: list[str]) -> None:
        for rep in range(1, args.reps + 1):
            rows.append(
                {
                    "runtime": runtime,
                    "workload": workload,
                    "phase": phase,
                    "rep": rep,
                    "i_refs": irefs(cmd),
                    "wall_s": wall(cmd),
                }
            )

    measure("sens-exact", "__global__", "startup", [runner, "startup"])
    measure("sens-exact", "__global__", "core", [runner, "load"])
    measure("cpython-source", "__global__", "startup", [args.python, "-c", "pass"])
    # .pyc runs in the same CPython process implementation, so it shares startup.

    for name in sens.CASES:
        f = files[name]
        measure(
            "sens-exact",
            name,
            "load",
            [runner, "lower", str(f["setup"]), str(f["call"])],
        )
        measure(
            "sens-exact",
            name,
            "cold-ready",
            [runner, "setup", str(f["setup"])],
        )
        measure(
            "cpython-source",
            name,
            "load",
            [args.python, str(CPYTHON_DRIVER), str(f["py"]), "load"],
        )
        measure(
            "cpython-source",
            name,
            "cold-ready",
            [args.python, str(CPYTHON_DRIVER), str(f["py"]), "ready"],
        )
        measure(
            "cpython-pyc",
            name,
            "load",
            [args.python, str(PYC_DRIVER), str(f["pyc"]), "load"],
        )
        measure(
            "cpython-pyc",
            name,
            "cold-ready",
            [args.python, str(PYC_DRIVER), str(f["pyc"]), "ready"],
        )

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "current-load-raw.tsv").open("w", encoding="utf-8") as fh:
        fields = ("runtime", "workload", "phase", "rep", "i_refs", "wall_s")
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[field]) for field in fields) + "\n")

    sens_start_i = median(rows, "sens-exact", "__global__", "startup", "i_refs")
    sens_start_w = median(rows, "sens-exact", "__global__", "startup", "wall_s")
    core_i = median(rows, "sens-exact", "__global__", "core", "i_refs")
    core_w = median(rows, "sens-exact", "__global__", "core", "wall_s")
    py_start_i = median(rows, "cpython-source", "__global__", "startup", "i_refs")
    py_start_w = median(rows, "cpython-source", "__global__", "startup", "wall_s")

    def net(runtime: str, name: str, phase: str, field: str) -> float:
        raw = median(rows, runtime, name, phase, field)
        if runtime == "sens-exact":
            startup = sens_start_i if field == "i_refs" else sens_start_w
        else:
            startup = py_start_i if field == "i_refs" else py_start_w
        return raw - startup

    lines = [
        "# Current exact-domain load: SENS vs CPython source/.pyc",
        "",
        "Primary metric: Cachegrind I refs. Wall time is auxiliary.",
        "All workload load/ready values below subtract the implementation process-startup median.",
        "",
        "## Startup / Core",
        "",
        "| phase | I refs | wall, ms |",
        "|---|---:|---:|",
        f"| SENS process startup | {sens_start_i:,.0f} | {sens_start_w * 1000:.3f} |",
        f"| SENS Core bootstrap raw | {core_i:,.0f} | {core_w * 1000:.3f} |",
        f"| SENS Core bootstrap net | {core_i - sens_start_i:,.0f} | {(core_w - sens_start_w) * 1000:.3f} |",
        f"| CPython process startup | {py_start_i:,.0f} | {py_start_w * 1000:.3f} |",
        "",
        "## Program load — no definitions executed",
        "",
        "| workload | SENS exact parse+lower | CPython source read+compile | CPython .pyc decode | source/SENS | pyc/SENS |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    source_ratios: list[float] = []
    pyc_ratios: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "load", "i_refs")
        ps = net("cpython-source", name, "load", "i_refs")
        pc = net("cpython-pyc", name, "load", "i_refs")
        source_ratios.append(ps / s)
        pyc_ratios.append(pc / s)
        lines.append(
            f"| {name} | {s:,.0f} | {ps:,.0f} | {pc:,.0f} | {ps / s:.3f}x | {pc / s:.3f}x |"
        )

    lines += [
        "",
        f"Geomean CPython source / SENS load: **{geomean(source_ratios):.3f}x**.",
        f"Geomean CPython .pyc / SENS load: **{geomean(pyc_ratios):.3f}x**.",
        "",
        "## Cold ready — definitions installed, benchmark call not executed",
        "",
        "| workload | SENS Core+setup | CPython source ready | CPython .pyc ready | source/SENS | pyc/SENS |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    source_ready_ratios: list[float] = []
    pyc_ready_ratios: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "cold-ready", "i_refs")
        ps = net("cpython-source", name, "cold-ready", "i_refs")
        pc = net("cpython-pyc", name, "cold-ready", "i_refs")
        source_ready_ratios.append(ps / s)
        pyc_ready_ratios.append(pc / s)
        lines.append(
            f"| {name} | {s:,.0f} | {ps:,.0f} | {pc:,.0f} | {ps / s:.3f}x | {pc / s:.3f}x |"
        )

    lines += [
        "",
        f"Geomean CPython source / SENS cold-ready: **{geomean(source_ready_ratios):.3f}x**.",
        f"Geomean CPython .pyc / SENS cold-ready: **{geomean(pyc_ready_ratios):.3f}x**.",
        "",
        "Interpretation boundary:",
        "- SENS load is exact-domain source read + parse + lower for setup+call; Core bootstrap is excluded from this load row.",
        "- SENS cold-ready includes current Core bootstrap plus exact-domain setup definition installation.",
        "- CPython source load is UTF-8 read + compile(), no module execution.",
        "- CPython .pyc load validates the header and unmarshals the code object, no module execution.",
        "- CPython ready executes definitions under a non-__main__ namespace, so bench() is not called.",
        "- Warm resident-Core program setup is a separate slope experiment in #3513/#3544 and must not be inferred from cold-ready.",
        "- No historical Sens8/Sid8/Function8 SENS path participates.",
        "",
    ]

    report = "\n".join(lines)
    (args.out / "current-load-report.md").write_text(report, encoding="utf-8")
    (args.out / "environment.json").write_text(
        json.dumps(
            {
                "semantic_generation": "contract-11-5-exact-d1-d6",
                "sens_source_heads": {
                    "D3_EQ": sens.EQ,
                    "D3_COND": sens.COND,
                    "D4_LAMBDA": sens.LAMBDA,
                    "D4_DEFINE": sens.DEFINE,
                    "D5_PLUS": sens.PLUS,
                    "D5_DIFFERENCE": sens.DIFFERENCE,
                },
                "legacy_function8_used": False,
                "python": subprocess.run(
                    [args.python, "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "platform": platform.platform(),
                "reps": args.reps,
                "cases": list(sens.CASES),
                "params": sens.PARAMS,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
