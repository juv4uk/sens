#!/usr/bin/env python3
"""Current Contract 11.5 load comparison: exact-domain SENS vs Racket CS.

Racket lanes:
- load: read source forms + compile a top-level begin, no instantiation;
- cold-ready: compile + instantiate definitions in a fresh base namespace,
  no benchmark call.

SENS lanes match #3562/#3570:
- load: exact-domain read + parse + lower, no execution;
- cold-ready: Core bootstrap + parse/lower whole program + setup definitions,
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

ROOT = Path(__file__).resolve().parents[2]
RACKET_DRIVER = ROOT / "benchmarks" / "cross-language" / "racket_phase_driver.rkt"


def racket_source(name: str) -> str:
    n = sens.PARAMS[name]
    if name == "fib":
        return f"""(define (fib n)
  (cond [(zero? n) 0]
        [(= n 1) 1]
        [else (+ (fib (sub1 n)) (fib (- n 2)))]))

(define (bench)
  (fib {n}))
"""
    if name == "loop":
        return f"""(define (bench-loop n acc)
  (if (zero? n) acc (bench-loop (sub1 n) (+ acc 2))))

(define (bench)
  (bench-loop {n} 0))
"""
    if name == "ackermann":
        return f"""(define (ack m n)
  (cond [(zero? m) (add1 n)]
        [(zero? n) (ack (sub1 m) 1)]
        [else (ack (sub1 m) (ack m (sub1 n)))]))

(define (bench)
  (ack 3 {n}))
"""
    if name == "closures":
        return f"""(define (make-adder k)
  (lambda (x) (+ x k)))

(define add3 (make-adder 3))

(define (bench-loop n acc)
  (if (zero? n) acc (bench-loop (sub1 n) (add3 acc))))

(define (bench)
  (bench-loop {n} 0))
"""
    if name == "evenodd":
        return f"""(define (is-even n)
  (if (zero? n) #t (is-odd (sub1 n))))

(define (is-odd n)
  (if (zero? n) #f (is-even (sub1 n))))

(define (bench)
  (if (is-even {n}) 1 0))
"""
    raise KeyError(name)


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
    ap.add_argument("--racket", default="racket")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")

    version = subprocess.run(
        [args.racket, "--version"], capture_output=True, text=True, check=True
    )
    version_text = (version.stdout or version.stderr).strip()
    if "[cs]" not in version_text.lower():
        raise RuntimeError(f"Racket CS required, got {version_text}")

    runner = str(Path(args.sens_runner).resolve())
    workdir = Path(tempfile.mkdtemp(prefix="sens-racket-load-"))
    files: dict[str, dict[str, Path]] = {}

    for name in sens.CASES:
        setup, call = sens_phases.setup_call(name)
        s_setup = workdir / f"{name}.setup.lisp"
        s_call = workdir / f"{name}.call.lisp"
        rkt = workdir / f"{name}.rkt"

        s_setup.write_text(setup, encoding="utf-8")
        s_call.write_text(call, encoding="utf-8")
        rkt.write_text(racket_source(name), encoding="utf-8")

        files[name] = {"setup": s_setup, "call": s_call, "racket": rkt}

        expected = sens.EXPECTED[name]
        checked([runner, "steady", str(s_setup), str(s_call), "1"], expected)
        checked([args.racket, str(RACKET_DRIVER), str(rkt), "full"], expected)
        print(f"[check] {name}: SENS/Racket OK expected={expected}")

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
    measure("racket-cs", "__global__", "startup", [args.racket, "-e", "(void)"])

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
        measure(
            "racket-cs",
            name,
            "load",
            [args.racket, str(RACKET_DRIVER), str(f["racket"]), "load"],
        )
        measure(
            "racket-cs",
            name,
            "cold-ready",
            [args.racket, str(RACKET_DRIVER), str(f["racket"]), "ready"],
        )

    args.out.mkdir(parents=True, exist_ok=True)
    fields = ("runtime", "workload", "phase", "rep", "i_refs", "wall_s")
    with (args.out / "racket-load-raw.tsv").open("w", encoding="utf-8") as fh:
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
    racket_start_i = med("racket-cs", "__global__", "startup", "i_refs")
    sens_start_w = med("sens-exact", "__global__", "startup", "wall_s")
    racket_start_w = med("racket-cs", "__global__", "startup", "wall_s")

    def net(runtime: str, name: str, phase: str, field: str) -> float:
        raw = med(runtime, name, phase, field)
        if runtime == "sens-exact":
            start = sens_start_i if field == "i_refs" else sens_start_w
        else:
            start = racket_start_i if field == "i_refs" else racket_start_w
        return raw - start

    lines = [
        "# Current exact-domain load: SENS vs Racket CS",
        "",
        "Primary metric: Cachegrind I refs. Wall time is auxiliary.",
        "",
        f"SENS startup: {sens_start_i:,.0f} I refs / {sens_start_w * 1000:.3f} ms.",
        f"Racket CS startup: {racket_start_i:,.0f} I refs / {racket_start_w * 1000:.3f} ms.",
        "",
        "## Load — source compiled, definitions not instantiated",
        "",
        "| workload | SENS parse+lower | Racket read+compile | Racket/SENS |",
        "|---|---:|---:|---:|",
    ]

    load_ratios: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "load", "i_refs")
        r = net("racket-cs", name, "load", "i_refs")
        load_ratios.append(r / s)
        lines.append(f"| {name} | {s:,.0f} | {r:,.0f} | {r / s:.3f}x |")

    lines += [
        "",
        f"Geomean Racket/SENS load: **{geomean(load_ratios):.3f}x**.",
        "",
        "## Cold ready — definitions instantiated, benchmark call not executed",
        "",
        "| workload | SENS Core+ready | Racket compile+instantiate | Racket/SENS |",
        "|---|---:|---:|---:|",
    ]

    ready_ratios: list[float] = []
    for name in sens.CASES:
        s = net("sens-exact", name, "cold-ready", "i_refs")
        r = net("racket-cs", name, "cold-ready", "i_refs")
        ready_ratios.append(r / s)
        lines.append(f"| {name} | {s:,.0f} | {r:,.0f} | {r / s:.3f}x |")

    lines += [
        "",
        f"Geomean Racket/SENS cold-ready: **{geomean(ready_ratios):.3f}x**.",
        "",
        "Interpretation boundary:",
        "- Racket load reads all forms and compiles one top-level begin in a fresh base namespace; it does not instantiate definitions.",
        "- Racket ready evaluates the compiled form in that namespace; bench is defined but not called.",
        "- This slice deliberately does not claim a .zo cached-artifact row; add it only when artifact load can be separated reproducibly from module instantiation.",
        "- SENS load is exact-domain read + parse + lower, no execution.",
        "- SENS cold-ready includes Core bootstrap and setup installation with call prepared but not executed.",
        "- Warm resident-Core SENS remains a separate slope experiment.",
        "- No historical Sens8/Sid8/Function8 path participates.",
        "",
    ]

    report = "\n".join(lines)
    (args.out / "racket-load-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
