#!/usr/bin/env python3
"""Amplification sweep: for which N is steady(N) stable?

steady(N) = (median(repeat_N) − median(ready)) / N

Wall-clock often needs large N; Cachegrind I-refs should be nearly flat.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHASES = HERE / "cpython_phases_min.py"

_STEADY_CANDIDATES = [
    HERE.parents[1] / "steady",
    HERE.parents[2] / "cross-language" / "steady",
]
_corpus_loaded = False
for _steady in _STEADY_CANDIDATES:
    if (_steady / "corpus.py").is_file():
        sys.path.insert(0, str(_steady))
        try:
            from corpus import CASES, EXPECTED, PARAMS, python_source  # type: ignore

            if (_steady / "cpython_phases.py").is_file():
                PHASES = _steady / "cpython_phases.py"
            _corpus_loaded = True
            break
        except ImportError:
            pass

if not _corpus_loaded:
    CASES = ("fib", "loop", "ackermann", "closures", "evenodd")
    PARAMS = {"fib": 16, "loop": 700, "ackermann": 3, "closures": 700, "evenodd": 700}
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
        bodies = {
            "fib": (
                f"import sys\nsys.setrecursionlimit({limit})\n"
                f"def fib(n):\n"
                f"    if n == 0: return 0\n"
                f"    if n == 1: return 1\n"
                f"    return fib(n - 1) + fib(n - 2)\n"
                f"def bench():\n    return fib({n})\n"
            ),
            "loop": (
                f"import sys\nsys.setrecursionlimit({limit})\n"
                f"def loop(n, acc):\n"
                f"    if n == 0: return acc\n"
                f"    return loop(n - 1, acc + 2)\n"
                f"def bench():\n    return loop({n}, 0)\n"
            ),
            "ackermann": (
                f"import sys\nsys.setrecursionlimit({limit})\n"
                f"def ack(m, n):\n"
                f"    if m == 0: return n + 1\n"
                f"    if n == 0: return ack(m - 1, 1)\n"
                f"    return ack(m - 1, ack(m, n - 1))\n"
                f"def bench():\n    return ack(3, {n})\n"
            ),
            "closures": (
                f"import sys\nsys.setrecursionlimit({limit})\n"
                f"def make_adder(k):\n"
                f"    def add(x): return x + k\n"
                f"    return add\n"
                f"add3 = make_adder(3)\n"
                f"def loop(n, acc):\n"
                f"    if n == 0: return acc\n"
                f"    return loop(n - 1, add3(acc))\n"
                f"def bench():\n    return loop({n}, 0)\n"
            ),
            "evenodd": (
                f"import sys\nsys.setrecursionlimit({limit})\n"
                f"def is_even(n):\n"
                f"    if n == 0: return 1\n"
                f"    return is_odd(n - 1)\n"
                f"def is_odd(n):\n"
                f"    if n == 0: return 0\n"
                f"    return is_even(n - 1)\n"
                f"def bench():\n    return is_even({n})\n"
            ),
        }
        return bodies[name]

DEFAULT_NS = (1, 2, 5, 10, 20, 50)


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
        raise RuntimeError(f"fail: {' '.join(cmd)}\n{proc.stderr}")
    return elapsed


def measure(cmd: list[str], cachegrind: bool) -> tuple[float, int | None]:
    wall = wall_seconds(cmd)
    irefs = instruction_count(cmd) if cachegrind else None
    return wall, irefs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--ns", default=",".join(str(n) for n in DEFAULT_NS))
    ap.add_argument("--only", default="fib,loop")
    ap.add_argument("--cachegrind", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    selected = tuple(x for x in args.only.split(",") if x)
    ns = tuple(int(x) for x in args.ns.split(",") if x)
    if args.reps < 1:
        ap.error("--reps >= 1")

    driver = PHASES
    if not driver.is_file():
        raise SystemExit(f"phase driver missing: {driver}")

    work = Path(tempfile.mkdtemp(prefix="amp-"))
    files: dict[str, Path] = {}
    for name in selected:
        p = work / f"{name}.py"
        p.write_text(python_source(name), encoding="utf-8")
        files[name] = p
        proc = subprocess.run(
            [args.python, str(driver), str(p), "full"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        got = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()][-1]
        exp = EXPECTED[name]
        if got != exp:
            raise RuntimeError(f"{name}: expected {exp!r} got {got!r}")
        print(f"[check] {name}: OK")

    rows: list[dict[str, object]] = []
    for name in selected:
        py = str(files[name])
        for rep in range(1, args.reps + 1):
            cmd_ready = [args.python, str(driver), py, "ready"]
            w, ir = measure(cmd_ready, args.cachegrind)
            rows.append(
                {
                    "workload": name,
                    "phase": "ready",
                    "n": "",
                    "rep": rep,
                    "wall_s": f"{w:.9f}",
                    "i_refs": ir if ir is not None else "",
                }
            )
            for n in ns:
                cmd_rep = [args.python, str(driver), py, "repeat", str(n)]
                w, ir = measure(cmd_rep, args.cachegrind)
                rows.append(
                    {
                        "workload": name,
                        "phase": "repeat",
                        "n": n,
                        "rep": rep,
                        "wall_s": f"{w:.9f}",
                        "i_refs": ir if ir is not None else "",
                    }
                )
        print(f"[measure] {name} done")

    args.out.mkdir(parents=True, exist_ok=True)
    fields = ["workload", "phase", "n", "rep", "wall_s", "i_refs"]
    with (args.out / "amplification.tsv").open("w", encoding="utf-8") as fh:
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[f]) for f in fields) + "\n")

    metric = "i_refs" if args.cachegrind else "wall_s"
    lines = [
        f"# Amplification sweep (metric={metric})",
        "",
        "steady(N) = (median(repeat_N) − median(ready)) / N",
        "",
        "| workload | N | ready | repeat | steady/call | ok |",
        "|---|---:|---:|---:|---:|:---:|",
    ]
    for name in selected:
        ready_vals = [
            float(r[metric])
            for r in rows
            if r["workload"] == name and r["phase"] == "ready" and r[metric] != ""
        ]
        if not ready_vals:
            continue
        ready_m = statistics.median(ready_vals)
        for n in ns:
            rep_vals = [
                float(r[metric])
                for r in rows
                if r["workload"] == name
                and r["phase"] == "repeat"
                and r["n"] == n
                and r[metric] != ""
            ]
            if not rep_vals:
                continue
            rep_m = statistics.median(rep_vals)
            delta = rep_m - ready_m
            ok = delta > 0
            per = delta / n if ok else float("nan")
            lines.append(
                f"| {name} | {n} | {ready_m:.4g} | {rep_m:.4g} | "
                f"{per:.4g} | {'yes' if ok else 'NO'} |"
            )

    lines += [
        "",
        "Wall rows may show NO at small N (process noise). "
        "Cachegrind should stay ok and nearly flat across N.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report + "\n", encoding="utf-8")
    (args.out / "environment.json").write_text(
        json.dumps(
            {
                "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "agent": "grok-bench-coord",
                "suite": "amplification-sweep",
                "metric": metric,
                "ns": list(ns),
                "cases": list(selected),
                "reps": args.reps,
                "platform": platform.platform(),
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
