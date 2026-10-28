#!/usr/bin/env python3
"""Fail-closed hierarchical paired A/B wall-time verdict (Kalibera–Jones-inspired).

An experimental session is the outer resampling unit, with nested processes
and AB/BA pairs. A restarted process within one shared session is NOT an
independent session. This is NOT the exact Kalibera–Jones estimator.
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
PHYSICAL_SCHEMA = "sens-paired-physical/v1"
PHYSICAL_METRICS = {
    "wall_time_ns": ("baseline_ns", "candidate_ns"),
    "energy_uj": ("baseline_energy_uj", "candidate_energy_uj"),
    "peak_rss_kib": ("baseline_peak_rss_kib", "candidate_peak_rss_kib"),
}
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
    if not isinstance(document, dict) or document.get("schema") not in (SCHEMA, PHYSICAL_SCHEMA):
        raise InvalidEvidence(f"schema must be {SCHEMA} or {PHYSICAL_SCHEMA}")
    if not (0 <= min_effect < 1) or draws < 1000:
        raise InvalidEvidence("minimum effect must be [0,1); draws >= 1000")
    metric = document.get("metric")
    if metric not in PHYSICAL_METRICS or (document["schema"] == SCHEMA and metric != "wall_time_ns"):
        raise InvalidEvidence("metric must be a supported physical metric for this schema")
    baseline_key, candidate_key = PHYSICAL_METRICS[metric]
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
    # Each GitHub-hosted run is normally one experimental session.  Multiple
    # child processes in that session are correlated; using them as independent
    # bootstrap top-level units creates pseudoreplication.
    legacy_groups: dict[str, list[float]] = defaultdict(list)
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    order_counts: dict[tuple[str, str], set[str]] = defaultdict(set)
    machines: set[str] = set()
    missing_session_or_machine = False
    for n, item in enumerate(pairs):
        if not isinstance(item, dict) or not isinstance(item.get("process_id"), str) or not item["process_id"].strip():
            raise InvalidEvidence(f"pairs[{n}]: process_id required")
        order = item.get("order")
        if order not in ("AB", "BA"):
            raise InvalidEvidence(f"pairs[{n}]: order must be AB or BA")
        a = _finite_positive(item.get(baseline_key), f"pairs[{n}].{baseline_key}")
        b = _finite_positive(item.get(candidate_key), f"pairs[{n}].{candidate_key}")
        legacy_groups[item["process_id"]].append(math.log(b / a))
        session = item.get("session_id")
        machine = item.get("machine_id")
        if not isinstance(session, str) or not session.strip() or not isinstance(machine, str) or not machine.strip():
            missing_session_or_machine = True
            continue
        machines.add(machine)
        key = (session, item["process_id"])
        groups[key].append(math.log(b / a))
        order_counts[key].add(order)

    count = len(groups)
    sessions: dict[str, list[list[float]]] = defaultdict(list)
    for (session_id, _process_id), samples in groups.items():
        sessions[session_id].append(samples)
    session_count = len(sessions)
    base_counts = {"independent_sessions": session_count,
                   "independent_processes": count, "pairs": len(pairs)}
    if missing_session_or_machine:
        # Backward-compatible descriptive ratio for legacy pilot files.  This
        # value has NO confidence interval, significance or language ranking:
        # session independence cannot be reconstructed from process IDs.
        descriptive_ratio = (math.exp(statistics.mean(
            statistics.mean(group) for group in legacy_groups.values()))
            if legacy_groups else None)
        return {"schema": OUTPUT_SCHEMA, "status": "INCONCLUSIVE",
                "reason": "SESSION_OR_MACHINE_ID_NOT_RECORDED",
                "metric": metric,
                "independent_processes": len(legacy_groups),
                "independent_sessions": session_count,
                "pairs": len(pairs), "ratio": descriptive_ratio,
                "ci95_ratio": None,
                "ratio_scope": "LEGACY_DESCRIPTIVE_ONLY_NO_SESSION_INFERENCE"}
    if len(machines) != 1:
        return {"schema": OUTPUT_SCHEMA, "status": "INCONCLUSIVE",
                "reason": "UNSTRATIFIED_MULTIPLE_MACHINES",
                **base_counts, "ratio": None, "ci95_ratio": None}

    adequate = (count >= MIN_PROCESSES and
                all(len(x) >= MIN_PAIRS_EACH for x in groups.values()) and
                all(order_counts[key] == {"AB", "BA"} for key in groups))
    if not adequate:
        return {"schema": OUTPUT_SCHEMA, "status": "INCONCLUSIVE",
                "reason": "INSUFFICIENT_INDEPENDENT_PAIRED_SAMPLES_OR_ORDER_BALANCE",
                **base_counts, "ratio": None, "ci95_ratio": None}
    # The prospective protocol (§D) requires at least four real sessions.
    # A session label is only recorded evidence, not proof of independent
    # physical hosts/days or of a frozen preregistration.
    if session_count < 4:
        return {"schema": OUTPUT_SCHEMA, "status": "INCONCLUSIVE",
                "reason": "INSUFFICIENT_INDEPENDENT_SESSIONS",
                **base_counts, "ratio": None, "ci95_ratio": None}

    session_samples = list(sessions.values())
    point_log_ratio = statistics.mean(
        statistics.mean(statistics.mean(process) for process in session)
        for session in session_samples
    )
    rng = random.Random(seed)
    replicates = []
    for _ in range(draws):
        # Three-level hierarchical bootstrap: sessions -> processes -> pairs.
        # Samples within the same session are never treated as top-level
        # independent replicates. Each actual session has equal weight.
        selected_sessions = [session_samples[rng.randrange(session_count)]
                             for _ in range(session_count)]
        session_means = []
        for session in selected_sessions:
            chosen_processes = [session[rng.randrange(len(session))]
                                for _ in range(len(session))]
            process_means = [
                statistics.mean(process[rng.randrange(len(process))]
                                for _ in process)
                for process in chosen_processes
            ]
            session_means.append(statistics.mean(process_means))
        replicates.append(statistics.mean(session_means))
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
        "method": "session-process-pair-hierarchical-log-ratio-bootstrap; exploratory; not exact KJ estimator",
        "metric": metric,
        "ratio": math.exp(point_log_ratio),
        "ci95_ratio": [low_ratio, high_ratio],
        "relative_change": math.exp(point_log_ratio) - 1,
        "minimum_practical_effect": min_effect,
        **base_counts,
        "bootstrap_draws": draws, "seed": seed,
        "git_sha": provenance["git_sha"],
        "warning": ("EXPLORATORY only: session labels alone do not prove "
                    "independent days/hosts, pre-registration, or null-test validity"),
    }


LEVELS = ("machine", "session", "block", "pair")


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm–Bonferroni step-down. Correction is chosen in advance, never per result.

    WHY: comparing several metrics or several languages multiplies the chance of a
    spurious 'FASTER'. Holm controls family-wise error without assuming
    independence between comparisons (unlike plain Bonferroni it is uniformly more
    powerful). Order is by ascending p; ties keep input order.
    """
    m = len(p_values)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, (m - rank) * p_values[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def independent_units(document: dict) -> dict:
    """Count recorded units at each hierarchy level, not proof of independence.

    WHY: a restarted process is not automatically an independent block. Neighbouring
    runs share CPU, cache state, frequency and temperature, so pairs that live in
    the same session are correlated. Only the OUTERMOST level that actually varies
    may be resampled.
    """
    pairs = document.get("pairs") or []
    machines = {p.get("machine_id") for p in pairs if isinstance(p, dict)}
    sessions = {p.get("session_id") for p in pairs if isinstance(p, dict)}
    blocks = {p.get("process_id") for p in pairs if isinstance(p, dict)}
    return {
        "machine": len(machines - {None}),
        "session": len(sessions - {None}),
        "block": len(blocks - {None}),
        "pair": len(pairs),
        "note": "resampling unit is session; process/pair observations are nested",
    }


def analyze_many(documents: list[dict], *, draws: int = 4000, seed: int = 5227,
                 min_effect: float = 0.01, family_alpha: float = 0.05) -> dict:
    """Report descriptive paired effects; refuse unsupported family inference.

    Holm-adjusted p-values require *valid* unadjusted p-values from a
    prespecified null distribution that respects paired, hierarchical samples.
    A 95% CI excluding 1.0 is NOT p=0. The previous implementation converted
    each individual CI into p=0/1 and falsely claimed family-wise error
    control. Until a valid null test is implemented and calibrated, return
    INCONCLUSIVE for any family-level FASTER/SLOWER claim, preserving the
    per-comparison effect ratio and confidence interval for inspection.
    """
    if (type(family_alpha) not in (int, float) or
            not 0.0 < family_alpha < 1.0 or
            not math.isfinite(family_alpha)):
        raise InvalidEvidence("family_alpha must be finite and strictly in (0, 1)")
    reports = [analyze(d, draws=draws, seed=seed, min_effect=min_effect)
               for d in documents]
    blocked = next((r for r in reports if r.get("status") == "BLOCKED"), None)
    for report in reports:
        # Individual, unadjusted decisions cannot be promoted into a family
        # verdict. Do not invent adjusted p-values or erase descriptive data.
        report["holm_adjusted_p"] = None
        if report.get("status") in ("FASTER", "SLOWER"):
            report["status"] = "INCONCLUSIVE"
            report["reason"] = "VALID_FAMILY_P_VALUES_UNAVAILABLE"
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "BLOCKED" if blocked is not None else "INCONCLUSIVE",
        "reason": ("MEMBER_BLOCKED: " + str(blocked.get("reason", "UNKNOWN"))
                   if blocked is not None else
                   ("VALID_FAMILY_P_VALUES_UNAVAILABLE" if reports
                    else "NO_COMPARISONS")),
        "family_alpha": family_alpha,
        "comparisons": reports,
        "survivors": 0,
        "family_inference": "NOT_PERFORMED",
        "warning": ("Descriptive per-comparison CIs only. No Holm-adjusted "
                    "inference until calibrated paired/hierarchical p-values "
                    "are implemented and independently validated."),
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
