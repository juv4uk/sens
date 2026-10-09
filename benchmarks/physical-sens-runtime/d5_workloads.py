#!/usr/bin/env python3
"""Measure real D5 recursion and higher-order calls from physical T5 .sens files.

The same immutable physical bytes are sent to both production CLIs. Their
observable outputs must match before subprocess wall timings are admitted.
This is paired-entrypoint mechanism evidence, not an independent Lisp oracle
or a comparison with CPython semantics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, parse_words  # noqa: E402

WORKLOADS = {
    "d5-label-recursion": "examples/binary/d5-label-recursion.bits",
    "d5-label-copy": "examples/binary/d5-label-copy.bits",
    "d5-label-map": "examples/binary/d5-label-map.bits",
}
LANES = ("sens", "sens-trit-eval")


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def invoke(command: list[str]) -> tuple[int, bytes]:
    start = time.perf_counter_ns()
    proc = subprocess.run(
        command, cwd=ROOT, capture_output=True, check=False, timeout=45
    )
    elapsed = time.perf_counter_ns() - start
    if proc.returncode != 0:
        raise RuntimeError(
            f"physical D5 execution failed, code={proc.returncode}, "
            f"command={command!r}, stderr={proc.stderr[-1200:]!r}"
        )
    return elapsed, proc.stdout


def p95_ns(samples: list[int]) -> int:
    return sorted(samples)[math.ceil(0.95 * len(samples)) - 1]


def cpu_model() -> str:
    file = Path("/proc/cpuinfo")
    if file.is_file():
        for line in file.read_text(errors="replace").splitlines():
            if line.startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens", required=True, type=Path)
    parser.add_argument("--sens-trit", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--reps", type=int, default=19)
    parser.add_argument("--warmups", type=int, default=3)
    args = parser.parse_args()

    if args.reps < 5 or args.warmups < 1:
        parser.error("at least 5 measured samples and 1 warmup required")
    executables = {lane: str(p.resolve(strict=True)) for lane, p in (
        ("sens", args.sens), ("sens-trit-eval", args.sens_trit)
    )}
    result_rows: list[dict] = []
    raw_rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="sens-d5-bench-") as directory:
        for workload, filename in WORKLOADS.items():
            source_bytes = (ROOT / filename).read_bytes()
            source = source_bytes.decode("ascii")
            # Exact domain words are mandatory; no quoted names or legacy IDs.
            words = parse_words(source)
            physical = encode_words(words)
            if decode_bytes(physical) != words:
                raise RuntimeError(f"{workload}: physical T5 loss")
            fixture = Path(directory) / f"{workload}.sens"
            fixture.write_bytes(physical)
            commands = {
                "sens": [executables["sens"], str(fixture)],
                "sens-trit-eval": [executables["sens-trit-eval"], "eval", str(fixture)],
            }
            initial = {lane: invoke(cmd)[1] for lane, cmd in commands.items()}
            if not initial["sens"] or initial["sens"] != initial["sens-trit-eval"]:
                raise RuntimeError(f"{workload}: empty or discordant observable")
            samples = {lane: [] for lane in LANES}
            for trial in range(args.warmups + args.reps):
                order = LANES[trial % 2:] + LANES[:trial % 2]
                for lane in order:
                    elapsed, output = invoke(commands[lane])
                    if output != initial[lane]:
                        raise RuntimeError(f"{workload}/{lane}: unstable execution result")
                    if trial >= args.warmups:
                        samples[lane].append(elapsed)
                        raw_rows.append({
                            "workload": workload, "lane": lane,
                            "rep": trial - args.warmups + 1, "wall_ns": elapsed,
                        })
            for lane in LANES:
                values = samples[lane]
                result_rows.append({
                    "workload": workload, "lane": lane, "reps": len(values),
                    "median_wall_ns": int(statistics.median(values)),
                    "p95_wall_ns": p95_ns(values), "min_wall_ns": min(values),
                    "source_words": len(words), "semantic_bits": sum(map(len, words)),
                    "physical_t5_bytes": len(physical),
                    "ascii_bit_view_bytes": len(" ".join(words).encode("ascii")) + 1,
                    "physical_sha256": checksum(physical),
                    "output_sha256": checksum(initial[lane]),
                    "same_engine_cli_parity": True,
                })
            print(f"{workload}: {len(words)} exact words, {len(physical)} T5 bytes, "
                  f"output sha256={checksum(initial['sens'])[:16]}", flush=True)

    args.out.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    environment = {
        "schema": "sens-physical-d5-process-bench/v1", "git_sha": revision,
        "platform": platform.platform(), "cpu": cpu_model(),
        "python": platform.python_version(), "samples": args.reps,
        "warmups": args.warmups, "units": "subprocess wall nanoseconds",
        "scope": "D5 LABEL/recursive copy/higher-order MAP; both CLIs share one evaluator",
        "constraints": [
            "No textual Lisp parser in any measured SENS lane",
            "No independent semantic oracle or cross-language timing claim",
            "Execution-output parity is checked before and after every sample",
            "Different D5 programs do not have identical computational complexity",
            "No cross-host or cross-commit wall-clock speedup assertion",
        ],
    }
    (args.out / "d5-environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.out / "d5-results.json").write_text(
        json.dumps(result_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (args.out / "d5-raw.tsv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=("workload", "lane", "rep", "wall_ns"), delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(raw_rows)
    report = [
        "# Фізичний SENS: D5 LABEL, рекурсія і функції вищого порядку",
        "",
        f"SHA: `{revision}`. GitHub-hosted CPU: {environment['cpu']}. "
        f"{args.reps} вимірів і {args.warmups} прогрівання; запуск процесу включено.",
        "",
        "| Двійкова програма | Виконавець | p50, мс | p95, мс | T5, Б |",
        "|---|---|---:|---:|---:|",
    ]
    for row in result_rows:
        report.append(
            f"| {row['workload']} | {row['lane']} | "
            f"{row['median_wall_ns'] / 1e6:.3f} | {row['p95_wall_ns'] / 1e6:.3f} | "
            f"{row['physical_t5_bytes']} |"
        )
    report += [
        "", "Обидва виконувані файли використовують одну семантику SENS; їхня "
        "паритетність не замінює незалежний Lisp-оракул.",
        "Рекурсія, копіювання списку та MAP — різні обчислення; швидкість "
        "між ними не порівнюється як мовний speedup.",
        "Початковий паритет перевірено до часу вимірювання, кожний "
        "наступний stdout повинен збігатися побайтно.",
        "",
    ]
    report_text = "\n".join(report)
    (args.out / "d5-report.md").write_text(report_text, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as file:
            file.write(report_text)
    print(report_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
