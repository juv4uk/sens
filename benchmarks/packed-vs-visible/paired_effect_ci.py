#!/usr/bin/env python3
"""Within-run paired effect sizes and *exploratory* confidence intervals for SENS.

Inputs are the raw JSONL rows produced by the existing packed-vs-visible
release benchmarks. Both candidates must come from the same measured batch,
with byte/AST or evaluated-value parity established BEFORE the timing loop.

The unit of resampling is the *paired batch*, not a single inner iteration.
A percentile pair-bootstrap at one hosted runner/SHA is NOT a Kalibera-Jones
hierarchical confidence interval over independent JVM/process/host runs.
This tool never changes semantic-oracle verdicts or blocks CI on speed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import sys

SCHEMAS = {
    "sens-packed-visible-ingest/v1": ("preflight", "same-D2-domain-AST"),
    "sens-packed-visible-runtime/v1": ("oracle", "same-evaluated-value-output"),
}
OUTPUT_SCHEMA = "sens-within-run-paired-effect/v1"
SHA = re.compile(r"^[0-9a-f]{40}$")


def require_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}: expected numeric elapsed nanoseconds")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{label}: timing must be finite and positive")
    return result


def numeric_samples(row: dict, name: str) -> list[float]:
    raw = row.get(name)
    if not isinstance(raw, list) or len(raw) < 5 or len(raw) % 2 == 0:
        raise ValueError(f"{name}: require an odd count of >=5 paired batches")
    return [require_number(x, f"{name}[{i}]") for i, x in enumerate(raw)]


def percentile(values: list[float], q: float) -> float:
    """Linear interpolation on ordered bootstrap estimates."""
    values = sorted(values)
    position = (len(values) - 1) * q
    low = int(math.floor(position))
    high = int(math.ceil(position))
    return values[low] * (high - position) + values[high] * (position - low) if low != high else values[low]


def analyze(row: dict, *, source_sha: str, seed: int, resamples: int) -> dict:
    schema = row.get("schema")
    if schema not in SCHEMAS:
        raise ValueError(f"unsupported measured schema: {schema!r}")
    oracle_key, oracle_value = SCHEMAS[schema]
    if row.get(oracle_key) != oracle_value:
        raise ValueError("missing pre-timing observable/AST equivalence oracle")
    case, phase = row.get("case"), row.get("phase", "ingest")
    if not isinstance(case, str) or not case or not isinstance(phase, str) or not phase:
        raise ValueError("missing measured case/phase")
    visible = numeric_samples(row, "visible_samples_ns")
    packed = numeric_samples(row, "packed_samples_ns")
    n = len(visible)
    if len(packed) != n or row.get("samples") != n:
        raise ValueError("different batch counts: pairing is not established")

    # Cross-check reported per-batch timing and median so malformed or
    # unrelated raw samples cannot be converted into a speed claim.
    v = statistics.median(visible)
    p = statistics.median(packed)
    for field, observed in (("visible_median_ns", v), ("packed_median_ns", p)):
        reported = require_number(row.get(field), field)
        if not math.isclose(observed, reported, rel_tol=0.0001, abs_tol=0.1):
            raise ValueError(f"{field}: reported median disagrees with raw paired batches")
    reported_ratio = require_number(row.get("ratio_visible_over_packed"), "reported ratio")
    if not math.isclose(v / p, reported_ratio, rel_tol=0.001, abs_tol=0.001):
        raise ValueError("reported ratio disagrees with source samples")

    # Reproducible per-case randomness; insertion/reordering rows cannot
    # silently change the confidence interval for any other case.
    digest = hashlib.sha256(f"{source_sha}|{schema}|{case}|{phase}|{seed}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:16], "big"))
    boot = []
    for _ in range(resamples):
        draws = [rng.randrange(n) for __ in range(n)]
        boot.append(
            statistics.median(visible[i] for i in draws)
            / statistics.median(packed[i] for i in draws)
        )
    lo, hi = percentile(boot, 0.025), percentile(boot, 0.975)
    verdict = "INCONCLUSIVE"
    if lo > 1.0:
        verdict = "PACKED_FASTER_WITHIN_RUN"
    elif hi < 1.0:
        verdict = "VISIBLE_FASTER_WITHIN_RUN"
    return {
        "schema": OUTPUT_SCHEMA,
        "source_schema": schema,
        "source_sha": source_sha,
        "case": case,
        "phase": phase,
        "paired_batches": n,
        "effect": "median(visible_ns)/median(packed_ns)",
        "ratio": v / p,
        "ci95_paired_bootstrap": [lo, hi],
        "verdict": verdict,
        "ci_scope": "exploratory single-run batch bootstrap; NOT independent-run Kalibera-Jones",
        "seed": seed,
        "resamples": resamples,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="raw existing benchmark JSONL")
    parser.add_argument("--source-sha", required=True, help="40-character measured Git SHA")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--resamples", type=int, default=5000)
    args = parser.parse_args(argv)

    if not SHA.fullmatch(args.source_sha):
        parser.error("source-sha must be a full 40-character lowercase hex commit ID")
    if args.resamples < 1000 or args.resamples > 100000:
        parser.error("resamples must be in [1000, 100000]")

    rows = [
        json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError("empty measurement corpus")
    results = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("only JSON object measurements are accepted")
        key = (row.get("schema"), row.get("case"), row.get("phase", "ingest"))
        if key in seen:
            raise ValueError(f"duplicate measured pair: {key}")
        seen.add(key)
        results.append(analyze(row, source_sha=args.source_sha, seed=args.seed, resamples=args.resamples))

    # All checks succeed before writing any report.
    args.out_dir.mkdir(parents=True, exist_ok=True)
    result_file = args.out_dir / "paired-effect.json"
    result_file.write_text(json.dumps({
        "schema": OUTPUT_SCHEMA,
        "source_sha": args.source_sha,
        "results": results,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    table = [
        "# SENS paired performance — exploratory single-run uncertainty",
        "",
        f"Measured source SHA: `{args.source_sha}`. Paired batch bootstrap, seed {args.seed}, {args.resamples} resamples.",
        "",
        "| Case | Phase | Visible / packed | Exploratory 95% interval | Verdict |",
        "|---|---|---:|---:|---|",
    ]
    for result in results:
        lo, hi = result["ci95_paired_bootstrap"]
        table.append(
            f"| {result['case']} | {result['phase']} | {result['ratio']:.3f}× "
            f"| [{lo:.3f}, {hi:.3f}] | {result['verdict']} |"
        )
    table.extend([
        "",
        "Interpretation: ratio >1 means the packed candidate was faster on this corpus.",
        "The paired unit is the recorded batch (one timing for each candidate), not",
        "the inner invocation. Both methods must pass the existing parity oracle.",
        "**This interval is conditional on ONE hosted run; it does not cover independent",
        "machine/process/run variance and is NOT a Kalibera–Jones confidence interval.**",
        "Do not use the interval as a semantic gate, a cross-machine claim, or a",
        "regression failure threshold. Do not compare Cachegrind I refs with nanoseconds.",
        "",
    ])
    (args.out_dir / "paired-effect.md").write_text("\n".join(table), encoding="utf-8")
    print("\n".join(table))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"BLOCKED_NO_STATISTICS: {error}", file=sys.stderr)
        raise SystemExit(2)
