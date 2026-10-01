#!/usr/bin/env python3
"""#1546 load-format A/B: SENS FASL vs CPython .py vs CPython .pyc.

This is format/load evidence, not a current D1-D4 whole-language claim.
The SENS lane is explicitly tagged historical-function8-fasl until #1668
replays the shared corpus onto ratified exact-width D1-D4.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import platform
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_RUN = ROOT / "benchmarks" / "cross-language" / "run.py"
PYC_DRIVER = ROOT / "benchmarks" / "cross-language" / "cpython_pyc_driver.py"


def load_base():
    spec = importlib.util.spec_from_file_location("cross_language_base", BASE_RUN)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_RUN}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_pyc(python: str, source: Path, target: Path) -> None:
    code = (
        "import py_compile,sys;"
        "py_compile.compile(sys.argv[1],cfile=sys.argv[2],doraise=True,optimize=0)"
    )
    subprocess.run(
        [python, "-c", code, str(source), str(target)],
        check=True,
        capture_output=True,
        text=True,
    )

def median(values: list[int]) -> int:
    return int(statistics.median(values))


def geomean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_version(command: list[str]) -> str:
    proc = subprocess.run(command, check=True, capture_output=True, text=True)
    return (proc.stdout or proc.stderr).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens-bench", required=True, type=Path)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")

    base = load_base()
    sens_surface = base.load_sens_surface_module()
    workdir = Path(tempfile.mkdtemp(prefix="sens-load-formats-"))

    expected_by_name: dict[str, str] = {}
    for name in base.CASES:
        workload = sens_surface.WORKLOADS[name]
        params = base.PARAMS[name]
        expected = workload["expected"](params)
        expected_by_name[name] = expected

        (workdir / f"{name}-sens.setup.lisp").write_text(
            sens_surface.render(workload["setup"], "sens", params),
            encoding="utf-8",
        )
        (workdir / f"{name}-sens.call.lisp").write_text(
            sens_surface.render(workload["call"], "sens", params) + "\n",
            encoding="utf-8",
        )
        py_file = workdir / f"{name}.py"
        py_file.write_text(base.python_source(name, params), encoding="utf-8")
        (workdir / f"{name}.expected").write_text(expected + "\n", encoding="utf-8")

        base.run_checked(
            [str(args.sens_bench), str(workdir), name, "sens", "encode"]
        )
        compile_pyc(args.python, py_file, workdir / f"{name}.pyc")

    # Correctness before timing.
    for name in base.CASES:
        expected = expected_by_name[name]
        base.run_checked(
            [str(args.sens_bench), str(workdir), name, "sens", "full"]
        )
        base.run_checked(
            [args.python, str(workdir / f"{name}.py")],
            expected=expected,
        )
        base.run_checked(
            [args.python, str(PYC_DRIVER), str(workdir / f"{name}.pyc"), "full"],
            expected=expected,
        )
        print(f"[check] {name}: SENS=OK source=OK pyc=OK expected={expected}")

    sens_startup = [
        base.instruction_count(
            [str(args.sens_bench), str(workdir), "empty", "-"]
        )
        for _ in range(args.reps)
    ]
    py_startup = [
        base.instruction_count([args.python, "-c", "pass"])
        for _ in range(args.reps)
    ]
    sens_empty = median(sens_startup)
    py_empty = median(py_startup)

    rows = []
    raw_rows = []
    for rep, value in enumerate(sens_startup, 1):
        raw_rows.append(("sens", "empty", "startup", rep, value, 0, value))
    for rep, value in enumerate(py_startup, 1):
        raw_rows.append(("cpython", "empty", "startup", rep, value, 0, value))

    for name in base.CASES:
        sens_cmd = [str(args.sens_bench), str(workdir), name, "sens", "load"]
        source_cmd = [
            args.python,
            str(base.CPYTHON_DRIVER),
            str(workdir / f"{name}.py"),
            "load",
        ]
        pyc_cmd = [
            args.python,
            str(PYC_DRIVER),
            str(workdir / f"{name}.pyc"),
            "load",
        ]

        sens_raw = [base.instruction_count(sens_cmd) for _ in range(args.reps)]
        source_raw = [base.instruction_count(source_cmd) for _ in range(args.reps)]
        pyc_raw = [base.instruction_count(pyc_cmd) for _ in range(args.reps)]

        sens_net_samples = [raw - startup for raw, startup in zip(sens_raw, sens_startup)]
        source_net_samples = [raw - startup for raw, startup in zip(source_raw, py_startup)]
        pyc_net_samples = [raw - startup for raw, startup in zip(pyc_raw, py_startup)]

        sens_net = median(sens_net_samples)
        source_net = median(source_net_samples)
        pyc_net = median(pyc_net_samples)

        for rep in range(args.reps):
            raw_rows.append(("sens-fasl", name, "load", rep + 1, sens_raw[rep], sens_startup[rep], sens_net_samples[rep]))
            raw_rows.append(("cpython-source", name, "load", rep + 1, source_raw[rep], py_startup[rep], source_net_samples[rep]))
            raw_rows.append(("cpython-pyc-direct", name, "load", rep + 1, pyc_raw[rep], py_startup[rep], pyc_net_samples[rep]))

        fasl_bytes = sum(
            (workdir / f"{name}-sens.{part}.fasl").stat().st_size
            for part in ("setup", "call")
        )
        source_bytes = (workdir / f"{name}.py").stat().st_size
        pyc_bytes = (workdir / f"{name}.pyc").stat().st_size

        rows.append(
            {
                "workload": name,
                "sens_i_refs": sens_net,
                "cpython_source_i_refs": source_net,
                "cpython_pyc_i_refs": pyc_net,
                "source_over_sens": source_net / sens_net,
                "pyc_over_sens": pyc_net / sens_net,
                "source_over_pyc": source_net / pyc_net,
                "sens_fasl_bytes": fasl_bytes,
                "cpython_source_bytes": source_bytes,
                "cpython_pyc_bytes": pyc_bytes,
            }
        )
        print(
            f"[measure] {name}: sens={sens_net} source={source_net} pyc={pyc_net}"
        )

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "load-formats.tsv").open("w", encoding="utf-8") as fh:
        fields = list(rows[0].keys())
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[field]) for field in fields) + "\n")

    with (args.out / "load-formats-raw.tsv").open("w", encoding="utf-8") as fh:
        fh.write("implementation\tworkload\tmode\trep\traw_i_refs\tstartup_i_refs\tnet_i_refs\n")
        for row in raw_rows:
            fh.write("\t".join(map(str, row)) + "\n")

    version = base.run_checked([args.python, "--version"])
    environment = {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": base.git_fact("rev-parse", "HEAD"),
        "python": (version.stdout or version.stderr).strip(),
        "valgrind": command_version(["valgrind", "--version"]),
        "rustc": command_version(["rustc", "--version"]),
        "sens_binary_sha256": sha256(args.sens_bench.resolve()),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": base.os.cpu_count(),
        "reps": args.reps,
        "sens_semantic_generation": "historical-function8-fasl",
        "sens_current_d1_d4_claim": False,
        "cpython_pyc_lane": "direct header+marshal code-object decode",
        "cases": list(base.CASES),
    }
    (args.out / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Load formats: SENS FASL vs CPython source vs CPython .pyc",
        "",
        "Primary metric: Cachegrind I refs, median repeated runs, process startup subtracted.",
        "",
        "> SENS lane is historical Function8 FASL, not current D1-D4 whole-program evidence.",
        "",
        f"Startup I refs: SENS {sens_empty:,}; CPython {py_empty:,}.",
        "",
        "| workload | SENS FASL | CPython source | CPython .pyc | source/SENS | pyc/SENS | source/pyc |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['workload']} | {row['sens_i_refs']:,} | "
            f"{row['cpython_source_i_refs']:,} | {row['cpython_pyc_i_refs']:,} | "
            f"x{row['source_over_sens']:.2f} | x{row['pyc_over_sens']:.2f} | "
            f"x{row['source_over_pyc']:.2f} |"
        )

    lines += [
        "",
        f"Geomean source/SENS: **x{geomean([row['source_over_sens'] for row in rows]):.2f}**.",
        f"Geomean pyc/SENS: **x{geomean([row['pyc_over_sens'] for row in rows]):.2f}**.",
        f"Geomean source/pyc: **x{geomean([row['source_over_pyc'] for row in rows]):.2f}**.",
        "",
        "## Artifact bytes",
        "",
        "| workload | SENS FASL | CPython .py | CPython .pyc |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['workload']} | {row['sens_fasl_bytes']:,} | "
            f"{row['cpython_source_bytes']:,} | {row['cpython_pyc_bytes']:,} |"
        )

    lines += [
        "",
        "Interpretation boundary:",
        "- CPython source lane = read UTF-8 + compile().",
        "- CPython .pyc lane = validate magic/header + marshal code object; no import-system/module setup.",
        "- SENS lane = decode prebuilt historical Function8 FASL; encode excluded.",
        "- Fresh D1-D4 comparison is blocked on #1668 and must replace, not relabel, the SENS lane.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
