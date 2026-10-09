#!/usr/bin/env python3
"""Fail-closed hierarchical paired A/B wall-time verdict (Kalibera–Jones-inspired).

An independently restarted process is the resampling unit; repetitions inside
one process are not independent observations. This tool is NOT an implementation
of the exact Kalibera–Jones variance-component estimator, nor proof of speedup.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path


SCHEMA = "sens-paired-wall-time/v1"
OUTPUT_SCHEMA = "sens-paired-verdict/v1"
MIN_PROCESSES = 8
MIN_PAIRS_EACH = 4
REQUIRED_PROVENANCE = (
    "git_sha", "binary_sha256", "cpu_model", "rustc", "os",
    "affinity", "governor", "turbo", "timing_source",
)


class InvalidEvidence(ValueError):
    """Input cannot support a performance verdict."""


def _finite_positive(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidEvidence(f"{field}: numeric value required")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise InvalidEvidence(f"{field}: expected finite positive value")
    return number


def _percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent
    low = int(math.floor(index))
    high = int(math.ceil(index))
    return ordered[low] * (high - index) + ordered[high] * (index - low) if low != high else ordered[low]


def analyze(document: dict, *, draws: int = 4000, seed: int = 5227,
            min_effect: float = 0.01) -> dict:
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise InvalidEvidence(f"schema must be {SCHEMA}")
    if not (0 <= min_effect < 1) or draws < 1000:
        raise InvalidEvidence("minimum effect must be [0,1); draws >= 1000")
    if document.get("metric") != "wall_time_ns":
        raise InvalidEvidence("paired verdict only accepts wall_time_ns, not I refs")
    parity = document.get("parity")
    if not isinstance(parity, dict) or parity.get("passed") is not True or not parity.get("oracle_id"):
        return {"schema": OUTPUT_SCHEMA, "status": "BLOCKED",
                "reason": "PARITY_NOT_PROVED", "ratio": None, "ci95_ratio": None}
    provenance = document.get("provenance")
    if not isinstance(provenance, dict):
        raise InvalidEvidence("provenance object required")
    missing = [name for name in REQUIRED_PROVENANCE if not isinstance(provenance.get(name), str) or not provenance[name].strip()]
    if missing:
        return {"schema": OUTPUT_SCHEMA, "status": "BLOCKED",
                "reason": "PROVENANCE_INCOMPLETE:" + ",".join(missing),
                "ratio": None, "ci95_ratio": None}

    pairs = document.get("pairs")
    if not isinstance(pairs, list):
        raise InvalidEvidence("pairs must be a list")
    groups: dict[str, list[float]] = defaultdict(list)
    order_counts: dict[str, set[str]] = defaultdict(set)
    for n, item in enumerate(pairs):
        if not isinstance(item, dict) or not isinstance(item.get("process_id"), str) or not item["process_id"].strip():
            raise InvalidEvidence(f"pairs[{n}]: process_id required")
        order = item.get("order")
        if order not in ("AB", "BA"):
            raise InvalidEvidence(f"pairs[{n}]: order must be AB or BA")
        a = _finite_positive(item.get("baseline_ns"), f"pairs[{n}].baseline_ns")
        b = _finite_positive(item.get("candidate_ns"), f"pairs[{n}].candidate_ns")
        groups[item["process_id"]].append(math.log(b / a))
        order_counts[item["process_id"]].add(order)

    count = len(groups)
    adequate = (count >= MIN_PROCESSES and
                all(len(x) >= MIN_PAIRS_EACH for x in groups.values()) and
                all(order_counts[key] == {"AB", "BA"} for key in groups))
    if not adequate:
        return {"schema": OUTPUT_SCHEMA, "status": "INCONCLUSIVE",
                "reason": "INSUFFICIENT_INDEPENDENT_PAIRED_SAMPLES_OR_ORDER_BALANCE",
                "independent_processes": count, "pairs": len(pairs),
                "ratio": None, "ci95_ratio": None}

    samples = list(groups.values())
    # Equal weight for independent process restarts, not each inner iteration.
    point_log_ratio = statistics.mean(statistics.mean(sample) for sample in samples)
    rng = random.Random(seed)
    replicates = []
    for _ in range(draws):
        chosen = [samples[rng.randrange(count)] for _ in range(count)]
        process_means = [
            statistics.mean(sample[rng.randrange(len(sample))] for _ in sample)
            for sample in chosen
        ]
        replicates.append(statistics.mean(process_means))
    lo, hi = (_percentile(replicates, 0.025), _percentile(replicates, 0.975))
    low_ratio, high_ratio = math.exp(lo), math.exp(hi)
    status = "INCONCLUSIVE"
    if high_ratio < 1.0 - min_effect:
        status = "FASTER"
    elif low_ratio > 1.0 + min_effect:
        status = "SLOWER"
    return {
        "schema": OUTPUT_SCHEMA, "status": status,
        "comparison": "candidate / baseline; lower is better",
        "method": "hierarchical-paired-log-ratio-bootstrap; not exact KJ estimator",
        "metric": "wall_time_ns",
        "ratio": math.exp(point_log_ratio),
        "ci95_ratio": [low_ratio, high_ratio],
        "relative_change": math.exp(point_log_ratio) - 1,
        "minimum_practical_effect": min_effect,
        "independent_processes": count, "pairs": len(pairs),
        "bootstrap_draws": draws, "seed": seed,
        "git_sha": provenance["git_sha"],
        "warning": "Interpret only within matching measured provenance and proved parity",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--draws", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=5227)
    parser.add_argument("--min-effect", type=float, default=0.01)
    args = parser.parse_args()
    try:
        evidence = json.loads(args.input.read_text(encoding="utf-8"))
        report = analyze(evidence, draws=args.draws, seed=args.seed, min_effect=args.min_effect)
    except (InvalidEvidence, OSError, json.JSONDecodeError) as exc:
        report = {"schema": OUTPUT_SCHEMA, "status": "BLOCKED",
                  "reason": str(exc), "ratio": None, "ci95_ratio": None}
    result = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result, encoding="utf-8")
    print(result, end="")
    return 2 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
