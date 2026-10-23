#!/usr/bin/env python3
"""Зіставляє source-to-result запуск T5 SENS та Python для одного pair-copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_t5m_codec import decode_bytes, encode_words, parse_words  # noqa: E402

CASE = "d5-label-copy"
SOURCE_WORDS = ROOT / "examples/binary/d5-label-copy.bits"
PYTHON_SOURCE = Path(__file__).parent / "fixtures/recursive_pair_copy.py"
EXPECTED = "(1 0 ())\n"


def check_parity(sens_output: str, python_output: str) -> bool:
    return bool(sens_output) and sens_output == python_output


def python_command(source: Path) -> list[str]:
    return [sys.executable, str(source.resolve(strict=True))]


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def p95(values: list[int]) -> int:
    ordered = sorted(values)
    rank = (95 * len(ordered) + 99) // 100
    return ordered[rank - 1]


def cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(errors="replace").splitlines():
            if line.startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def invoke(command: list[str], cwd: Path) -> tuple[str, int]:
    started = time.perf_counter_ns()
    completed = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False, timeout=30
    )
    elapsed = time.perf_counter_ns() - started
    if completed.returncode:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {command!r}; "
            f"stderr={completed.stderr[-1600:]!r}"
        )
    return completed.stdout, elapsed


def run(args: argparse.Namespace) -> dict:
    sens_cli = args.sens_trit.resolve(strict=True)
    if not PYTHON_SOURCE.is_file() or not SOURCE_WORDS.is_file():
        raise RuntimeError("tracked SENS or Python source fixture is missing")
    words = parse_words(SOURCE_WORDS.read_text(encoding="ascii"))
    physical = encode_words(words)
    if decode_bytes(physical) != words:
        raise RuntimeError("T5 trit carrier failed exact-width word round-trip")

    commands = {
        "sens": [str(sens_cli), "eval"],
        "python": python_command(PYTHON_SOURCE),
    }
    raw_samples: dict[str, list[int]] = {"sens": [], "python": []}
    sample_orders: list[list[str]] = []
    with tempfile.TemporaryDirectory(prefix="sens-trit-source-copy-") as directory:
        program_path = Path(directory) / "d5-label-copy.sens"
        program_path.write_bytes(physical)
        commands["sens"].append(str(program_path))

        opened, _ = invoke([str(sens_cli), "open", str(program_path)], ROOT)
        expected_projection = " ".join(SOURCE_WORDS.read_text(encoding="ascii").split())
        if opened.strip() != expected_projection:
            raise RuntimeError("production SENS open did not preserve exact-width source words")

        initial: dict[str, str] = {}
        for side, command in commands.items():
            initial[side], _ = invoke(command, ROOT)
        if not check_parity(initial["sens"], initial["python"]):
            raise RuntimeError(
                f"PARITY FAIL: sens={initial['sens']!r}; python={initial['python']!r}"
            )
        if initial["sens"] != EXPECTED:
            raise RuntimeError(
                f"ORACLE FAIL: expected {EXPECTED!r}; got {initial['sens']!r}"
            )

        randomizer = random.Random(args.seed)
        total = args.warmups + args.reps
        for trial in range(total):
            order = ["sens", "python"]
            if randomizer.getrandbits(1):
                order.reverse()
            if trial >= args.warmups:
                sample_orders.append(order)
            for side in order:
                observed, elapsed = invoke(commands[side], ROOT)
                if not check_parity(initial[side], observed):
                    raise RuntimeError(
                        f"PARITY DRIFT at trial={trial + 1}/{side}: "
                        f"expected={initial[side]!r}, actual={observed!r}"
                    )
                if trial >= args.warmups:
                    raw_samples[side].append(elapsed)

    sens_bin = sens_cli.read_bytes()
    python_source = PYTHON_SOURCE.read_bytes()
    sens_samples = raw_samples["sens"]
    python_samples = raw_samples["python"]
    return {
        "schema": "sens-trit-source-vs-python-source/v1",
        "status": "research-pilot",
        "claim_scope": (
            "One recursive proper-pair copy workload: current SENS evaluator "
            "reads an actual T5 trit-carrier .sens file; CPython executes the "
            "matching Python source file. End-to-end fresh subprocess time only."
        ),
        "not_claimed": [
            "general language speedup or ranking",
            "pure evaluator time without process startup",
            "trit packing/encoding time",
            "precompiled Python code or saved .pyc comparison",
        ],
        "workload": CASE,
        "sens_source_projection": "examples/binary/d5-label-copy.bits",
        "sens_trit_source_bytes": len(physical),
        "sens_exact_domain_word_count": len(words),
        "sens_trit_source_sha256": checksum(physical),
        "python_source": str(PYTHON_SOURCE.relative_to(ROOT)),
        "python_source_bytes": len(python_source),
        "python_source_sha256": checksum(python_source),
        "sens_output": initial["sens"],
        "python_output": initial["python"],
        "parity": "PASS",
        "samples": args.reps,
        "warmups": args.warmups,
        "order_seed": args.seed,
        "pair_orders": sample_orders,
        "sens_wall_ns": sens_samples,
        "python_wall_ns": python_samples,
        "sens_median_wall_ns": int(statistics.median(sens_samples)),
        "python_median_wall_ns": int(statistics.median(python_samples)),
        "sens_p95_wall_ns": p95(sens_samples),
        "python_p95_wall_ns": p95(python_samples),
        "python_over_sens_median_ratio": statistics.median(python_samples)
        / statistics.median(sens_samples),
        "sens_trit_cli_sha256": checksum(sens_bin),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "cpu": cpu_model(),
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "rustc": subprocess.check_output(
            ["rustc", "--version"], text=True
        ).strip(),
        "timing_boundary": (
            "parent perf_counter_ns around a fresh subprocess; includes interpreter/CLI "
            "startup, source-file read, decode/parse/eval, stdout capture and process exit"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sens-trit", type=Path, default=ROOT / "target/release/sens-trit"
    )
    parser.add_argument("--reps", type=int, default=19)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.reps < 7 or args.warmups < 1:
        parser.error("reps >= 7 and warmups >= 1 required")

    report = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(
        f"{report['workload']}: parity={report['parity']}; "
        f"SENS p50={report['sens_median_wall_ns']} ns, "
        f"Python p50={report['python_median_wall_ns']} ns; "
        f"wrote {args.out}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        raise SystemExit(2)
