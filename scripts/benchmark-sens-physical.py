#!/usr/bin/env python3
"""Measured physical T5 vs exact-width spaced-bit view; no semantic claims.

Measures complete decode+encode round trips for each representation using the
same CPython process and the same pinned real .sens fixture, after byte parity.
The human .lisp file is counted in bytes, never assigned an execution result.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, typed_sha256
from sens_t5_spaced_view import canonical_view, parse_view

DEFAULT_FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
    "tests/fixtures/migration-d1-cond-cohort/branch.sens",
)
SCHEMA = "sens-physical-t5-measurement/v1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def loop_roundtrip(kind: str, physical: bytes, view: bytes, expected: list[str],
                   iterations: int) -> None:
    last: list[str] | None = None
    if kind == "t5":
        for _ in range(iterations):
            last = decode_bytes(physical)
            encoded = encode_words(last)
        if encoded != physical or last != expected:
            raise RuntimeError("physical T5 roundtrip changed bits")
    elif kind == "view":
        for _ in range(iterations):
            last = parse_view(view)
            encoded = canonical_view(last)
        if encoded != view or last != expected:
            raise RuntimeError("visible exact-width roundtrip changed bits")
    else:
        raise ValueError(f"unknown representation {kind}")


def measure(physical: bytes, view: bytes, expected: list[str],
            reps: int, iterations: int) -> dict[str, object]:
    samples: dict[str, list[float]] = {"t5": [], "view": []}
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        for kind in ("t5", "view"):
            loop_roundtrip(kind, physical, view, expected, min(250, iterations))
        # AB/BA to reduce (not eliminate) heating/order effects.
        for rep in range(reps):
            order = ("t5", "view") if rep % 2 == 0 else ("view", "t5")
            for kind in order:
                started = time.perf_counter_ns()
                loop_roundtrip(kind, physical, view, expected, iterations)
                elapsed_ns = time.perf_counter_ns() - started
                samples[kind].append(elapsed_ns / iterations)
    finally:
        if was_enabled:
            gc.enable()

    median_t5 = statistics.median(samples["t5"])
    median_view = statistics.median(samples["view"])
    return {
        "unit": "ns_per_decode_encode_roundtrip",
        "iterations_per_rep": iterations,
        "repetitions": reps,
        "t5_samples": samples["t5"],
        "view_samples": samples["view"],
        "t5_median_ns": median_t5,
        "view_median_ns": median_view,
        "t5_over_view_time_ratio": median_t5 / median_view,
    }


def inspect_fixture(relative: str, reps: int, iterations: int) -> dict[str, object]:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".sens":
        raise ValueError(f"unsafe fixture path: {relative}")
    path = ROOT / rel
    uk_path = path.with_suffix(".lisp")
    bit_path = path.with_suffix("")
    physical = path.read_bytes()
    original = uk_path.read_bytes()
    view = bit_path.read_bytes()
    decoded = decode_bytes(physical)
    if encode_words(decoded) != physical:
        raise ValueError(f"{relative}: noncanonical physical bytes")
    if parse_view(view) != decoded or canonical_view(decoded) != view:
        raise ValueError(f"{relative}: noncanonical or stale bit view")
    if not original:
        raise ValueError(f"{relative}: empty paired Lisp source")
    measured = measure(physical, view, decoded, reps, iterations)
    return {
        "fixture": relative,
        "status": "PASS_TRANSPORT_ONLY",
        "word_count": len(decoded),
        "semantic_bit_count": sum(map(len, decoded)),
        "physical_bytes": len(physical),
        "view_bytes": len(view),
        "lisp_bytes": len(original),
        "view_over_physical_size_ratio": len(view) / len(physical),
        "lisp_over_physical_size_ratio": len(original) / len(physical),
        "physical_sha256": sha(physical),
        "view_sha256": sha(view),
        "lisp_sha256": sha(original),
        "typed_word_sha256": typed_sha256(decoded),
        "timings": measured,
        "semantic_oracle_parity": "NOT_MEASURED",
        "native_execution": "NOT_MEASURED",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--reps", type=int, default=7)
    ap.add_argument("--iterations", type=int, default=10000)
    ap.add_argument("--fixture", action="append", dest="fixtures")
    args = ap.parse_args()
    if args.reps < 3 or args.iterations < 10:
        ap.error("--reps >= 3 and --iterations >= 10 required")
    fixtures = args.fixtures or DEFAULT_FIXTURES
    if len(set(fixtures)) != len(fixtures):
        ap.error("duplicate fixture path")

    git_sha = os.getenv("GITHUB_SHA") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    cases = [inspect_fixture(fixture, args.reps, args.iterations)
             for fixture in fixtures]
    report = {
        "schema": SCHEMA,
        "git_sha": git_sha,
        "cpu": cpu_model(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "timer": "time.perf_counter_ns; median of paired alternating repetitions",
        "lane": "CPython transport-mechanism-only; not SENS execution vs Python",
        "fixtures": cases,
        "all_transport_preflights_passed": True,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "physical-t5.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Physical SENS — measured T5 vs spaced-bit transport",
        "",
        f"Commit: {git_sha}; CPU: {report['cpu']}; Python: {report['python']}",
        "",
        "| Fixture | Words | Lisp bytes | T5 bytes | Bit-view bytes | "
        "View/T5 size | T5 ns/op | Bit-view ns/op | T5/View time |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in cases:
        metrics = row["timings"]
        lines.append(
            f"| {Path(row['fixture']).stem} | {row['word_count']} "
            f"| {row['lisp_bytes']} | {row['physical_bytes']} | {row['view_bytes']} "
            f"| {row['view_over_physical_size_ratio']:.2f}x "
            f"| {metrics['t5_median_ns']:.1f} "
            f"| {metrics['view_median_ns']:.1f} "
            f"| {metrics['t5_over_view_time_ratio']:.2f}x |"
        )
    lines.extend([
        "",
        "Measurement: CPython decode+encode round trip for real physical T5 "
        "versus canonical ASCII bit-word view; warm-up; alternating order; "
        "median of independent repetitions; widths, bytes and SHA-256 pinned.",
        "",
        "**NOT an execution benchmark. NOT a semantic oracle. "
        "Timing ratios do not compare Rust/SENS runtime with Python.**",
        "",
    ])
    (args.out_dir / "physical-t5.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
