#!/usr/bin/env python3
"""Current SENS exact-domain lane for the shared cross-language corpus.

The five workloads and parameters intentionally match external_controls.py.
Only exact current D3/D4/D5 call heads are used. User-defined function names
remain lexical symbols. No Sens8/Sid8/Function8 spelling participates.

COND clause test/branch expressions are recursively lifted by the #3422 bridge.\n\nThis first lane measures a prebuilt SENS benchmark runner. It is designed to be
joined with external controls in one same-machine workflow after the stacked
source bridge lands.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import re
import statistics
import subprocess
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

# Current exact-domain heads.
DEFINE = "0011"      # D4
LAMBDA = "0010"      # D4
EQ = "101"           # D3
COND = "110"         # D3
PLUS = "01010"       # D5
DIFFERENCE = "01011" # D5

TRUE_TEST = f"({EQ} 0 0)"


def source(name: str) -> str:
    n = PARAMS[name]
    if name == "fib":
        return f"""({DEFINE} fib ({LAMBDA} (n)
  ({COND}
    (({EQ} n 0) 0)
    (({EQ} n 1) 1)
    ({TRUE_TEST} ({PLUS}
      (fib ({DIFFERENCE} n 1))
      (fib ({DIFFERENCE} n 2)))))))
(fib {n})
"""
    if name == "loop":
        return f"""({DEFINE} loop ({LAMBDA} (n acc)
  ({COND}
    (({EQ} n 0) acc)
    ({TRUE_TEST} (loop ({DIFFERENCE} n 1) ({PLUS} acc 2))))))
(loop {n} 0)
"""
    if name == "ackermann":
        return f"""({DEFINE} ack ({LAMBDA} (m n)
  ({COND}
    (({EQ} m 0) ({PLUS} n 1))
    (({EQ} n 0) (ack ({DIFFERENCE} m 1) 1))
    ({TRUE_TEST}
      (ack ({DIFFERENCE} m 1)
           (ack m ({DIFFERENCE} n 1)))))))
(ack 3 {n})
"""
    if name == "closures":
        return f"""({DEFINE} make-adder
  ({LAMBDA} (k) ({LAMBDA} (x) ({PLUS} x k))))
({DEFINE} add3 (make-adder 3))
({DEFINE} loop ({LAMBDA} (n acc)
  ({COND}
    (({EQ} n 0) acc)
    ({TRUE_TEST} (loop ({DIFFERENCE} n 1) (add3 acc))))))
(loop {n} 0)
"""
    if name == "evenodd":
        return f"""({DEFINE} is-even ({LAMBDA} (n)
  ({COND}
    (({EQ} n 0) 1)
    ({TRUE_TEST} (is-odd ({DIFFERENCE} n 1))))))
({DEFINE} is-odd ({LAMBDA} (n)
  ({COND}
    (({EQ} n 0) 0)
    ({TRUE_TEST} (is-even ({DIFFERENCE} n 1))))))
(is-even {n})
"""
    raise KeyError(name)


def final_answer(stdout: str) -> str:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def checked(cmd: list[str], expected: str) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    got = final_answer(proc.stdout)
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
    proc = subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True
    )
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runner", required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--only", default=",".join(CASES))
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    selected = tuple(x for x in args.only.split(",") if x)
    unknown = sorted(set(selected) - set(CASES))
    if unknown:
        ap.error(f"unknown workloads: {', '.join(unknown)}")
    if args.reps < 1:
        ap.error("--reps must be >= 1")

    runner = str(Path(args.runner).resolve())
    workdir = Path(tempfile.mkdtemp(prefix="sens-current-exact-"))
    programs: dict[str, Path] = {}
    for name in selected:
        path = workdir / f"{name}.lisp"
        path.write_text(source(name), encoding="utf-8")
        programs[name] = path

    # Correctness is a hard gate. A wrong answer never becomes a timing row.
    for name in selected:
        checked([runner, str(programs[name])], EXPECTED[name])
        print(f"[check] sens-exact/{name}: OK expected={EXPECTED[name]}")

    if args.check_only:
        return 0

    rows: list[dict[str, object]] = []
    for rep in range(1, args.reps + 1):
        for name in selected:
            cmd = [runner, str(programs[name])]
            rows.append(
                {
                    "semantic_generation": "contract-11-5-exact-d1-d6",
                    "runtime": "sens-exact",
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
        / f"{stamp}-sens-exact-{git_fact('rev-parse', '--short=8', 'HEAD')}"
    )
    out.mkdir(parents=True, exist_ok=True)

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
    with (out / "sens-exact-full.tsv").open("w", encoding="utf-8") as fh:
        fh.write("\t".join(fields) + "\n")
        for row in rows:
            fh.write("\t".join(str(row[field]) for field in fields) + "\n")

    env = {
        "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "git_sha": git_fact("rev-parse", "HEAD"),
        "semantic_generation": "contract-11-5-exact-d1-d6",
        "authority": "#3393",
        "mixed_source": "#3548",
        "benchmark_issue": "#3417",
        "runner": runner,
        "runner_sha256": subprocess.run(
            ["sha256sum", runner], capture_output=True, text=True, check=True
        ).stdout.split()[0],
        "platform": platform.platform(),
        "cases": list(selected),
        "params": {name: PARAMS[name] for name in selected},
        "heads": {
            "D3_EQ": EQ,
            "D3_COND": COND,
            "D4_LAMBDA": LAMBDA,
            "D4_DEFINE": DEFINE,
            "D5_PLUS": PLUS,
            "D5_DIFFERENCE": DIFFERENCE,
        },
        "legacy_function8_used": False,
    }
    (out / "environment.json").write_text(
        json.dumps(env, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Current SENS exact-domain control",
        "",
        "| workload | median I refs | median wall, s |",
        "|---|---:|---:|",
    ]
    for name in selected:
        sample = [row for row in rows if row["workload"] == name]
        irefs = statistics.median(int(row["i_refs"]) for row in sample)
        wall = statistics.median(float(row["wall_s"]) for row in sample)
        lines.append(f"| {name} | {irefs:,.0f} | {wall:.6f} |")
    lines += [
        "",
        "This lane uses exact D3/D4/D5 call heads only.",
        "No historical Sens8/Sid8/Function8 source identity participates.",
        "Join these rows with external controls only when measured on the same machine/job.",
        "",
    ]
    report = "\n".join(lines)
    (out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"results: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
