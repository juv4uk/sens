#!/usr/bin/env python3
"""Current Contract 11.5 load comparison: exact-domain SENS vs SBCL.

SBCL phases:
- startup: empty SBCL process;
- source-compile: COMPILE-FILE source -> FASL, artifact emission included;
- source-ready: LOAD source definitions, no bench call;
- fasl-ready: LOAD precompiled FASL definitions, no bench call.

SENS phases:
- startup;
- exact program load = read + parse + lower, no execution;
- cold-ready = Core bootstrap + whole-program parse/lower + setup definitions,
  call prepared but not executed.

Cachegrind I refs are primary. Wall time is auxiliary.
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import current_sens as sens
import current_sens_phases as sens_phases


def lisp_source(name: str) -> str:
    n = sens.PARAMS[name]
    if name == "fib":
        return f"""(defun fib (n)
  (cond ((= n 0) 0)
        ((= n 1) 1)
        (t (+ (fib (- n 1)) (fib (- n 2))))))

(defun bench ()
  (fib {n}))
"""
    if name == "loop":
        return f"""(defun bench-loop (n acc)
  (if (= n 0) acc (bench-loop (- n 1) (+ acc 2))))

(defun bench ()
  (bench-loop {n} 0))
"""
    if name == "ackermann":
        return f"""(defun ack (m n)
  (cond ((= m 0) (+ n 1))
        ((= n 0) (ack (- m 1) 1))
        (t (ack (- m 1) (ack m (- n 1))))))

(defun bench ()
  (ack 3 {n}))
"""
    if name == "closures":
        return f"""(defun make-adder (k)
  (lambda (x) (+ x k)))

(defparameter *add3* (make-adder 3))

(defun bench-loop (n acc)
  (if (= n 0) acc (bench-loop (- n 1) (funcall *add3* acc))))

(defun bench ()
  (bench-loop {n} 0))
"""
    if name == "evenodd":
        return f"""(defun is-even (n)
  (if (= n 0) t (is-odd (- n 1))))

(defun is-odd (n)
  (if (= n 0) nil (is-even (- n 1))))

(defun bench ()
  (if (is-even {n}) 1 0))
