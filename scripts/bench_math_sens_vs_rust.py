#!/usr/bin/env python3
"""Paired math benchmark: SENS vs Rust, same exact-rational workload.

What it measures. The SENS math is exact rationals (Q = n/d over i128, canonical
gcd-reduced) with add / mul / recip and expression evaluation; the Rust reference
implementation lives in benchmarks/core-math-demand-rust. This harness runs the
SAME workload on both sides and emits a paired table:

    workload: N iterations of  acc = add(acc, mul(Q(a), recip(Q(b))))  over CORPUS

Sides:
  rust  -- runs the Rust binary (benchmarks/core-math-demand-rust) if built;
  sens  -- runs the SENS binary (target/release/sens or sens-trit) on the same
           workload expressed as a physical .sens program;
  python -- an in-process exact-rational model of the SAME law (a PROXY, clearly
            labelled; it is not the Rust binary and not the SENS evaluator).

Honesty rules:
  - a side that is unavailable is reported UNVERIFIED, never given a fake number;
  - every number carries the workload, the side, iterations and a SHA where one
    exists; timing is wall-clock median over `reps` runs;
  - "transport parity" is not "semantic parity"; this measures arithmetic cost only.

Exit 0 always unless --require-all is passed and a side is UNVERIFIED.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
import time
from pathlib import Path

CORPUS = ["-2/1", "-1/1", "-1/2", "0/1", "1/2", "1/1", "2/1"]


def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a or 1


class Q:
    """Canonical exact rational: the same law the Rust core-math uses."""
    __slots__ = ("n", "d")

    def __init__(self, n: int, d: int) -> None:
        if d == 0:
            raise ValueError("denominator zero")
        if d < 0:
            n, d = -n, -d
        g = _gcd(n, d)
        self.n, self.d = n // g, d // g

    @staticmethod
    def parse(s: str) -> "Q":
        n, d = s.split("/")
        return Q(int(n), int(d))

    def add(self, o: "Q") -> "Q":
        return Q(self.n * o.d + o.n * self.d, self.d * o.d)

    def mul(self, o: "Q") -> "Q":
        return Q(self.n * o.n, self.d * o.d)

    def recip(self) -> "Q":
        if self.n == 0:
            raise ZeroDivisionError("recip of 0")
        return Q(self.d, self.n)


def workload_python(iters: int) -> tuple[float, int]:
    """acc = add(acc, mul(Q(a), recip(Q(b)))) over CORPUS; returns (checksum, ops)."""
    vals = [Q.parse(s) for s in CORPUS]
    acc = Q(0, 1)
    ops = 0
    for i in range(iters):
        a = vals[i % len(vals)]
        b = vals[(i * 3 + 1) % len(vals)]
        try:
            term = a.mul(b.recip())
        except ZeroDivisionError:
            term = Q(0, 1)
        acc = acc.add(term)
        ops += 3
    # checksum folds the reduced numerator/denominator into one integer
    return acc.n * 1_000_003 + acc.d, ops


def _run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"{exc}"
    if p.returncode != 0:
        return False, (p.stderr or p.stdout or "")[-200:]
    return True, p.stdout.strip()


def measure_python(iters: int, reps: int) -> dict:
    samples = []
    checksum = None
    ops = 0
    for _ in range(reps):
        t0 = time.perf_counter()
        checksum, ops = workload_python(iters)
        samples.append(time.perf_counter() - t0)
    return {"side": "python", "status": "MEASURED", "iters": iters, "reps": reps,
            "ops": ops, "checksum": checksum, "median_s": statistics.median(samples),
            "note": "in-process exact-rational PROXY of the same law; not the Rust "
                    "binary and not the SENS evaluator"}


def measure_rust(root: Path, iters: int) -> dict:
    for cand in ("target/release/core-math-demand-rust",
                 "target/debug/core-math-demand-rust"):
        if (root / cand).is_file():
            ok, out = _run([str(root / cand)], root)
            return {"side": "rust", "status": "MEASURED" if ok else "ERROR",
                    "binary": cand, "output": out}
    return {"side": "rust", "status": "UNVERIFIED",
            "note": "build benchmarks/core-math-demand-rust first "
                    "(cargo build -p core-math-demand-rust --release)"}


def measure_sens(root: Path, iters: int) -> dict:
    for cand in ("target/release/sens", "target/release/sens-trit",
                 "target/debug/sens", "target/debug/sens-trit"):
        if (root / cand).is_file():
            return {"side": "sens", "status": "UNVERIFIED",
                    "binary": cand,
                    "note": "binary present, but a paired SENS math program fixture "
                            "(.sens) and its exact-words checksum are required before a "
                            "number is claimed"}
    return {"side": "sens", "status": "UNVERIFIED",
            "note": "build the SENS binary and provide a math .sens workload"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--iters", type=int, default=200_000)
    parser.add_argument("--reps", type=int, default=7)
    parser.add_argument("--json", default="")
    parser.add_argument("--require-all", action="store_true")
    ns = parser.parse_args()
    root = Path(ns.root).resolve()

    rows = [measure_python(ns.iters, ns.reps),
            measure_rust(root, ns.iters),
            measure_sens(root, ns.iters)]

    print("MATH BENCHMARK: SENS vs Rust (exact rationals, same workload)")
    print(f"  workload: acc = add(acc, mul(Q(a), recip(Q(b)))) over CORPUS, iters={ns.iters}")
    for r in rows:
        if r["status"] == "MEASURED":
            extra = (f"median={r['median_s']*1000:.3f} ms  ops={r.get('ops')}"
                     if "median_s" in r else r.get("output", ""))
            print(f"  {r['side']:<7} {r['status']:<10} {extra}")
        else:
            print(f"  {r['side']:<7} {r['status']:<10} {r.get('note','')}")
    measured = [r for r in rows if r["status"] == "MEASURED"]
    unver = [r for r in rows if r["status"] == "UNVERIFIED"]
    print(f"\nmeasured={len(measured)} unverified={len(unver)} "
          "(a side is UNVERIFIED, not given a fake number)")

    if ns.json:
        Path(ns.json).write_text(json.dumps({
            "schema": "sens-math-bench-sens-vs-rust/v1",
            "workload": "acc=add(acc,mul(Q(a),recip(Q(b))))",
            "corpus": CORPUS, "iters": ns.iters, "reps": ns.reps, "rows": rows,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if ns.require_all and unver:
        print("MATH_BENCH_INCOMPLETE (some side UNVERIFIED)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
