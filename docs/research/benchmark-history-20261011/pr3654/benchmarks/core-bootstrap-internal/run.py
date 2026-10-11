#!/usr/bin/env python3
"""#3648 private Core bootstrap stage decomposition.

Runs one ignored sens lib-test under identical test-harness overhead. The stage
is selected only through SENS_BOOTSTRAP_MEASURE_STAGE.

Primary metric: Cachegrind I refs. Wall time is auxiliary.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import time
from pathlib import Path

STAGES = (
    "root",
    "profile",
    "macro",
    "decode",
    "eval-no-peers",
    "eval-with-peers",
    "full-loader",
)
TEST_FILTER = "bootstrap_measurement::bootstrap_measure_dispatch"
IREF_RE = re.compile(r"I\s+refs:\s*([\d,]+)")


def command(test_binary: Path) -> list[str]:
    return [
        str(test_binary),
        TEST_FILTER,
        "--exact",
        "--ignored",
        "--nocapture",
        "--test-threads=1",
    ]


def stage_env(stage: str) -> dict[str, str]:
    env = dict(os.environ)
    env["SENS_BOOTSTRAP_MEASURE_STAGE"] = stage
    return env


def viability(test_binary: Path, stage: str) -> None:
    proc = subprocess.run(
        command(test_binary),
        env=stage_env(stage),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"stage={stage} failed ({proc.returncode})\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )


def irefs(test_binary: Path, stage: str) -> int:
    proc = subprocess.run(
        [
            "valgrind",
            "--tool=cachegrind",
            "--cache-sim=no",
            "--cachegrind-out-file=/dev/null",
            *command(test_binary),
        ],
        env=stage_env(stage),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"cachegrind stage={stage} failed ({proc.returncode})\n{proc.stderr}"
        )
    match = IREF_RE.search(proc.stderr)
    if match is None:
        raise RuntimeError(
            f"Cachegrind did not report I refs for stage={stage}\n{proc.stderr}"
        )
    return int(match.group(1).replace(",", ""))


def wall_seconds(test_binary: Path, stage: str) -> float:
    started = time.perf_counter()
    proc = subprocess.run(
        command(test_binary),
        env=stage_env(stage),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise RuntimeError(
            f"wall stage={stage} failed ({proc.returncode})\n{proc.stderr}"
        )
    return elapsed


def median(rows: list[dict[str, object]], stage: str, field: str) -> float:
    values = [float(row[field]) for row in rows if row["stage"] == stage]
    if not values:
        raise ValueError(f"no rows for stage={stage}")
    return statistics.median(values)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test-binary", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--git-sha", required=True)
    ap.add_argument("--contract-version", default="11.6")
    args = ap.parse_args()

    if args.reps < 3:
        raise ValueError("--reps must be >= 3")
    if not re.fullmatch(r"[0-9a-f]{40}", args.git_sha):
        raise ValueError("--git-sha must be a 40-hex commit SHA")

    test_binary = args.test_binary.resolve()
    if not test_binary.is_file():
        raise FileNotFoundError(test_binary)

    rows: list[dict[str, object]] = []
    for stage in STAGES:
        viability(test_binary, stage)
        for rep in range(1, args.reps + 1):
            rows.append(
                {
                    "schema": "sens-core-bootstrap-internal/v1",
                    "git_sha": args.git_sha,
                    "contract_version": args.contract_version,
                    "stage": stage,
                    "rep": rep,
                    "i_refs": irefs(test_binary, stage),
                    "wall_s": wall_seconds(test_binary, stage),
                }
            )
        print(f"[core-bootstrap-3648] {stage}: OK")

    med_i = {stage: int(median(rows, stage, "i_refs")) for stage in STAGES}
    med_w = {stage: median(rows, stage, "wall_s") for stage in STAGES}

    stage_deltas = {
        "profile_setup_i_refs": med_i["profile"] - med_i["root"],
        "first_macro_i_refs": med_i["macro"] - med_i["profile"],
        "fasl_decode_freshness_i_refs": med_i["decode"] - med_i["macro"],
        "decoded_core_eval_i_refs": med_i["eval-no-peers"] - med_i["decode"],
        "stable_peer_projection_i_refs": (
            med_i["eval-with-peers"] - med_i["eval-no-peers"]
        ),
        "production_loader_gap_i_refs": (
            med_i["full-loader"] - med_i["eval-with-peers"]
        ),
        "full_loader_delta_i_refs": med_i["full-loader"] - med_i["root"],
    }

    full_delta = stage_deltas["full_loader_delta_i_refs"]
    shares = {
        key.removesuffix("_i_refs") + "_share":
            (value / full_delta if full_delta else None)
        for key, value in stage_deltas.items()
        if key not in {"full_loader_delta_i_refs", "production_loader_gap_i_refs"}
    }

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "rows.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = {
        "schema": "sens-core-bootstrap-internal-summary/v1",
        "git_sha": args.git_sha,
        "contract_version": args.contract_version,
        "reps": args.reps,
        "test_filter": TEST_FILTER,
        "median_i_refs": med_i,
        "median_wall_s": med_w,
        "stage_deltas": stage_deltas,
        "stage_shares_of_full_loader": shares,
        "measurement_law": (
            "single identical ignored test harness; adjacent stage controls share "
            "the same prefix and differ only by the named added stage"
        ),
        "api_boundary": "test-only private access; no public semantic API added",
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# #3648 Internal Core bootstrap split",
        "",
        f"Contract: {args.contract_version}",
        f"SHA: {args.git_sha}",
        f"Repetitions: {args.reps}",
        "",
        "| stage | median I refs | median wall, ms |",
        "|---|---:|---:|",
    ]
    for stage in STAGES:
        lines.append(
            f"| {stage} | {med_i[stage]:,} | {med_w[stage] * 1000:.3f} |"
        )

    lines += [
        "",
        "## Matched-prefix stage deltas",
        "",
        "| stage delta | I refs |",
        "|---|---:|",
    ]
    for name, value in stage_deltas.items():
        lines.append(f"| {name} | {value:,} |")

    lines += [
        "",
        "Measurement law: one identical ignored test is reused for every stage.",
        "Adjacent controls share the same prefix and differ only by the named stage.",
        "The harness is cfg(test)-only and adds no public semantic API.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        RuntimeError,
        ValueError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2)
