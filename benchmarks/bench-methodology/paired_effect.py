#!/usr/bin/env python3
"""SENS paired wall-clock effect-size report with multi-build uncertainty.

Hierarchical paired bootstrap *inspired by* Kalibera-Jones, not the complete
Kalibera-Jones random-effects estimator. No instruction counts accepted.
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

SCHEMA = "sens-paired-wall/v1"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
REQUIRED_ENV = ("cpu_model", "rustc", "profile", "cpu_governor", "turbo_state", "affinity")


class EvidenceError(ValueError):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise EvidenceError(message)


def parse(data: dict) -> list[list[tuple[float, float]]]:
    require(data.get("schema") == SCHEMA, "schema mismatch")
    require(data.get("metric") == "wall_ns", "only wall_ns admitted; no instruction-count conflation")
    require(bool(HEX40.fullmatch(str(data.get("sha", "")))), "exact 40-hex commit SHA required")
    require(bool(HEX64.fullmatch(str(data.get("input_sha256", "")))), "input digest required")
    require(bool(HEX64.fullmatch(str(data.get("output_sha256", "")))), "output-parity digest required")
    builds = data.get("builds")
    require(isinstance(builds, list) and bool(builds), "at least one build required")
    unique_ids = set()
    pinned_env = None
    parsed = []
    for build in builds:
        require(isinstance(build, dict), "invalid build object")
        build_id = build.get("build_id")
        require(isinstance(build_id, str) and build_id and build_id not in unique_ids, "duplicate/missing build_id")
        unique_ids.add(build_id)
        require(bool(HEX64.fullmatch(str(build.get("binary_sha256", "")))), "binary digest required per build")
        env = build.get("environment")
        require(isinstance(env, dict), "environment required")
        for name in REQUIRED_ENV:
            require(isinstance(env.get(name), str) and env[name].strip(), f"missing environment field: {name}")
        # Different runner IDs are allowed, but do not mix CPU or toolchain.
        normalized = tuple(env[name] for name in REQUIRED_ENV)
        if pinned_env is None:
            pinned_env = normalized
        require(pinned_env == normalized, "mixed CPU/toolchain/environment; split the experiment")
        rounds = build.get("rounds")
        require(isinstance(rounds, list) and rounds, "empty build rounds")
        build_rounds = []
        for row in rounds:
            require(isinstance(row, dict), "invalid round")
            order = row.get("order")
            require(order in ("ABBA", "BAAB"), "round must be ABBA or BAAB")
            values = row.get("samples_ns")
            require(isinstance(values, list) and len(values) == 4,
                    "ABBA/BAAB requires four independent timing samples")
            require(all(isinstance(v, (int, float)) and not isinstance(v, bool)
                        and math.isfinite(v) and v > 0 for v in values),
                    "all wall timings must be finite positive nanoseconds")
            digests = row.get("outputs_sha256")
            require(isinstance(digests, list) and len(digests) == 4
                    and all(d == data["output_sha256"] for d in digests),
                    "A/B output parity or witness digest failed")
            a = statistics.mean(v for v, variant in zip(values, order) if variant == "A")
            b = statistics.mean(v for v, variant in zip(values, order) if variant == "B")
            build_rounds.append((a, b))
        parsed.append(build_rounds)
    return parsed


def percentile(values: list[float], fraction: float) -> float:
    sorted_values = sorted(values)
    pos = (len(sorted_values) - 1) * fraction
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def ratio(groups: list[list[tuple[float, float]]]) -> float:
    # Equal weight per independently compiled build, not per pooled round.
    a = statistics.mean(statistics.mean(p[0] for p in block) for block in groups)
    b = statistics.mean(statistics.mean(p[1] for p in block) for block in groups)
    return a / b


def evaluate(data: dict, iterations: int = 4000, seed: int = 20261010) -> dict:
    require(iterations >= 1000, "at least 1000 hierarchical bootstrap draws required")
    groups = parse(data)
    point = ratio(groups)
    rng = random.Random(seed)
    draws = []
    for _ in range(iterations):
        selected = [rng.choice(groups) for _ in groups]
        rerounds = [[rng.choice(block) for _ in block] for block in selected]
        draws.append(ratio(rerounds))
    lo, hi = percentile(draws, 0.025), percentile(draws, 0.975)
    enough_replicates = len(groups) >= 3 and all(len(x) >= 10 for x in groups)
    unknown_env = any(
        str(data["builds"][0]["environment"][key]).lower() in ("unknown", "unset", "uncontrolled")
        for key in ("cpu_governor", "turbo_state", "affinity")
    )
    if not enough_replicates:
        verdict = "UNVERIFIED_MULTIBUILD"
    elif unknown_env:
        verdict = "UNVERIFIED_ENVIRONMENT"
    elif lo > 1:
        verdict = "FASTER_ON_MATCHED_WALL_WORKLOAD"
    elif hi < 1:
        verdict = "SLOWER_ON_MATCHED_WALL_WORKLOAD"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "schema": "sens-paired-wall-verdict/v1",
        "metric": "wall_ns",
        "sha": data["sha"],
        "input_sha256": data["input_sha256"],
        "output_sha256": data["output_sha256"],
        "builds": len(groups),
        "rounds_per_build": [len(x) for x in groups],
        "point_ratio_baseline_over_candidate": round(point, 8),
        "confidence_95_ratio": [round(lo, 8), round(hi, 8)],
        "time_reduction_fraction": round(1 - 1 / point, 8),
        "verdict": verdict,
        "bootstrap_draws": iterations,
        "bootstrap_seed": seed,
        "method": "two-level paired clustered bootstrap; Kalibera-Jones-inspired, NOT full KJ random effects",
        "claim_boundary": "within one matched corpus and CPU/toolchain; not generic SENS throughput or GPU",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--bootstrap", type=int, default=4000)
    args = parser.parse_args()
    try:
        source = args.evidence.read_bytes()
        data = json.loads(source)
        result = evaluate(data, iterations=args.bootstrap)
    except (EvidenceError, OSError, ValueError, TypeError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    result["evidence_sha256"] = hashlib.sha256(source).hexdigest()
    output = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
