#!/usr/bin/env python3
"""Measure one complete Ukrainian SENS source file through live AST and T5M."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures")
DEFAULT_SOURCE = FIXTURES / "arithmetic-before.lisp"
DEFAULT_CANDIDATE = FIXTURES / "arithmetic-constant-folded.lisp"
EXPECTED_RESULT = "23"


def invoke(command: list[str], *, timeout: int = 240) -> str:
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
    return result.stdout.strip()


def key_values(output: str) -> dict[str, str]:
    values = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def count_exact_words(projection: str) -> tuple[int, int]:
    words = projection.split()
    if not words:
        raise ValueError("empty exact-word projection")
    if any(not word or set(word) - {"0", "1"} for word in words):
        raise ValueError("non-binary token in exact-word projection")
    return len(words), sum(map(len, words))


def transport_trit_cost(word_count: int, semantic_bits: int, physical_bytes: int) -> dict[str, int]:
    """Count current T5 boundary/padding twos; semantic bits remain 0/1."""
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


def comparison_annotation(
    before: dict[str, int | str], after: dict[str, int | str]
) -> str:
    if before["result"] != after["result"]:
        raise ValueError(
            f"optimization candidate changes result: {before['result']!r} -> {after['result']!r}"
        )
    return (
        "::notice title=SENS optimization candidate::"
        f"visits={before['eval_visits']}→{after['eval_visits']}; "
        f"AST={before['lowered_ast_nodes']}→{after['lowered_ast_nodes']}; "
        f"words={before['exact_words']}→{after['exact_words']} "
        f"bits={before['exact_bits']}→{after['exact_bits']} "
        f"trit2={before['trit2_count']}→{after['trit2_count']}; "
        f"T5M={before['t5m_bytes']}→{after['t5m_bytes']} B; "
        f"result={before['result']}; parity=PASS"
    )


def measure(
    source: Path, helper: Path | None, sens: Path, sens_trit: Path,
    expected_result: str = EXPECTED_RESULT,
) -> dict[str, int | str]:
    source = source.resolve()
    sens = sens.resolve()
    sens_trit = sens_trit.resolve()
    if helper is None:
        ast_output = invoke([
            "cargo", "run", "--locked", "-p", "sens", "--example", "program_size",
            "--features", "benchmark-ast-visits", "--", str(source)
        ])
    else:
        ast_output = invoke([str(helper.resolve()), str(source)])
    stats = key_values(ast_output)
    required = (
        "FORMS", "SOURCE_BYTES", "AST_NODES", "LOWERED_AST_NODES",
        "EVAL_VISITS", "RESULT",
    )
    missing = [name for name in required if name not in stats]
    if missing:
        raise ValueError(f"AST helper omitted fields: {missing}")
    parsed = {
        name: int(stats[name])
        for name in required
        if name != "RESULT"
    }
    if parsed["FORMS"] < 1 or parsed["AST_NODES"] < 1:
        raise ValueError("SENS source has no measurable program AST")
    if parsed["SOURCE_BYTES"] != len(source.read_bytes()):
        raise ValueError("source byte count differs from the UTF-8 source file")

    with tempfile.TemporaryDirectory(prefix="sens-program-size-") as temporary:
        physical = Path(temporary) / "program.sens"
        invoke([str(sens), "--t5m-mint", str(source), str(physical)])
        if not physical.is_file() or not physical.stat().st_size:
            raise ValueError("SENS/Zig did not produce a non-empty physical T5M file")
        execution = invoke([str(sens), "--t5m-pair", str(source), str(physical)])
        projection = invoke([str(sens_trit), "open", str(physical)])
        exact_words, exact_bits = count_exact_words(projection)
        trit_cost = transport_trit_cost(exact_words, exact_bits, physical.stat().st_size)
        result = execution.splitlines()[-1].strip()
        if result != expected_result:
            raise ValueError(f"fixture result mismatch: expected {expected_result!r}, got {result!r}")
        if stats["RESULT"] != result:
            raise ValueError(
                f"source/lowered evaluator result {stats['RESULT']!r} differs from T5M result {result!r}"
            )
        return {
            "forms": parsed["FORMS"],
            "source_bytes": parsed["SOURCE_BYTES"],
            "ast_nodes": parsed["AST_NODES"],
            "lowered_ast_nodes": parsed["LOWERED_AST_NODES"],
            "eval_visits": parsed["EVAL_VISITS"],
            "exact_words": exact_words,
            "exact_bits": exact_bits,
            "trit2_count": trit_cost["trit2"],
            "trit2_separators": trit_cost["separators"],
            "trit2_tail": trit_cost["tail"],
            "t5m_bytes": physical.stat().st_size,
            "result": result,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--expect", default=EXPECTED_RESULT)
    parser.add_argument("--helper", type=Path, help="prebuilt SENS AST counter; default uses cargo run")
    parser.add_argument("--sens", type=Path, default=ROOT / "target/debug/sens")
    parser.add_argument("--sens-trit", type=Path, default=ROOT / "target/debug/sens-trit")
    args = parser.parse_args()
    before = measure(args.source, args.helper, args.sens, args.sens_trit, args.expect)
    after = measure(args.candidate, args.helper, args.sens, args.sens_trit, args.expect)
    print(comparison_annotation(before, after))
    print(
        f"SENS_PROGRAM_SIZE_COMPARE before_visits={before['eval_visits']} "
        f"candidate_visits={after['eval_visits']} before_ast={before['lowered_ast_nodes']} "
        f"candidate_ast={after['lowered_ast_nodes']} before_words={before['exact_words']} "
        f"candidate_words={after['exact_words']} before_bits={before['exact_bits']} "
        f"candidate_bits={after['exact_bits']} before_trit2={before['trit2_count']} "
        f"candidate_trit2={after['trit2_count']} before_t5m={before['t5m_bytes']} B "
        f"candidate_t5m={after['t5m_bytes']} B result={before['result']} parity=PASS"
    )
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write("## SENS — оптимізація повної програми\n\n")
            handle.write("| Варіант | Форми | AST вузли (джерело/нижній рівень) | Відвідані вузли | Слова / біти | Трити 2 | T5M | Результат |\n")
            handle.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
            for label, metrics in (("до", before), ("кандидат", after)):
                handle.write(
                    f"| {label} | {metrics['forms']} | "
                    f"{metrics['ast_nodes']} / {metrics['lowered_ast_nodes']} "
                    f"| {metrics['eval_visits']} | {metrics['exact_words']} / {metrics['exact_bits']} "
                    f"| {metrics['trit2_count']} ({metrics['trit2_separators']} межі + "
                    f"{metrics['trit2_tail']} pad) | {metrics['t5m_bytes']} Б "
                    f"| `{metrics['result']}` (PASS) |\n"
                )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"SENS_PROGRAM_SIZE FAIL: {error}", file=os.sys.stderr)
        raise SystemExit(2)
