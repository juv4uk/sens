#!/usr/bin/env python3
"""#3490/#3513 phase decomposition for current exact-domain SENS.

Cold modes measure startup/Core load/source processing/steady evaluation.
Warm modes keep one Core Session resident and fit repeated slopes for:
- creating an isolated lexical child;
- installing a pre-parsed program setup into a fresh child;
- parsing exact-domain setup source and installing it into a fresh child.

Cachegrind I refs are primary. Wall time is auxiliary.
"""

from __future__ import annotations

import argparse
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

import current_sens as shared

REPEAT_LADDER = (1, 10, 100)


def setup_call(name: str) -> tuple[str, str]:
    n = shared.PARAMS[name]
    d = shared.DEFINE
    l = shared.LAMBDA
    eq = shared.EQ
    cond = shared.COND
    plus = shared.PLUS
    sub = shared.DIFFERENCE
    yes = shared.TRUE_TEST

    if name == "fib":
        setup = f"""({d} fib ({l} (n)
  ({cond}
    (({eq} n 0) 0)
    (({eq} n 1) 1)
    ({yes} ({plus}
      (fib ({sub} n 1))
      (fib ({sub} n 2)))))))
"""
        call = f"(fib {n})\n"
    elif name == "loop":
        setup = f"""({d} loop ({l} (n acc)
  ({cond}
    (({eq} n 0) acc)
    ({yes} (loop ({sub} n 1) ({plus} acc 2))))))
"""
        call = f"(loop {n} 0)\n"
    elif name == "ackermann":
        setup = f"""({d} ack ({l} (m n)
  ({cond}
    (({eq} m 0) ({plus} n 1))
    (({eq} n 0) (ack ({sub} m 1) 1))
    ({yes}
      (ack ({sub} m 1)
           (ack m ({sub} n 1)))))))
"""
        call = f"(ack 3 {n})\n"
    elif name == "closures":
        setup = f"""({d} make-adder
  ({l} (k) ({l} (x) ({plus} x k))))
({d} add3 (make-adder 3))
({d} loop ({l} (n acc)
  ({cond}
    (({eq} n 0) acc)
    ({yes} (loop ({sub} n 1) (add3 acc))))))
"""
        call = f"(loop {n} 0)\n"
    elif name == "evenodd":
        setup = f"""({d} is-even ({l} (n)
  ({cond}
    (({eq} n 0) 1)
    ({yes} (is-odd ({sub} n 1))))))
({d} is-odd ({l} (n)
  ({cond}
    (({eq} n 0) 0)
    ({yes} (is-even ({sub} n 1))))))
"""
        call = f"(is-even {n})\n"
    else:
        raise KeyError(name)

    assert setup + call == shared.source(name), name
    return setup, call


def final_answer(stdout: str) -> str:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def check(cmd: list[str], expected: str | None = None) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    if expected is not None:
        got = final_answer(proc.stdout)
        if got != expected:
            raise RuntimeError(
                f"wrong answer: {' '.join(cmd)}: expected={expected!r}, got={got!r}"
            )


def instruction_count(cmd: list[str]) -> int:
    import re

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
    proc = subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
    )
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    return elapsed


