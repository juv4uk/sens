#!/usr/bin/env python3
"""Measure one complete Ukrainian SENS source file through live AST and T5M."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = Path(__file__).with_name("fixtures") / "decimal-arithmetic.lisp"
EXPECTED_RESULT = "2"


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


def annotation(metrics: dict[str, int | str]) -> str:
    return (
        "::notice title=SENS whole-program size::"
        f"forms={metrics['forms']}; source={metrics['source_bytes']} B; "
        f"AST={metrics['ast_nodes']}/"
        f"{metrics['lowered_ast_nodes']} nodes (source/lowered); "
        f"words={metrics['exact_words']} bits={metrics['exact_bits']}; "
        f"T5M={metrics['t5m_bytes']} B; result={metrics['result']}"
    )


def measure(
    source: Path, helper: Path | None, sens: Path, sens_trit: Path
) -> dict[str, int | str]:
    source = source.resolve()
    sens = sens.resolve()
    sens_trit = sens_trit.resolve()
    if helper is None:
        ast_output = invoke([
            "cargo", "run", "--locked", "-p", "sens", "--example", "program_size", "--", str(source)
        ])
    else:
        ast_output = invoke([str(helper.resolve()), str(source)])
    stats = key_values(ast_output)
    required = ("FORMS", "SOURCE_BYTES", "AST_NODES", "LOWERED_AST_NODES")
    missing = [name for name in required if name not in stats]
    if missing:
        raise ValueError(f"AST helper omitted fields: {missing}")
    parsed = {name: int(stats[name]) for name in required}
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
        result = execution.splitlines()[-1].strip()
        if result != EXPECTED_RESULT:
            raise ValueError(f"fixture result mismatch: expected {EXPECTED_RESULT!r}, got {result!r}")
        return {
            "forms": parsed["FORMS"],
            "source_bytes": parsed["SOURCE_BYTES"],
            "ast_nodes": parsed["AST_NODES"],
            "lowered_ast_nodes": parsed["LOWERED_AST_NODES"],
            "exact_words": exact_words,
            "exact_bits": exact_bits,
            "t5m_bytes": physical.stat().st_size,
            "result": result,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--helper", type=Path, help="prebuilt SENS AST counter; default uses cargo run")
    parser.add_argument("--sens", type=Path, default=ROOT / "target/debug/sens")
    parser.add_argument("--sens-trit", type=Path, default=ROOT / "target/debug/sens-trit")
    args = parser.parse_args()
    metrics = measure(args.source, args.helper, args.sens, args.sens_trit)
    print(annotation(metrics))
    print(
        f"SENS_PROGRAM_SIZE forms={metrics['forms']} source={metrics['source_bytes']} B "
        f"ast={metrics['ast_nodes']} lowered_ast={metrics['lowered_ast_nodes']} "
        f"words={metrics['exact_words']} bits={metrics['exact_bits']} "
        f"t5m={metrics['t5m_bytes']} B result={metrics['result']} parity=PASS"
    )
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write("## SENS — розмір повної програми\n\n")
            handle.write("| Форми | AST вузли (джерело/нижній рівень) | Точні слова | Біти | Фізичний T5M | Результат |\n")
            handle.write("|---:|---:|---:|---:|---:|---:|\n")
            handle.write(
                f"| {metrics['forms']} | {metrics['ast_nodes']} / {metrics['lowered_ast_nodes']} "
                f"| {metrics['exact_words']} | {metrics['exact_bits']} | "
                f"{metrics['t5m_bytes']} Б | `{metrics['result']}` (PASS) |\n"
            )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"SENS_PROGRAM_SIZE FAIL: {error}", file=os.sys.stderr)
        raise SystemExit(2)
