#!/usr/bin/env python3
"""Small, fresh-process peak-RSS smoke comparison for language interpreters."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RSS_PATH = ROOT / "benchmarks/cross-language/reality-matrix/rss.py"
SENS_PROGRAM = ROOT / "examples/binary/d3-cond-program.sens"
EXPECTED = "1"


def _load_rss():
    spec = importlib.util.spec_from_file_location("sens_reality_matrix_rss", RSS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shared RSS measurement helper: {RSS_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _required_command(names: tuple[str, ...]) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(f"required interpreter not found (tried: {', '.join(names)})")


def commands(sens_trit: Path) -> list[tuple[str, list[str]]]:
    lua = _required_command(("lua", "lua5.4", "lua5.3"))
    guile = _required_command(("guile",))
    if not sens_trit.is_file():
        raise RuntimeError(f"sens-trit executable not found: {sens_trit}")
    if not SENS_PROGRAM.is_file():
        raise RuntimeError(f"physical SENS fixture not found: {SENS_PROGRAM}")
    return [
        ("SENS / T5M", [str(sens_trit), "eval", str(SENS_PROGRAM)]),
        ("Python", [sys.executable, "-B", str(HERE / "programs/conditional.py")]),
        (
            "Guile",
            [guile, "--no-auto-compile", "-s", str(HERE / "programs/conditional.scm")],
        ),
        ("Lua", [lua, str(HERE / "programs/conditional.lua")]),
    ]


def run_benchmark(sens_trit: Path, repetitions: int) -> list[dict[str, object]]:
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    rss = _load_rss()
    rows: list[dict[str, object]] = []
    for language, command in commands(sens_trit):
        samples = []
        for _ in range(repetitions):
            stdout, _stderr, peak_kib = rss.measure_peak_rss_kb(command)
            result = stdout.strip()
            if result != EXPECTED:
                raise RuntimeError(
                    f"{language} produced {result!r}; expected the shared result {EXPECTED!r}"
                )
            samples.append(peak_kib)
        rows.append({"language": language, "samples_kib": samples})
    return rows


def render_report(rows: list[dict[str, object]], repetitions: int) -> str:
    lines = [
        "## Пікова пам’ять інтерпретаторів — smoke",
        "",
        f"Однаковий малий умовний сценарій; {repetitions} свіжі процеси на реалізацію.",
        "Вимір — піковий RSS для всього процесу в KiB, включно з інтерпретатором і програмою.",
        "Це не приріст пам’яті лише від програми й не рейтинг усіх мов.",
        "",
        "| Мова / шлях виконання | Медіана пікового RSS, KiB | Сирі заміри, KiB |",
        "|---|---:|---|",
    ]
    for row in rows:
        samples = [int(value) for value in row["samples_kib"]]
        median = statistics.median(samples)
        median_text = str(int(median)) if median == int(median) else f"{median:.1f}"
        raw = ", ".join(str(value) for value in samples)
        lines.append(f"| {row['language']} | {median_text} | {raw} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens-trit", type=Path, default=ROOT / "target/debug/sens-trit")
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()

    report = render_report(run_benchmark(args.sens_trit, args.repetitions), args.repetitions)
    print(report, end="")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(report)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"INTERPRETER_MEMORY_BENCH_FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
