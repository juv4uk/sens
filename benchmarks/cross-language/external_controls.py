#!/usr/bin/env python3
"""Contract 11-5 external runtime controls for SENS cross-language work.

This lane intentionally contains no fresh SENS timing row. It establishes
reproducible CPython, Lua 5.4, Racket CS, SBCL and optimized native Rust
controls on the shared five-workload corpus. Current SENS joins only after
the exact-domain D1-D6 correctness gate is GREEN.

This is a benchmark of concrete implementations, not abstract languages.
Correctness is mandatory before any timing row is emitted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASES = ("fib", "loop", "ackermann", "closures", "evenodd")
PARAMS = {
    "fib": 16,
    "loop": 700,
    "ackermann": 3,
    "closures": 700,
    "evenodd": 700,
}
EXPECTED = {
    "fib": "987",
    "loop": "1400",
    "ackermann": "61",
    "closures": "2100",
    "evenodd": "1",
}


def python_source(name: str) -> str:
    n = PARAMS[name]
    limit = max(10_000, n * 4 + 100)
    if name == "fib":
        return f"""import sys
sys.setrecursionlimit({limit})
def fib(n):
    if n == 0: return 0
    if n == 1: return 1
    return fib(n - 1) + fib(n - 2)
print(fib({n}))
"""
    if name == "loop":
        return f"""import sys
sys.setrecursionlimit({limit})
def loop(n, acc):
    if n == 0: return acc
    return loop(n - 1, acc + 2)
print(loop({n}, 0))
"""
    if name == "ackermann":
        return f"""import sys
sys.setrecursionlimit({limit})
def ack(m, n):
    if m == 0: return n + 1
    if n == 0: return ack(m - 1, 1)
    return ack(m - 1, ack(m, n - 1))
print(ack(3, {n}))
"""
    if name == "closures":
        return f"""import sys
sys.setrecursionlimit({limit})
def make_adder(k):
    def add(x): return x + k
    return add
add3 = make_adder(3)
def loop(n, acc):
    if n == 0: return acc
    return loop(n - 1, add3(acc))
print(loop({n}, 0))
"""
    if name == "evenodd":
        return f"""import sys
sys.setrecursionlimit({limit})
def is_even(n):
    if n == 0: return 1
    return is_odd(n - 1)
def is_odd(n):
    if n == 0: return 0
    return is_even(n - 1)
print(is_even({n}))
"""
    raise KeyError(name)


def lua_source(name: str) -> str:
    n = PARAMS[name]
    if name == "fib":
        return f"""local function fib(n)
  if n == 0 then return 0 end
  if n == 1 then return 1 end
  return fib(n - 1) + fib(n - 2)
end
print(fib({n}))
"""
    if name == "loop":
        return f"""local function loop(n, acc)
  if n == 0 then return acc end
  return loop(n - 1, acc + 2)
end
print(loop({n}, 0))
"""
    if name == "ackermann":
        return f"""local ack
ack = function(m, n)
  if m == 0 then return n + 1 end
  if n == 0 then return ack(m - 1, 1) end
  return ack(m - 1, ack(m, n - 1))
end
print(ack(3, {n}))
"""
    if name == "closures":
        return f"""local function make_adder(k)
  return function(x) return x + k end
end
local add3 = make_adder(3)
local function loop(n, acc)
  if n == 0 then return acc end
  return loop(n - 1, add3(acc))
end
print(loop({n}, 0))
"""
    if name == "evenodd":
        return f"""local is_even, is_odd
is_even = function(n)
  if n == 0 then return true end
  return is_odd(n - 1)
end
is_odd = function(n)
  if n == 0 then return false end
  return is_even(n - 1)
end
print(is_even({n}) and 1 or 0)
"""
    raise KeyError(name)


def racket_source(name: str) -> str:
    n = PARAMS[name]
    if name == "fib":
        return f"""#lang racket/base
(define (fib n)
  (cond [(zero? n) 0]
        [(= n 1) 1]
        [else (+ (fib (sub1 n)) (fib (- n 2)))]))
