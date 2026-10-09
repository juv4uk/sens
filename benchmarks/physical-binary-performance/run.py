#!/usr/bin/env python3
"""Measure physical SENS transport and execution, not Rust test duration.

Each sample launches a new process. The first timed sample is reported
separately from warm OS-cache medians; these are NOT in-process warm VM timings.
The two independent CLI entry points must emit identical observable bytes
before latency or size comparisons are admitted. No latency thresholds, no
invented speedup claims, and no name/semantic tables in the measurement code.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, typed_sha256

FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
)
LANES = ("sens-exec", "sens-trit-eval", "sens-trit-open")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def invoke(argv: list[str], *, timeout: int = 30) -> tuple[float, bytes]:
    start = time.perf_counter_ns()
    proc = subprocess.run(
        argv, cwd=ROOT, capture_output=True, check=False, timeout=timeout
    )
    elapsed = (time.perf_counter_ns() - start) / 1_000_000.0
    if proc.returncode != 0:
        raise RuntimeError(
            f"benchmark command returned {proc.returncode}: {argv!r}\n"
            f"{proc.stderr.decode('utf-8', errors='replace')[-2000:]}"
        )
    return elapsed, proc.stdout


def percentile_nearest_rank(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.partition(":")[2].strip()
    return platform.processor() or "unknown"


def i_refs(argv: list[str]) -> int:
    cmd = [
        "valgrind", "--tool=cachegrind", "--cache-sim=no", "--branch-sim=no",
        "--cachegrind-out-file=/dev/null", *argv,
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, check=False, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError(
            f"cachegrind failed: {cmd!r}\n"
            f"{proc.stderr.decode('utf-8', errors='replace')[-2000:]}"
        )
    match = re.search(rb"I\s+refs:\s+([\d,]+)", proc.stderr)
    if not match:
        raise RuntimeError("Cachegrind did not report instruction references")
    return int(match.group(1).replace(b",", b""))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens", type=Path, required=True)
    parser.add_argument("--sens-trit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=21)
    parser.add_argument("--warmup", type=int, default=4)
    parser.add_argument("--cachegrind", action="store_true")
    args = parser.parse_args()
    if args.reps < 5 or args.warmup < 1:
        parser.error("reps must be >= 5 and warmup >= 1")

    sens = str(args.sens.resolve())
    trit = str(args.sens_trit.resolve())
    for exe in (sens, trit):
        if not Path(exe).is_file():
            raise RuntimeError(f"compiled binary not found: {exe}")
    if args.cachegrind and not shutil.which("valgrind"):
        raise RuntimeError("requested Cachegrind but valgrind is not installed")

    args.out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    raw_rows: list[dict] = []
    summaries: list[dict] = []

    for fixture in FIXTURES:
        physical = ROOT / fixture
        if not physical.is_file():
            raise RuntimeError(f"fixture missing: {fixture}")
        payload = physical.read_bytes()
        if not payload:
            raise RuntimeError(f"fixture empty: {fixture}")

        commands = {
            "sens-exec": [sens, str(physical)],
            "sens-trit-eval": [trit, "eval", str(physical)],
            "sens-trit-open": [trit, "open", str(physical)],
        }
        # Перед замірами: дві виконавчі доріжки повинні збігатися.
        # Окремий Python T5-декодер доводить точну транспортну проєкцію,
        # але сам по собі НЕ встановлює семантичних законів мови.
        first_invocations = {lane: invoke(cmd) for lane, cmd in commands.items()}
        baseline = {lane: result for lane, (_, result) in first_invocations.items()}
        if baseline["sens-exec"] != baseline["sens-trit-eval"]:
            raise RuntimeError(f"{fixture}: two execution lanes disagree")
        words = decode_bytes(payload)
        if encode_words(words) != payload:
            raise RuntimeError(f"{fixture}: T5 roundtrip disagrees with physical file")
        visible = (" ".join(words) + "\n").encode("ascii")
        if baseline["sens-trit-open"] != visible:
            raise RuntimeError(f"{fixture}: Rust T5 view differs from independent Python decode")
        visible_bytes = len(visible)
        dimensions = {
            "fixture": fixture,
            "physical_bytes": len(payload),
            "visible_binary_bytes": visible_bytes,
            "visible_to_physical_ratio": round(visible_bytes / len(payload), 5),
            "physical_sha256": sha256(payload),
            "exact_word_count": len(words),
            "typed_words_sha256": typed_sha256(words),
            "execution_stdout_sha256": sha256(baseline["sens-exec"]),
            "visible_sha256": sha256(visible),
            "mechanism_parity": "PASS",
            "independent_t5_roundtrip": "PASS",
        }

        samples: dict[str, list[float]] = {lane: [] for lane in LANES}
        # Перший вимір — preflight invocation, до всіх прогрівів бенчмарка.
        # Це НЕ гарантія порожнього OS page cache.
        first_sample = {lane: elapsed for lane, (elapsed, _) in first_invocations.items()}
        # Rotate order each repetition so one lane cannot always benefit from
        # the same OS cache state. Never label subprocess medians "warm VM".
        for iteration in range(args.reps + args.warmup):
            order = LANES[iteration % 3 :] + LANES[: iteration % 3]
            for lane in order:
                elapsed, output = invoke(commands[lane])
                if output != baseline[lane]:
                    raise RuntimeError(
                        f"{fixture}: nondeterministic output in {lane} at {iteration}"
                    )
                if iteration >= args.warmup:
                    samples[lane].append(elapsed)
                    raw_rows.append(
                        {
                            "sha": commit,
                            "fixture": fixture,
                            "lane": lane,
                            "rep": iteration - args.warmup + 1,
                            "wall_ms": f"{elapsed:.6f}",
                            "stdout_sha256": sha256(output),
                        }
                    )

        for lane in LANES:
            values = samples[lane]
            row = {
                **dimensions,
                "lane": lane,
                "reps": len(values),
                "first_process_ms": round(first_sample[lane], 6),
                "median_wall_ms": round(statistics.median(values), 6),
                "p95_wall_ms": round(percentile_nearest_rank(values, 0.95), 6),
                "min_wall_ms": round(min(values), 6),
                "max_wall_ms": round(max(values), 6),
                "wall_cv": round(statistics.pstdev(values) / statistics.mean(values), 6),
                "cachegrind_i_refs": None,
            }
            if args.cachegrind:
                row["cachegrind_i_refs"] = i_refs(commands[lane])
            summaries.append(row)
        print(
            f"{fixture}: transport={len(payload)} bytes, visible={visible_bytes} "
            f"bytes, execution/parity=PASS",
            flush=True,
        )

    with (args.out / "raw.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(raw_rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(raw_rows)
    report = {
        "schema": "sens-physical-binary-performance/v1",
        "commit_sha": commit,
        "utc": datetime.now(timezone.utc).isoformat(),
        "measurement": "first preflight invocation and process-per-call wall latency after warmups; OS cache state uncontrolled",
        "in_process_warm_execution_measured": False,
        "cross_machine_relative_rank_admissible": False,
        "semantic_correctness_oracle": "EXTERNAL_NOT_PROVEN_BY_THIS_BENCH",
        "transport_parity_oracle": "INDEPENDENT_PYTHON_T5_ROUNDTRIP_AND_EXACT_VIEW",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": cpu_model(),
        "python": sys.version.split()[0],
        "reps": args.reps,
        "warmup": args.warmup,
        "cachegrind_enabled": args.cachegrind,
        "results": summaries,
    }
    (args.out / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Фізична двійкова SENS — вимірювання часу й щільності",
        "",
        f"Commit: `{commit}`; runner CPU: {cpu_model()}",
        "",
        "| Програма | Шлях | Медіана, мс | p95, мс | Перший preflight, мс | I refs |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summaries:
        refs = str(row["cachegrind_i_refs"]) if row["cachegrind_i_refs"] is not None else "—"
        lines.append(
            f"| {Path(row['fixture']).name} | {row['lane']} | "
            f"{row['median_wall_ms']:.3f} | {row['p95_wall_ms']:.3f} | "
            f"{row['first_process_ms']:.3f} | {refs} |"
        )
    lines.extend(
        [
            "",
            "## Реальна щільність",
            "",
            "| Файл | Фізичні байти | Видимі ASCII-байти | Видимі / фізичні |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in summaries[::3]:
        lines.append(
            f"| {Path(row['fixture']).name} | {row['physical_bytes']} | "
            f"{row['visible_binary_bytes']} | {row['visible_to_physical_ratio']:.3f}× |"
        )
    lines.extend(
        [
            "",
            "Обидві CLI-дороги дали однакові байти результату. Це лише parity",
            "механізмів; семантичні закони встановлюють Lisp-оракули.",
            "Кожна вибірка запускає **новий процес**. p95 — nearest-rank;",
            "міжмашинні порівняння без однакового обладнання невалідні.",
            "Час відлічується навколо subprocess і включає startup, I/O та stdout.",
            "Перший preflight замір перед прогрівами; холодний OS page cache НЕ доведений.",
            "Видимі байти рахуються з канонічним кінцевим LF, перевіреним Python T5-кодеком.",
            "Ширина кожного слова збережена в typed SHA256; це транспортний доказ.",
            "",
        ]
    )
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
