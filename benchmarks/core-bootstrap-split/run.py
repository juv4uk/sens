#!/usr/bin/env python3
"""#3629 — діагностичний split cold Core bootstrap.

Старі startup_bench modes лишаються provenance-compatible. Нові root-* controls
відділяють чистий Environment::root() від Session::default(), який уже
завантажує macro library.

Primary metric: Cachegrind I refs. Wall time — допоміжний.
Незалежні process modes не трактуються як вкладені таймери.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import time
from pathlib import Path

MODES = (
    "root",
    "session",
    "root-macro",
    "macro",
    "root-core",
    "core",
    "bytes",
    "decode",
    "parse",
)
FASL_MODES = {"bytes", "decode"}
IREF_RE = re.compile(r"I\s+refs:\s*([\d,]+)")


def command(runner: Path, mode: str, fasl: Path) -> list[str]:
    cmd = [str(runner), mode]
    if mode in FASL_MODES:
        cmd.append(str(fasl))
    return cmd


def viability(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"mode failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
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
    match = IREF_RE.search(proc.stderr)
    if match is None:
        raise RuntimeError(f"Cachegrind did not report I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def wall_seconds(cmd: list[str]) -> float:
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise RuntimeError(
            f"mode failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr}"
        )
    return elapsed


def median(rows: list[dict[str, object]], mode: str, field: str) -> float:
    values = [float(row[field]) for row in rows if row["mode"] == mode]
    if not values:
        raise ValueError(f"no rows for mode={mode}")
    return statistics.median(values)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runner", type=Path, required=True)
    ap.add_argument("--fasl", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.reps < 3:
        raise ValueError("--reps must be >= 3 for #3629 decision rows")

    runner = args.runner.resolve()
    fasl = args.fasl.resolve()
    if not runner.is_file():
        raise FileNotFoundError(runner)
    if not fasl.is_file():
        raise FileNotFoundError(fasl)

    rows: list[dict[str, object]] = []
    for mode in MODES:
        cmd = command(runner, mode, fasl)
        viability(cmd)
        for rep in range(1, args.reps + 1):
            rows.append(
                {
                    "schema": "sens-core-bootstrap-split/v1",
                    "mode": mode,
                    "rep": rep,
                    "i_refs": irefs(cmd),
                    "wall_s": wall_seconds(cmd),
                }
            )
        print(f"[core-bootstrap-3629] {mode}: OK")

    args.out.mkdir(parents=True, exist_ok=True)
    jsonl = args.out / "rows.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    med_i = {mode: int(median(rows, mode, "i_refs")) for mode in MODES}
    med_w = {mode: median(rows, mode, "wall_s") for mode in MODES}

    derived = {
        "default_session_minus_root_i_refs": med_i["session"] - med_i["root"],
        "first_macro_minus_root_i_refs": med_i["root-macro"] - med_i["root"],
        "second_macro_minus_session_i_refs": med_i["macro"] - med_i["session"],
        "root_core_minus_root_i_refs": med_i["root-core"] - med_i["root"],
        "default_core_minus_session_i_refs": med_i["core"] - med_i["session"],
        "legacy_bytes_minus_session_i_refs": med_i["bytes"] - med_i["session"],
        "legacy_decode_minus_session_i_refs": med_i["decode"] - med_i["session"],
        "legacy_parse_minus_session_i_refs": med_i["parse"] - med_i["session"],
    }

    summary = {
        "schema": "sens-core-bootstrap-split-summary/v1",
        "reps": args.reps,
        "median_i_refs": med_i,
        "median_wall_s": med_w,
        "derived_diagnostics": derived,
        "interpretation_guard": (
            "independent process modes; deltas are diagnostic comparisons, "
            "not nested phase subtraction"
        ),
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# #3629 Core bootstrap split",
        "",
        "Primary metric: Cachegrind I refs. Wall time is auxiliary.",
        "",
        "| mode | median I refs | median wall, ms |",
        "|---|---:|---:|",
    ]
    for mode in MODES:
        lines.append(f"| {mode} | {med_i[mode]:,} | {med_w[mode] * 1000:.3f} |")

    lines += [
        "",
        "## Diagnostic deltas",
        "",
        "| comparison | I refs |",
        "|---|---:|",
    ]
    for name, value in derived.items():
        lines.append(f"| {name} | {value:,} |")

    lines += [
        "",
        "Interpretation guard: these are independent process modes, not nested timers.",
        "session already includes the first macro bootstrap by Session::default().",
        "macro therefore measures a second explicit macro load on top of default Session.",
        "root-core is the full public load_core_library path starting from bare Environment::root().",
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