"""
    raise KeyError(name)


def cl_string(path: Path) -> str:
    return '"' + str(path).replace("\\", "\\\\").replace('"', '\\"') + '"'


def sbcl_base(sbcl: str) -> list[str]:
    return [sbcl, "--noinform", "--disable-debugger"]


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
            f"cachegrind failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
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


def geomean(values: list[float]) -> float:
    return math.exp(sum(math.log(v) for v in values) / len(values))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens-runner", required=True)
    ap.add_argument("--sbcl", default="sbcl")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")

    version = subprocess.run(
        [args.sbcl, "--version"], capture_output=True, text=True, check=True
    )
    version_text = (version.stdout or version.stderr).strip()
    if "SBCL" not in version_text.upper():
        raise RuntimeError(f"SBCL required, got {version_text}")

    runner = str(Path(args.sens_runner).resolve())
    workdir = Path(tempfile.mkdtemp(prefix="sens-sbcl-load-"))
    files: dict[str, dict[str, Path]] = {}

    for name in sens.CASES:
        setup, call = sens_phases.setup_call(name)
        s_setup = workdir / f"{name}.setup.lisp"
        s_call = workdir / f"{name}.call.lisp"
        src = workdir / f"{name}.cl"
        fasl = workdir / f"{name}.fasl"

        s_setup.write_text(setup, encoding="utf-8")
        s_call.write_text(call, encoding="utf-8")
        src.write_text(lisp_source(name), encoding="utf-8")

        compile_expr = f"(compile-file {cl_string(src)} :output-file {cl_string(fasl)})"
        checked(sbcl_base(args.sbcl) + ["--eval", compile_expr, "--eval", "(sb-ext:quit)"])

        files[name] = {
            "setup": s_setup,
            "call": s_call,
            "src": src,
            "fasl": fasl,
        }

        expected = sens.EXPECTED[name]
        checked([runner, "steady", str(s_setup), str(s_call), "1"], expected)
        checked(
            sbcl_base(args.sbcl)
            + [
                "--load",
                str(src),
                "--eval",
                '(format t "~a~%" (bench))',
                "--eval",
                "(sb-ext:quit)",
            ],
            expected,
        )
        checked(
            sbcl_base(args.sbcl)
            + [
                "--load",
                str(fasl),
                "--eval",
                '(format t "~a~%" (bench))',
                "--eval",
                "(sb-ext:quit)",
            ],
            expected,
        )
        print(f"[check] {name}: SENS/SBCL source/FASL OK expected={expected}")

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
    measure(
        "sbcl",
        "__global__",
        "startup",
        sbcl_base(args.sbcl) + ["--eval", "(sb-ext:quit)"],
    )

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
            [runner, "ready", str(f["setup"]), str(f["call"])],
        )

        measured_fasl = workdir / f"{name}.measured.fasl"
        compile_expr = (
            f"(compile-file {cl_string(f['src'])} :output-file {cl_string(measured_fasl)})"
        )
        measure(
            "sbcl",
            name,
            "source-compile",
            sbcl_base(args.sbcl)
            + ["--eval", compile_expr, "--eval", "(sb-ext:quit)"],
        )
        measure(
            "sbcl",
            name,
            "source-ready",
            sbcl_base(args.sbcl)
            + ["--load", str(f["src"]), "--eval", "(sb-ext:quit)"],
        )
        measure(
            "sbcl",
            name,
            "fasl-ready",
            sbcl_base(args.sbcl)
            + ["--load", str(f["fasl"]), "--eval", "(sb-ext:quit)"],
        )

    args.out.mkdir(parents=True, exist_ok=True)
    fields = ("runtime", "workload", "phase", "rep", "i_refs", "wall_s")
    with (args.out / "sbcl-load-raw.tsv").open("w", encoding="utf-8") as fh:
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[f]) for f in fields) + "\n")

    def med(runtime: str, workload: str, phase: str, field: str) -> float:
        values = [
            float(r[field])
            for r in rows
            if r["runtime"] == runtime
            and r["workload"] == workload
            and r["phase"] == phase
        ]
        return statistics.median(values)

    sens_start_i = med("sens-exact", "__global__", "startup", "i_refs")
    sbcl_start_i = med("sbcl", "__global__", "startup", "i_refs")
    sens_start_w = med("sens-exact", "__global__", "startup", "wall_s")
    sbcl_start_w = med("sbcl", "__global__", "startup", "wall_s")

    def net(runtime: str, name: str, phase: str, field: str) -> float:
        raw = med(runtime, name, phase, field)
        if runtime == "sens-exact":
            start = sens_start_i if field == "i_refs" else sens_start_w
        else:
            start = sbcl_start_i if field == "i_refs" else sbcl_start_w
        return raw - start

    lines = [
        "# Current exact-domain load: SENS vs SBCL",
        "",
        "Primary metric: Cachegrind I refs. Wall time is auxiliary.",
        "",
        f"SENS startup: {sens_start_i:,.0f} I refs / {sens_start_w * 1000:.3f} ms.",
        f"SBCL startup: {sbcl_start_i:,.0f} I refs / {sbcl_start_w * 1000:.3f} ms.",
        "",
        "## Source compile vs SENS program load",
        "",
        "SBCL source-compile includes FASL artifact emission and is therefore not a strict decode-only analogue.",
        "",
        "| workload | SENS parse+lower | SBCL COMPILE-FILE | SBCL/SENS |",
        "|---|---:|---:|---:|",
    ]

    compile_ratios: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "load", "i_refs")
        b = net("sbcl", name, "source-compile", "i_refs")
        compile_ratios.append(b / s)
        lines.append(f"| {name} | {s:,.0f} | {b:,.0f} | {b / s:.3f}x |")

    lines += [
        "",
        f"Geomean SBCL source-compile / SENS load: **{geomean(compile_ratios):.3f}x**.",
        "",
        "## Cold ready — definitions installed, benchmark call not executed",
        "",
        "| workload | SENS Core+ready | SBCL source LOAD | SBCL FASL LOAD | source/SENS | FASL/SENS |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    src_ready_ratios: list[float] = []
    fasl_ready_ratios: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "cold-ready", "i_refs")
        bs = net("sbcl", name, "source-ready", "i_refs")
        bf = net("sbcl", name, "fasl-ready", "i_refs")
        src_ready_ratios.append(bs / s)
        fasl_ready_ratios.append(bf / s)
        lines.append(
            f"| {name} | {s:,.0f} | {bs:,.0f} | {bf:,.0f} | {bs / s:.3f}x | {bf / s:.3f}x |"
        )

    lines += [
        "",
        f"Geomean SBCL source-ready / SENS cold-ready: **{geomean(src_ready_ratios):.3f}x**.",
        f"Geomean SBCL FASL-ready / SENS cold-ready: **{geomean(fasl_ready_ratios):.3f}x**.",
        "",
        "Interpretation boundary:",
        "- SBCL COMPILE-FILE produces a FASL during the measured source-compile row; it is not a pure read/decode row.",
        "- SBCL LOAD of source or FASL installs definitions, so those rows correspond to ready rather than decode-only.",
        "- The FASL used for the cached-ready row is produced before timing by the same pinned SBCL.",
        "- SENS load is exact-domain read + parse + lower, no execution.",
        "- SENS cold-ready includes Core bootstrap and setup installation with call prepared but not executed.",
        "- Warm resident-Core SENS remains a separate slope experiment.",
        "- No historical Sens8/Sid8/Function8 path participates.",
        "",
    ]

    report = "\n".join(lines)
    (args.out / "sbcl-load-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