def slope(xs: list[int], ys: list[float]) -> tuple[float, float]:
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0:
        raise ValueError("repeat ladder must contain distinct values")
    m = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    b = ybar - m * xbar
    return m, b


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runner", required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--only", default=",".join(shared.CASES))
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.reps < 1:
        ap.error("--reps must be >= 1")
    selected = tuple(x for x in args.only.split(",") if x)
    unknown = sorted(set(selected) - set(shared.CASES))
    if unknown:
        ap.error(f"unknown workloads: {', '.join(unknown)}")

    runner = str(Path(args.runner).resolve())
    workdir = Path(tempfile.mkdtemp(prefix="sens-phase-3490-"))
    files: dict[str, tuple[Path, Path]] = {}
    for name in selected:
        setup, call = setup_call(name)
        setup_path = workdir / f"{name}.setup.lisp"
        call_path = workdir / f"{name}.call.lisp"
        setup_path.write_text(setup, encoding="utf-8")
        call_path.write_text(call, encoding="utf-8")
        files[name] = (setup_path, call_path)

    check([runner, "startup"])
    check([runner, "load"])
    check([runner, "warm-child", "1"])
    for name in selected:
        setup_path, call_path = files[name]
        check([runner, "parse", str(setup_path), str(call_path)])
        check([runner, "lower", str(setup_path), str(call_path)])
        check([runner, "setup", str(setup_path)])
        check([runner, "warm-parsed", str(setup_path), "1"])
        check([runner, "warm-source", str(setup_path), "1"])
        for repeat in REPEAT_LADDER:
            check(
                [runner, "steady", str(setup_path), str(call_path), str(repeat)],
                shared.EXPECTED[name],
            )
        print(f"[check] phases/{name}: OK")

    rows: list[dict[str, object]] = []

    def measure(phase: str, workload: str, repeat: int, cmd: list[str]) -> None:
        for rep in range(1, args.reps + 1):
            rows.append(
                {
                    "phase": phase,
                    "workload": workload,
                    "repeat": repeat,
                    "rep": rep,
                    "i_refs": instruction_count(cmd),
                    "wall_s": wall_seconds(cmd),
                }
            )

    measure("startup", "__global__", 0, [runner, "startup"])
    measure("load", "__global__", 0, [runner, "load"])
    for repeat in REPEAT_LADDER:
        measure("warm-child", "__global__", repeat, [runner, "warm-child", str(repeat)])

    for name in selected:
        setup_path, call_path = files[name]
        measure("parse", name, 0, [runner, "parse", str(setup_path), str(call_path)])
        measure("lower", name, 0, [runner, "lower", str(setup_path), str(call_path)])
        measure("setup", name, 0, [runner, "setup", str(setup_path)])
        for repeat in REPEAT_LADDER:
            measure(
                "steady",
                name,
                repeat,
                [runner, "steady", str(setup_path), str(call_path), str(repeat)],
            )
            measure(
                "warm-parsed",
                name,
                repeat,
                [runner, "warm-parsed", str(setup_path), str(repeat)],
            )
            measure(
                "warm-source",
                name,
                repeat,
                [runner, "warm-source", str(setup_path), str(repeat)],
            )

    args.out.mkdir(parents=True, exist_ok=True)
    fields = ("phase", "workload", "repeat", "rep", "i_refs", "wall_s")
    with (args.out / "phase-rows.tsv").open("w", encoding="utf-8") as fh:
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[field]) for field in fields) + "\n")

    def med(phase: str, workload: str, repeat: int, field: str) -> float:
        values = [
            float(row[field])
            for row in rows
            if row["phase"] == phase
            and row["workload"] == workload
            and row["repeat"] == repeat
        ]
        return statistics.median(values)

    lines = [
        "# #3490 exact-domain SENS phase decomposition",
        "",
        "Primary metric: Cachegrind I refs. Wall time is auxiliary.",
        "",
        "| phase | workload | median I refs | median wall, s |",
        "|---|---|---:|---:|",
        f"| startup | global | {med('startup', '__global__', 0, 'i_refs'):,.0f} | {med('startup', '__global__', 0, 'wall_s'):.6f} |",
        f"| load | global | {med('load', '__global__', 0, 'i_refs'):,.0f} | {med('load', '__global__', 0, 'wall_s'):.6f} |",
    ]

    for name in selected:
        for phase in ("parse", "lower", "setup"):
            lines.append(
                f"| {phase} | {name} | {med(phase, name, 0, 'i_refs'):,.0f} | {med(phase, name, 0, 'wall_s'):.6f} |"
            )

    lines += [
        "",
        "## Repeated-call slope",
        "",
        "| workload | I refs / call | I-ref intercept | wall / call, s | wall intercept, s |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in selected:
        xs = list(REPEAT_LADDER)
        yi = [med("steady", name, n, "i_refs") for n in xs]
        yw = [med("steady", name, n, "wall_s") for n in xs]
        mi, bi = slope(xs, yi)
        mw, bw = slope(xs, yw)
        lines.append(f"| {name} | {mi:,.2f} | {bi:,.0f} | {mw:.9f} | {bw:.6f} |")

    child_i, child_bi = slope(
        list(REPEAT_LADDER),
        [med("warm-child", "__global__", n, "i_refs") for n in REPEAT_LADDER],
    )
    child_w, child_bw = slope(
        list(REPEAT_LADDER),
        [med("warm-child", "__global__", n, "wall_s") for n in REPEAT_LADDER],
    )

    lines += [
        "",
        "## Warm resident-Core program setup",
        "",
        "Core is loaded once per process. Every repetition gets a fresh lexical child.",
        f"Child-session slope alone: {child_i:,.2f} I refs / child, {child_w:.9f} s / child; intercept {child_bi:,.0f} I refs / {child_bw:.6f} s.",
        "",
        "| workload | pre-parsed setup I refs/program | source->ready I refs/program | pre-parsed wall/program, s | source->ready wall/program, s |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in selected:
        xs = list(REPEAT_LADDER)
        parsed_i, _ = slope(xs, [med("warm-parsed", name, n, "i_refs") for n in xs])
        source_i, _ = slope(xs, [med("warm-source", name, n, "i_refs") for n in xs])
        parsed_w, _ = slope(xs, [med("warm-parsed", name, n, "wall_s") for n in xs])
        source_w, _ = slope(xs, [med("warm-source", name, n, "wall_s") for n in xs])
        lines.append(
            f"| {name} | {parsed_i:,.2f} | {source_i:,.2f} | {parsed_w:.9f} | {source_w:.9f} |"
        )

    lines += [
        "",
        "Interpretation:",
        "- cold Core load is an intercept, not charged again to each warm program;",
        "- warm-parsed measures lowering/definition installation in a fresh lexical child;",
        "- warm-source adds exact-domain parsing from an in-memory source string;",
        "- warm child sessions share the resident Core as a parent but keep program definitions in their own lexical frame;",
        "- no historical Sens8/Sid8/Function8 source identity participates.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "phase-report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