(displayln (fib {n}))
"""
    if name == "loop":
        return f"""#lang racket/base
(define (loop n acc)
  (if (zero? n) acc (loop (sub1 n) (+ acc 2))))
(displayln (loop {n} 0))
"""
    if name == "ackermann":
        return f"""#lang racket/base
(define (ack m n)
  (cond [(zero? m) (add1 n)]
        [(zero? n) (ack (sub1 m) 1)]
        [else (ack (sub1 m) (ack m (sub1 n)))]))
(displayln (ack 3 {n}))
"""
    if name == "closures":
        return f"""#lang racket/base
(define (make-adder k) (lambda (x) (+ x k)))
(define add3 (make-adder 3))
(define (loop n acc)
  (if (zero? n) acc (loop (sub1 n) (add3 acc))))
(displayln (loop {n} 0))
"""
    if name == "evenodd":
        return f"""#lang racket/base
(define (is-even n)
  (if (zero? n) #t (is-odd (sub1 n))))
(define (is-odd n)
  (if (zero? n) #f (is-even (sub1 n))))
(displayln (if (is-even {n}) 1 0))
"""
    raise KeyError(name)


def sbcl_source(name: str) -> str:
    n = PARAMS[name]
    if name == "fib":
        return f"""(defun fib (n)
  (cond ((= n 0) 0)
        ((= n 1) 1)
        (t (+ (fib (- n 1)) (fib (- n 2))))))
(format t "~a~%" (fib {n}))
"""
    if name == "loop":
        return f"""(defun bench-loop (n acc)
  (if (= n 0) acc (bench-loop (- n 1) (+ acc 2))))
(format t "~a~%" (bench-loop {n} 0))
"""
    if name == "ackermann":
        return f"""(defun ack (m n)
  (cond ((= m 0) (+ n 1))
        ((= n 0) (ack (- m 1) 1))
        (t (ack (- m 1) (ack m (- n 1))))))
(format t "~a~%" (ack 3 {n}))
"""
    if name == "closures":
        return f"""(let ((add3 (let ((k 3)) (lambda (x) (+ x k)))))
  (labels ((bench-loop (n acc)
             (if (= n 0) acc
                 (bench-loop (- n 1) (funcall add3 acc)))))
    (format t "~a~%" (bench-loop {n} 0))))
"""
    if name == "evenodd":
        return f"""(labels ((is-even (n)
           (if (= n 0) t (is-odd (- n 1))))
         (is-odd (n)
           (if (= n 0) nil (is-even (- n 1)))))
  (format t "~a~%" (if (is-even {n}) 1 0)))
"""
    raise KeyError(name)


def rust_source(name: str) -> str:
    n = PARAMS[name]
    if name == "fib":
        return f"""fn fib(n: i64) -> i64 {{
    if n == 0 {{ 0 }} else if n == 1 {{ 1 }} else {{ fib(n - 1) + fib(n - 2) }}
}}
fn main() {{ println!("{{}}", fib({n})); }}
"""
    if name == "loop":
        return f"""fn bench_loop(n: i64, acc: i64) -> i64 {{
    if n == 0 {{ acc }} else {{ bench_loop(n - 1, acc + 2) }}
}}
fn main() {{ println!("{{}}", bench_loop({n}, 0)); }}
"""
    if name == "ackermann":
        return f"""fn ack(m: i64, n: i64) -> i64 {{
    if m == 0 {{ n + 1 }}
    else if n == 0 {{ ack(m - 1, 1) }}
    else {{ ack(m - 1, ack(m, n - 1)) }}
}}
fn main() {{ println!("{{}}", ack(3, {n})); }}
"""
    if name == "closures":
        return f"""fn make_adder(k: i64) -> impl Fn(i64) -> i64 {{ move |x| x + k }}
fn bench_loop<F: Fn(i64) -> i64>(n: i64, acc: i64, f: &F) -> i64 {{
    if n == 0 {{ acc }} else {{ bench_loop(n - 1, f(acc), f) }}
}}
fn main() {{
    let add3 = make_adder(3);
    println!("{{}}", bench_loop({n}, 0, &add3));
}}
"""
    if name == "evenodd":
        return f"""fn is_even(n: i64) -> bool {{ if n == 0 {{ true }} else {{ is_odd(n - 1) }} }}
fn is_odd(n: i64) -> bool {{ if n == 0 {{ false }} else {{ is_even(n - 1) }} }}
fn main() {{ println!("{{}}", if is_even({n}) {{ 1 }} else {{ 0 }}); }}
"""
    raise KeyError(name)


def command_version(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (proc.stdout or proc.stderr).strip()
    return text if text else f"exit={proc.returncode}"


def run_checked(cmd: list[str], expected: str) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    got = lines[-1] if lines else ""
    if got != expected:
        raise RuntimeError(
            f"wrong answer: {' '.join(cmd)}: expected={expected!r}, got={got!r}"
        )


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
            f"cachegrind failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    match = re.search(r"I\s+refs:\s*([\d,]+)", proc.stderr)
    if match is None:
        raise RuntimeError(f"Cachegrind did not report I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def wall_seconds(cmd: list[str]) -> float:
    start = time.perf_counter()
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(
            f"native command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    return elapsed


def git_fact(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception as exc:
        return f"unknown ({exc})"


def runtime_commands(
    workdir: Path,
    python: str,
    lua: str,
    racket: str,
    sbcl: str,
    name: str,
) -> dict[str, list[str]]:
    return {
        "cpython": [python, str(workdir / f"{name}.py")],
        "lua54": [lua, str(workdir / f"{name}.lua")],
        "racket-cs": [racket, str(workdir / f"{name}.rkt")],
        "sbcl": [sbcl, "--noinform", "--disable-debugger", "--script", str(workdir / f"{name}.lisp")],
        "rust-native": [str(workdir / f"{name}-rust")],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--lua", default="lua")
    ap.add_argument("--racket", default="racket")
    ap.add_argument("--sbcl", default="sbcl")
    ap.add_argument("--rustc", default="rustc")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--only", default=",".join(CASES))
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")

    selected = tuple(x for x in args.only.split(",") if x)
    unknown = sorted(set(selected) - set(CASES))
    if unknown:
        ap.error(f"unknown workloads: {', '.join(unknown)}")

    versions = {
        "python": command_version([args.python, "--version"]),
        "lua": command_version([args.lua, "-v"]),
        "racket": command_version([args.racket, "--version"]),
        "sbcl": command_version([args.sbcl, "--version"]),
        "rustc": command_version([args.rustc, "--version"]),
        "valgrind": command_version(["valgrind", "--version"]),
    }
    if "Lua 5.4" not in versions["lua"]:
        raise RuntimeError(f"Lua 5.4 required, got: {versions['lua']}")
    if "[cs]" not in versions["racket"].lower():
        raise RuntimeError(f"Racket CS required, got: {versions['racket']}")
    if "SBCL" not in versions["sbcl"].upper():
        raise RuntimeError(f"SBCL required, got: {versions['sbcl']}")

    workdir = Path(tempfile.mkdtemp(prefix="sens-external-controls-v2-"))
    for name in selected:
        (workdir / f"{name}.py").write_text(python_source(name), encoding="utf-8")
        (workdir / f"{name}.lua").write_text(lua_source(name), encoding="utf-8")
        (workdir / f"{name}.rkt").write_text(racket_source(name), encoding="utf-8")
        (workdir / f"{name}.lisp").write_text(sbcl_source(name), encoding="utf-8")
        rust_path = workdir / f"{name}.rs"
        rust_path.write_text(rust_source(name), encoding="utf-8")
        compile_proc = subprocess.run(
            [args.rustc, "-O", str(rust_path), "-o", str(workdir / f"{name}-rust")],
            capture_output=True,
            text=True,
            check=False,
        )
        if compile_proc.returncode != 0:
            raise RuntimeError(
                f"rustc failed for {name}:\n{compile_proc.stdout}\n{compile_proc.stderr}"
            )

    # Correctness is a hard gate before any measurements.
    for name in selected:
        commands = runtime_commands(
            workdir, args.python, args.lua, args.racket, args.sbcl, name
        )
        for runtime, cmd in commands.items():
            run_checked(cmd, EXPECTED[name])
            print(f"[check] {runtime}/{name}: OK expected={EXPECTED[name]}")

    if args.check_only:
        return 0

    rows: list[dict[str, object]] = []
    for rep in range(1, args.reps + 1):
        for name in selected:
            commands = runtime_commands(
                workdir, args.python, args.lua, args.racket, args.sbcl, name
            )
            for runtime, cmd in commands.items():
                rows.append(
                    {
                        "semantic_generation": "external-control-v2",
                        "runtime": runtime,
                        "workload": name,
                        "phase": "full",
                        "rep": rep,
                        "expected": EXPECTED[name],
                        "i_refs": instruction_count(cmd),
                        "wall_s": wall_seconds(cmd),
                    }
                )
        print(f"[measure] repetition {rep}/{args.reps}")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    out = args.out or (
        ROOT
        / "benchmarks"
        / "cross-language"
        / "results"
        / f"{stamp}-external-controls-v2-{git_fact('rev-parse', '--short=8', 'HEAD')}"
    )
    out.mkdir(parents=True, exist_ok=True)

    with (out / "external-full.tsv").open("w", encoding="utf-8") as fh:
        fields = (
            "semantic_generation",
            "runtime",
            "workload",
            "phase",
            "rep",
            "expected",
            "i_refs",
            "wall_s",
        )
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[f]) for f in fields) + "\n")

    environment = {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": git_fact("rev-parse", "HEAD"),
        "semantic_generation": "external-control-v2",
        "sens_rows_present": False,
        "sens_contract_target": "11-5",
        "sens_semantic_current": ["D1", "D2", "D3", "D4", "D5", "D6"],
        "sens_semantic_research": ["D7", "D8"],
        "sens_gate": "#1668/#3394",
        **versions,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "reps": args.reps,
        "cases": list(selected),
        "params": {name: PARAMS[name] for name in selected},
    }
    (out / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault((str(row["runtime"]), str(row["workload"])), []).append(row)

    runtimes = ("cpython", "lua54", "racket-cs", "sbcl", "rust-native")
    lines = [
        "# External runtime controls — Contract 11-5 benchmark program",
        "",
        "These rows are concrete implementation controls only. There is deliberately",
        "no fresh SENS timing row until the current D1-D6 exact-domain gate is GREEN.",
        "",
        "Primary metric: Cachegrind I refs. Wall time is auxiliary.",
        "",
        "| workload | runtime | median I refs | median wall, s |",
        "|---|---|---:|---:|",
    ]
    for name in selected:
        for runtime in runtimes:
            sample = grouped[(runtime, name)]
            irefs = statistics.median(int(r["i_refs"]) for r in sample)
            wall = statistics.median(float(r["wall_s"]) for r in sample)
            lines.append(f"| {name} | {runtime} | {irefs:,.0f} | {wall:.6f} |")

    lines += [
        "",
        "Interpretation boundary:",
        "- same workload parameters and expected answers are used for all runtimes;",
        "- this first slice measures full-process execution only;",
        "- Rust sources are compiled with rustc -O before measurement; compile cost is not hidden inside execution rows and will be a separate phase;",
        "- SBCL is a classic Common Lisp implementation control, not SENS semantic authority;",
        "- tail-call and compiler behavior are implementation properties and are not normalized away;",
        "- current SENS may join only through Contract 11-5 exact-domain correctness evidence;",
        "- historical Function8/Sens8 rows remain archive-only.",
        "",
    ]
    report = "\n".join(lines)
    (out / "report.md").write_text(report, encoding="utf-8")
    print()
    print(report)
    print(f"\nresults: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
