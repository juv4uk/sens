#!/usr/bin/env python3
"""Benchmark released SENS's real T5 files; timing never grants semantics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy",
    "tests/fixtures/migration-multiform-cohort-main/two-forms",
)


def run(cmd: list[str]) -> tuple[subprocess.CompletedProcess[bytes], int]:
    start = time.perf_counter_ns()
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, check=False)
    return proc, time.perf_counter_ns() - start


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens", type=Path, required=True)
    ap.add_argument("--sens-trit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=21)
    ap.add_argument("--warmups", type=int, default=4)
    args = ap.parse_args()
    if args.reps < 3 or args.warmups < 0:
        ap.error("reps >= 3 and warmups >= 0 required")
    sens = str(args.sens.resolve())
    trit = str(args.sens_trit.resolve())
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    git = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    raw: list[dict] = []
    cases: list[dict] = []

    for name in FIXTURES:
        packed_file = REPO / (name + ".sens")
        lisp_file = REPO / (name + ".lisp")
        packed = packed_file.read_bytes()
        lisp = lisp_file.read_bytes()
        commands = {
            "SENS-physical-T5": [sens, str(packed_file)],
            "SENS-trit-T5": [trit, "eval", str(packed_file)],
        }
        primary, _ = run(commands["SENS-physical-T5"])
        secondary, _ = run(commands["SENS-trit-T5"])
        if primary.returncode or secondary.returncode or primary.stdout != secondary.stdout:
            raise ValueError(f"BLOCKED: {name}: physical T5 output/parity invalid; no timing")
        view, _ = run([trit, "open", str(packed_file)])
        if view.returncode:
            raise ValueError(f"BLOCKED: {name}: T5 human binary projection failed")
        words = view.stdout.decode("ascii").split()
        if not words or any(not 1 <= len(w) <= 9 or set(w) - {"0", "1"} for w in words):
            raise ValueError(f"BLOCKED: {name}: canonical bit words malformed")
        legacy, _ = run([sens, str(lisp_file)])
        legacy_ok = legacy.returncode == 0 and legacy.stdout == primary.stdout
        # This historical Core4 bootstrap is different from pure T5; it is
        # never silently treated as the same implementation or a speedup.
        if legacy_ok:
            commands["SENS-text-Core4"] = [sens, str(lisp_file)]

        for _ in range(args.warmups):
            for cmd in commands.values():
                result, _ = run(cmd)
                if result.returncode or result.stdout != primary.stdout:
                    raise ValueError(f"BLOCKED: {name}: parity changed during warmup")
        case_rows = []
        for i in range(args.reps):
            modes = list(commands)
            offset = i % len(modes)
            for mode in modes[offset:] + modes[:offset]:
                result, ns = run(commands[mode])
                if result.returncode or result.stdout != primary.stdout:
                    raise ValueError(f"BLOCKED: {name}: {mode} result drifted during timing")
                case_rows.append({"case": Path(name).name, "mode": mode,
                                  "iteration": i, "wall_ns": ns})
        raw.extend(case_rows)
        medians = {
            mode: int(statistics.median(x["wall_ns"] for x in case_rows if x["mode"] == mode))
            for mode in commands
        }
        cases.append({
            "case": Path(name).name,
            "sha256_t5": sha(packed),
            "sha256_lisp": sha(lisp),
            "bytes_T5": len(packed),
            "bytes_visible_binary": len(view.stdout.rstrip(b"\n")),
            "bytes_legacy_lisp": len(lisp),
            "legacy_parity": "PASS-DIFFERENT-PROFILE" if legacy_ok else "BLOCKED",
            "median_cold_ns": medians,
        })

    env = {"platform": platform.platform(), "machine": platform.machine(),
           "python": platform.python_version(), "cpu_count": os.cpu_count(),
           "runner": os.getenv("RUNNER_NAME", "local"),
           "sha256_sens": sha(Path(sens).read_bytes()),
           "sha256_sens_trit": sha(Path(trit).read_bytes())}
    report = {"schema": "sens-physical-reality-bench/v1", "commit_sha": git,
              "env": env, "reps": args.reps, "warmups": args.warmups,
              "scope": "cold subprocess: process startup + read + decode + parse + evaluation + output",
              "limits": "Core4 text and pure T5 are distinct profiles; no global language ranking",
              "cases": cases}
    (out / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    with (out / "raw.tsv").open("w", newline="") as fp:
        writer = csv.DictWriter(fp, ["case", "mode", "iteration", "wall_ns"], delimiter="\t")
        writer.writeheader()
        writer.writerows(raw)
    lines = [
        "# SENS: real physical T5 benchmark", "",
        f"SHA: {git}; runs: {args.reps}; warmups: {args.warmups}.", "",
        "| Case | Mode | T5 bytes | Binary text bytes | Legacy Lisp bytes | Median cold ms |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for case in cases:
        for mode, duration in case["median_cold_ns"].items():
            lines.append(f"| {case['case']} | {mode} | {case['bytes_T5']} | "
                         f"{case['bytes_visible_binary']} | {case['bytes_legacy_lisp']} | "
                         f"{duration/1_000_000:.3f} |")
        if case["legacy_parity"] == "BLOCKED":
            lines.append(f"| {case['case']} | text/Core4: BLOCKED | — | — | — | — |")
    lines += ["", "This measures cold process execution; not steady-state or GPU.",
              "Text/Core4 uses a different bootstrap. Do not claim a language speedup from this.",
              "Raw repetitions and binary SHA256 provenance are in raw.tsv and results.json."]
    summary = "\n".join(lines) + "\n"
    (out / "report.md").write_text(summary)
    print(summary)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, UnicodeError) as error:
        print(f"BENCHMARK_BLOCKED: {error}", file=sys.stderr)
        sys.exit(2)
