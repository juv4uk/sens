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


def numeric_memory_commands(
    sens_memory_bench: Path, width_bits: int, retained_values: int
) -> list[tuple[str, list[str]]]:
    """Same SENS evaluator workload, varying only the retained-copy strategy."""
    common = [str(width_bits), str(retained_values)]
    return [
        (
            "SENS evaluator / shared clone",
            [str(sens_memory_bench), "shared", *common],
        ),
        (
            "SENS evaluator / deep-copy control",
            [str(sens_memory_bench), "deep-copy", *common],
        ),
    ]


def run_numeric_memory_benchmark(
    sens_memory_bench: Path,
    repetitions: int,
    width_bits: int,
    retained_values: int,
) -> list[dict[str, object]]:
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    if width_bits < 1 or retained_values < 1:
        raise ValueError("numeric width and retained value count must be positive")
    if not sens_memory_bench.is_file():
        raise RuntimeError(f"SENS numeric memory benchmark not found: {sens_memory_bench}")
    rss = _load_rss()
    rows: list[dict[str, object]] = []
    for strategy, command in numeric_memory_commands(
        sens_memory_bench, width_bits, retained_values
    ):
        samples = []
        for _ in range(repetitions):
            stdout, _stderr, peak_kib = rss.measure_peak_rss_kb(command)
            fields = stdout.strip().split("\t")
            expected = [
                "SENS_NUMERIC_MEMORY",
                f"mode={command[1]}",
                f"width_bits={width_bits}",
                f"retained={retained_values}",
                f"verified={retained_values}",
            ]
            if fields != expected:
                raise RuntimeError(
                    f"{strategy} produced unexpected runtime witness {stdout.strip()!r}; "
                    f"expected {expected!r}"
                )
            samples.append(peak_kib)
        rows.append(
            {
                "strategy": strategy,
                "width_bits": width_bits,
                "retained_values": retained_values,
                "samples_kib": samples,
            }
        )
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


def render_numeric_report(rows: list[dict[str, object]], repetitions: int) -> str:
    if len(rows) != 2:
        raise ValueError("numeric memory report requires shared and deep-copy control rows")
    if [row["strategy"] for row in rows] != [
        "SENS evaluator / shared clone",
        "SENS evaluator / deep-copy control",
    ]:
        raise ValueError("numeric memory report rows are missing or reordered")
    if any(
        row["width_bits"] != rows[0]["width_bits"]
        or row["retained_values"] != rows[0]["retained_values"]
        for row in rows[1:]
    ):
        raise ValueError("numeric memory rows must use the same width and retained count")
    summaries = []
    for row in rows:
        samples = [int(value) for value in row["samples_kib"]]
        if len(samples) != repetitions or not samples:
            raise ValueError("numeric memory row has missing RSS samples")
        summaries.append((statistics.median(samples), samples))
    delta = summaries[1][0] - summaries[0][0]
    lines = [
        "## Пам’ять числового шляху SENS evaluator",
        "",
        f"Те саме виконання D3 `як-є` над D24+ словом шириною {int(rows[0]['width_bits']):,} біт; "
        f"утримується {int(rows[0]['retained_values']):,} результатів, {repetitions} свіжі процеси на режим.",
        "RSS охоплює весь процес, включно зі стартом; це не ізольована ціна даних і не CPU-бенчмарк.",
        "Deep-copy контроль відтворює копіювання, а не старий бінарник; це не є міжмовним рейтингом.",
        "Обидва режими перевіряють однаковий точний домен і кількість утриманих результатів до заміру.",
        "",
        "| Стратегія | Медіана RSS, KiB | Сирі заміри, KiB |",
        "|---|---:|---|",
    ]
    for row, (median, samples) in zip(rows, summaries, strict=True):
        median_text = f"{median:,.1f}" if median != int(median) else f"{int(median):,}"
        raw = ", ".join(f"{sample:,}" for sample in samples)
        lines.append(f"| {row['strategy']} | {median_text} | {raw} |")
    lines.extend(
        [
            "",
            f"Різниця медіан (deep-copy control − shared clone): {delta:,.1f} KiB.",
            "Це вузький evaluator microbenchmark: він не вимірює декодування T5M, повний застосунок або інші інтерпретатори.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens-trit", type=Path, default=ROOT / "target/debug/sens-trit")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--sens-memory-bench",
        type=Path,
        default=ROOT / "target/debug/examples/sens_numeric_memory_bench",
    )
    parser.add_argument("--numeric-width-bits", type=int, default=196608)
    parser.add_argument("--numeric-retained-values", type=int, default=128)
    args = parser.parse_args()

    report = render_report(run_benchmark(args.sens_trit, args.repetitions), args.repetitions)
    numeric_report = render_numeric_report(
        run_numeric_memory_benchmark(
            args.sens_memory_bench,
            args.repetitions,
            args.numeric_width_bits,
            args.numeric_retained_values,
        ),
        args.repetitions,
    )
    report = f"{report}\n{numeric_report}"
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
