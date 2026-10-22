#!/usr/bin/env python3
"""Measure changed physical SENS programs through Zig T5M and the SENS evaluator."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METRICS = re.compile(
    r"^SENS_BINARY_BENCH AST_NODES=(\d+) EVAL_VISITS=(\d+) RESULT=(.*)$"
)


def invoke(command: list[str], *, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command!r}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load_binary_paths(entries: list[str], root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    binaries: list[Path] = []
    seen: set[Path] = set()
    for raw in entries:
        entry = raw.strip()
        if not entry:
            continue
        relative = Path(entry)
        if relative.is_absolute() or relative.suffix != ".sens":
            raise ValueError(f"expected a .sens binary path relative to repository: {entry}")
        path = root / relative
        resolved = path.resolve()
        if root not in resolved.parents or path.is_symlink() or not path.is_file():
            raise ValueError(f"binary path must be a regular in-repository file: {entry}")
        if path.stat().st_size == 0:
            raise ValueError(f"empty physical SENS binary: {entry}")
        if resolved not in seen:
            binaries.append(path)
            seen.add(resolved)
    if not binaries:
        raise ValueError("binary manifest contains no physical .sens programs")
    return binaries


def load_binary_manifest(manifest: Path, root: Path = ROOT) -> list[Path]:
    if not manifest.is_file():
        raise ValueError(f"binary manifest does not exist: {manifest}")
    return load_binary_paths(manifest.read_text(encoding="utf-8").splitlines(), root)


def count_exact_words(projection: str) -> tuple[int, int]:
    words = projection.split()
    if not words:
        raise ValueError("empty exact-word projection")
    if any(set(word) - {"0", "1"} for word in words):
        raise ValueError("non-binary token in exact-word projection")
    return len(words), sum(map(len, words))


def transport_trit_cost(word_count: int, semantic_bits: int, physical_bytes: int) -> dict[str, int]:
    """Count current T5 framing/padding twos; SENS semantic words stay binary."""
    if word_count < 1 or semantic_bits < 1 or physical_bytes < 1:
        raise ValueError("T5 transport accounting needs non-empty words and bytes")
    separators = word_count - 1
    encoded_trits = semantic_bits + separators
    expected_bytes = (encoded_trits + 4) // 5
    if physical_bytes != expected_bytes:
        raise ValueError(
            "decoded exact words disagree with physical T5 byte count: "
            f"expected {expected_bytes}, got {physical_bytes}"
        )
    tail = physical_bytes * 5 - encoded_trits
    if not 0 <= tail <= 4:
        raise ValueError(f"non-canonical T5 tail length: {tail}")
    return {"separators": separators, "tail": tail, "trit2": separators + tail}


def parse_binary_metrics(stderr: str) -> dict[str, int | str]:
    matches = [METRICS.fullmatch(line) for line in stderr.splitlines()]
    metrics = [match for match in matches if match]
    if len(metrics) != 1:
        raise ValueError(f"missing binary metrics: expected one SENS_BINARY_BENCH line, got {len(metrics)}")
    match = metrics[0]
    ast_nodes, eval_visits, result = match.groups()
    if not result:
        raise ValueError("binary evaluator returned an empty result field")
    return {"ast_nodes": int(ast_nodes), "eval_visits": int(eval_visits), "result": result}


def measure_binary(binary: Path, sens: Path, sens_trit: Path) -> dict[str, int | str]:
    binary = binary.resolve()
    sens = sens.resolve()
    sens_trit = sens_trit.resolve()
    physical_bytes = binary.stat().st_size
    projection = invoke([str(sens_trit), "open", str(binary)]).stdout
    exact_words, exact_bits = count_exact_words(projection)
    transport = transport_trit_cost(exact_words, exact_bits, physical_bytes)
    execution = invoke([str(sens), "--benchmark-physical", str(binary)])
    runtime = parse_binary_metrics(execution.stderr)
    output_lines = execution.stdout.splitlines()
    if not output_lines or output_lines[-1].strip() != runtime["result"]:
        raise ValueError(
            f"binary result/metrics disagree for {binary}: "
            f"stdout={output_lines[-1:]!r}, metrics={runtime['result']!r}"
        )
    return {
        **runtime,
        "path": binary.relative_to(ROOT).as_posix(),
        "exact_words": exact_words,
        "exact_bits": exact_bits,
        "trit2_count": transport["trit2"],
        "trit2_separators": transport["separators"],
        "trit2_tail": transport["tail"],
        "t5m_bytes": physical_bytes,
    }


def binary_annotation(path: str, metrics: dict[str, int | str]) -> str:
    return (
        f"::notice title=SENS binary program::path={path}; AST={metrics['ast_nodes']}; "
        f"visits={metrics['eval_visits']}; words={metrics['exact_words']} "
        f"bits={metrics['exact_bits']} trit2={metrics['trit2_count']}; "
        f"T5M={metrics['t5m_bytes']} B; result={metrics['result']}"
    )



def benchmark_summary_annotation(results: list[dict[str, int | str]]) -> str:
    """Summarize only programs actually executed through the physical SENS path."""
    if not results:
        raise ValueError("cannot summarize an empty measured cohort")
    return (
        "::notice title=SENS T5M executable cohort::"
        f"programs={len(results)}; "
        f"T5M={sum(int(row['t5m_bytes']) for row in results)} B; "
        f"AST nodes={sum(int(row['ast_nodes']) for row in results)}; "
        f"evaluator visits={sum(int(row['eval_visits']) for row in results)}; "
        f"words={sum(int(row['exact_words']) for row in results)}; "
        f"semantic bits={sum(int(row['exact_bits']) for row in results)}; "
        "execution/parity=PASS; no wall-time claim"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--binary-list", type=Path,
                        help="newline-delimited repository-relative physical .sens paths")
    inputs.add_argument("--binary", action="append",
                        help="repository-relative physical .sens input; may be repeated")
    parser.add_argument("--sens", type=Path, default=ROOT / "target/debug/sens")
    parser.add_argument("--sens-trit", type=Path, default=ROOT / "target/debug/sens-trit")
    args = parser.parse_args()

    binaries = (
        load_binary_manifest(args.binary_list)
        if args.binary_list
        else load_binary_paths(args.binary)
    )
    results = [measure_binary(binary, args.sens, args.sens_trit) for binary in binaries]
    for metrics in results:
        print(binary_annotation(str(metrics["path"]), metrics))
        print(
            f"SENS_BINARY_PROGRAM path={metrics['path']} ast={metrics['ast_nodes']} "
            f"visits={metrics['eval_visits']} words={metrics['exact_words']} "
            f"bits={metrics['exact_bits']} trit2={metrics['trit2_count']} "
            f"t5m_bytes={metrics['t5m_bytes']} result={metrics['result']}"
        )
    print(f"SENS_BINARY_BENCHMARKED count={len(results)} input=physical-sens parity=PASS")
    print(benchmark_summary_annotation(results))

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write("## SENS — бенчмарк бінарних програм `.sens`\n\n")
            handle.write("Вхід — фізичні бінарні програми; виконання — через Zig/T5M і evaluator SENS.\n\n")
            handle.write("| Бінарна програма | AST вузли | Відвідування | Слова / біти | Трити 2 | T5M | Результат |\n")
            handle.write("|---|---:|---:|---:|---:|---:|---|\n")
            for metrics in results:
                handle.write(
                    f"| `{metrics['path']}` | {metrics['ast_nodes']} | {metrics['eval_visits']} "
                    f"| {metrics['exact_words']} / {metrics['exact_bits']} "
                    f"| {metrics['trit2_count']} ({metrics['trit2_separators']} межі + "
                    f"{metrics['trit2_tail']} pad) | {metrics['t5m_bytes']} Б "
                    f"| `{metrics['result']}` (PASS) |\n"
                )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"SENS_BINARY_BENCH FAIL: {error}", file=sys.stderr)
        raise SystemExit(2)
