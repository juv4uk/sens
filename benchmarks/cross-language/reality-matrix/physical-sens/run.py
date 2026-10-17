#!/usr/bin/env python3
"""Paired physical-.sens D1-D3 pilot: native SENS versus Python µCPU.

This is an implementation-specific research comparison, not a language
ranking. Both engines receive the same tracked T5 bytes and must agree on
positive and one-bit-negative SENS-owned self-tests before timing starts.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "benchmarks/microcpu"))
from bench import bench, cpu  # noqa: E402
from slot_cpu import compile_t5, run as run_microcpu, visible  # noqa: E402


@dataclass(frozen=True)
class PhysicalInput:
    path: Path
    data: bytes
    sha256: str
    expected: str = ""


def load_physical(path: Path) -> PhysicalInput:
    """Load only a repository-tracked physical .sens file, never a projection."""
    resolved = path.resolve(strict=True)
    if resolved.suffix != ".sens":
        raise ValueError(f"physical input must end in .sens: {path}")
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"physical input must be inside repository: {path}") from exc
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative.as_posix()],
        cwd=ROOT, text=True, capture_output=True, check=False, timeout=10,
    )
    if tracked.returncode:
        raise ValueError(f"physical input must be git-tracked: {relative}")
    data = resolved.read_bytes()
    if not data:
        raise ValueError(f"physical input is empty: {relative}")
    return PhysicalInput(resolved, data, hashlib.sha256(data).hexdigest())


def run_checked(command: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False,
        timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command!r}\n{result.stderr.strip()}"
        )
    return result


def binary_sha(path: Path) -> str:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"expected executable file: {path}")
    return hashlib.sha256(resolved.read_bytes()).hexdigest()


def native_value(cli: Path, item: PhysicalInput) -> str:
    result = run_checked([str(cli.resolve(strict=True)), str(item.path)], timeout=30)
    return result.stdout.strip()


def probe_phases(probe: Path, item: PhysicalInput, *, warmup: int,
                 samples: int, loops: int) -> dict:
    result = run_checked([
        str(probe.resolve(strict=True)), str(item.path), str(warmup),
        str(samples), str(loops),
    ], timeout=120)
    meta: dict[str, str] = {}
    phases: dict[str, list[int]] = {}
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if fields[0] == "PROBE":
            meta["version"] = fields[1]
        elif fields[0] in {"ORACLE_HEX", "WORDS", "T5_BYTES"}:
            meta[fields[0].lower()] = fields[1]
        elif fields[0] == "SAMPLE":
            if len(fields) != 5:
                raise ValueError(f"malformed SENS probe sample: {line!r}")
            _, phase, sample, inner, elapsed = fields
            phases.setdefault(phase, []).append(int(elapsed) // int(inner))
    expected_hex = item.expected.encode("utf-8").hex()
    if meta.get("oracle_hex") != expected_hex:
        raise ValueError(
            f"native timing probe verdict mismatch for {item.path}: "
            f"expected hex {expected_hex}, got {meta.get('oracle_hex')}"
        )
    if int(meta.get("t5_bytes", "-1")) != len(item.data):
        raise ValueError(f"native probe byte count mismatch for {item.path}")
    if any(len(values) != samples for values in phases.values()):
        raise ValueError(f"native probe sample count mismatch for {item.path}")
    if "full_in_memory" not in phases or "eval_hot" not in phases:
        raise ValueError(f"native probe omitted required phases for {item.path}")
    return {"metadata": meta, "raw_ns_per_operation": phases}


def git_sha() -> str:
    return run_checked(["git", "rev-parse", "HEAD"], timeout=10).stdout.strip()


def contract_version() -> str:
    source = ROOT / "language-contract.lisp"
    match = re.search(r"Contract\s+(\d+\.\d+)", source.read_text(encoding="utf-8"))
    return match.group(1) if match else "unknown"


def p50(values: list[int]) -> int:
    import statistics
    return int(statistics.median(values))


def p95(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[(95 * len(ordered) + 99) // 100 - 1]


def summarize(values: list[int]) -> dict:
    return {"p50": p50(values), "p95": p95(values), "samples": len(values),
            "raw_ns_per_operation": values}


def run(args: argparse.Namespace) -> dict:
    cli = args.sens_cli.resolve(strict=True)
    probe = args.phase_probe.resolve(strict=True)
    workloads = [
        ("d3-selftest-positive", args.positive, "1"),
        ("d3-selftest-negative-one-bit", args.negative, "0"),
    ]
    loaded = [(name, load_physical(path), expected) for name, path, expected in workloads]
    if loaded[0][1].sha256 == loaded[1][1].sha256:
        raise ValueError("positive and negative inputs must be distinct physical bytes")

    # Correctness gate for the complete positive/negative pair precedes timing.
    parity = {}
    for name, item, expected in loaded:
        item = PhysicalInput(item.path, item.data, item.sha256, expected)
        tape = compile_t5(item.data)
        py_result = visible(run_microcpu(tape))
        native_result = native_value(cli, item)
        if py_result != expected or native_result != expected:
            raise ValueError(
                f"parity failed for {item.path}: expected={expected!r}, "
                f"native={native_result!r}, microcpu={py_result!r}"
            )
        parity[name] = {
            "expected": expected, "native_sens": native_result,
            "python_microcpu": py_result, "equal": native_result == py_result,
        }

    cases = {}
    for name, item, expected in loaded:
        item = PhysicalInput(item.path, item.data, item.sha256, expected)
        native = probe_phases(probe, item, warmup=args.warmup,
                              samples=args.samples, loops=args.loops)
        microcpu = bench(item.data, samples=args.samples, loops=args.loops,
                         warmup=args.warmup)
        if microcpu["result"] != expected:
            raise ValueError(f"microCPU verdict changed during timing: {item.path}")
        cases[name] = {
            "path": item.path.relative_to(ROOT).as_posix(),
            "physical_bytes": len(item.data), "physical_sha256": item.sha256,
            "expected_result": expected, "parity": parity[name],
            "word_count": microcpu["exact_word_count"],
            "microcpu_slot_count": microcpu["compiled_slot_count"],
            "native_sens": {
                "probe_metadata": native["metadata"],
                "full_decode_parse_execute": summarize(
                    native["raw_ns_per_operation"]["full_in_memory"]),
                "warm_eval_hot": summarize(native["raw_ns_per_operation"]["eval_hot"]),
            },
            "python_microcpu": {
                "full_decode_compile_execute": microcpu["timings_ns_per_operation"]["physical_compile_execute"],
                "warm_compiled_slot_replay": microcpu["timings_ns_per_operation"]["compiled_slot_replay"],
            },
        }
    return {
        "schema": "sens-physical-d3-native-vs-microcpu-pilot/v1",
        "repository_head": git_sha(), "contract_version": contract_version(),
        "cpu": cpu(), "platform": platform.platform(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "rustc": run_checked(["rustc", "--version"], timeout=10).stdout.strip(),
        "zig_version_pin": (ROOT / ".zig-version").read_text(encoding="utf-8").strip(),
        "sens_cli_sha256": binary_sha(cli), "phase_probe_sha256": binary_sha(probe),
        "samples_per_process": args.samples, "loops_per_sample": args.loops,
        "warmup_samples": args.warmup,
        "process_replications": 1,
        "methodology": (
            "Same tracked physical T5 bytes; positive and one-D1-bit negative parity "
            "for both engines is checked before any timing. Native SENS full phase is "
            "decode+parse+fresh-session+execute; warm is eval over parsed forms in a "
            "reused Session. Python full phase is decode+compile+execute; warm is "
            "replay of precompiled slots. Different implementations/representations; "
            "exploratory implementation-specific D1-D3 pilot, not a language ranking."
        ),
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens-cli", required=True, type=Path)
    parser.add_argument("--phase-probe", required=True, type=Path)
    parser.add_argument("--positive", type=Path,
                        default=ROOT / "tests/fixtures/semantic/d3-selftest.sens")
    parser.add_argument("--negative", type=Path,
                        default=ROOT / "tests/fixtures/semantic/d3-selftest-negative.sens")
    parser.add_argument("--samples", type=int, default=11)
    parser.add_argument("--loops", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.samples < 7 or args.loops < 1 or args.warmup < 0:
        parser.error("samples >= 7, loops >= 1, warmup >= 0 required")
    report = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"wrote {args.out}: {len(report['cases'])} physical workloads, parity PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
