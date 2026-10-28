#!/usr/bin/env python3
"""Validate the structural lock for the *prospective* SENS energy study.

This is NOT a semantic oracle, hardware validator, a statistical significance
test, proof of a genuine timestamp, or a license to call pilot results
'preregistered'. It rejects internally contradictory research plans.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys

SHA1 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{2,63}")
METRICS = frozenset({"energy_uj", "wall_time_ns", "peak_rss_kib"})
# Predeclared primary contrast slate: every candidate is either eligible or
# explicitly N/A in each of eight tasks BEFORE observations are inspected.
PLANNED_CANDIDATES = frozenset({"C", "Python", "SENS"})
EXPECTED_TASK_IDS = frozenset({
    "T01-symbolic-recursion", "T02-exact-rationals", "T03-parsing-text",
    "T04-sorting", "T05-allocation-gc", "T06-io", "T07-matrices",
    "T08-persistent-structures", "T09-bit-operations",
})
SENSORS = {
    "RAPL_PACKAGE": "WHOLE_PACKAGE",
    "CALIBRATED_WATTMETER": "WHOLE_SYSTEM",
}


class InvalidPlan(ValueError):
    """A manifest cannot be admitted as a complete frozen design."""


def demand(condition: bool, reason: str) -> None:
    if not condition:
        raise InvalidPlan(reason)


def obj(value: object, path: str) -> dict:
    demand(type(value) is dict, f"{path}: expected object")
    return value


def nonempty(value: object, path: str) -> str:
    demand(type(value) is str and bool(value.strip()), f"{path}: missing text")
    return value


def positive_int(value: object, path: str) -> int:
    demand(type(value) is int and value > 0, f"{path}: expected positive integer")
    return value


def sha(value: object, path: str, pattern: re.Pattern) -> str:
    demand(type(value) is str and pattern.fullmatch(value) is not None,
           f"{path}: invalid full hex digest")
    return value


def utc_stamp(value: object, path: str) -> datetime:
    value = nonempty(value, path)
    demand(value.endswith("Z"), f"{path}: UTC timestamp must end in Z")
    try:
        stamp = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise InvalidPlan(f"{path}: invalid timestamp: {exc}") from exc
    demand(stamp.utcoffset() == timezone.utc.utcoffset(stamp),
           f"{path}: must be UTC")
    return stamp


def validate(plan: object) -> dict[str, int]:
    p = obj(plan, "plan")
    demand(p.get("schema") == "sens-energy-prereg-v1", "schema: unsupported")
    demand(p.get("state") == "FROZEN", "state: not FROZEN")
    sha(p.get("protocol_sha"), "protocol_sha", SHA1)
    sha(p.get("analysis_sha"), "analysis_sha", SHA1)
    sha(p.get("variance_pilot_sha"), "variance_pilot_sha", SHA1)

    lock_time = utc_stamp(p.get("locked_at_utc"), "locked_at_utc")
    first_time = utc_stamp(p.get("first_confirmatory_at_utc"), "first_confirmatory_at_utc")
    demand(lock_time < first_time, "timestamps: measurement is not after freeze")
    review = nonempty(p.get("lock_review_url"), "lock_review_url")
    demand(review.startswith("https://github.com/"), "lock_review_url: needs public audit URL")

    nonempty(p.get("host_id"), "host_id")
    nonempty(p.get("host_cpu"), "host_cpu")
    sensor = p.get("energy_sensor")
    demand(type(sensor) is str and sensor in SENSORS,
           "energy_sensor: no valid physical instrument")
    demand(p.get("energy_scope") == SENSORS[sensor],
           "energy_scope: conflicts with physical sensor")
    proof = nonempty(p.get("sensor_proof_url"), "sensor_proof_url")
    demand(proof.startswith("https://"), "sensor_proof_url: needs evidence link")
    max_bytes = positive_int(p.get("max_work_bytes_per_invocation"), "max_work_bytes_per_invocation")
    demand(max_bytes <= 3 * 1024**3, "max_work_bytes_per_invocation: exceeds 3 GiB")

    seed = p.get("random_seed")
    demand(type(seed) is int and 0 <= seed < 2**64, "random_seed: invalid integer")
    demand(positive_int(p.get("sessions"), "sessions") >= 4,
           "sessions: fewer than four independent sessions")
    pairs = positive_int(p.get("pairs_per_session"), "pairs_per_session")
    demand(pairs >= 4 and pairs % 2 == 0, "pairs_per_session: requires >=4 even AB/BA pairs")
    demand(type(p.get("precision_target")) in (int, float)
           and math.isclose(p["precision_target"], 0.10, rel_tol=0, abs_tol=1e-12),
           "precision_target: must be preregistered 0.10")
    demand(type(p.get("alpha")) in (int, float)
           and math.isclose(p["alpha"], 0.05, rel_tol=0, abs_tol=1e-12),
           "alpha: must be preregistered 0.05")
    demand(p.get("multiplicity") == "HOLM_FWER", "multiplicity: must be HOLM_FWER")
    demand(p.get("analysis_state") == "VALIDATED",
           "analysis_state: #6290 must validate the method before locking")

    tasks = p.get("tasks")
    demand(type(tasks) is list and len(tasks) == 9, "tasks: exactly nine frozen tasks required")
    task_impls: dict[str, set[str]] = {}
    task_input: dict[str, str] = {}
    expected_contrasts: set[tuple[str, str]] = set()
    for index, entry in enumerate(tasks):
        t = obj(entry, f"tasks[{index}]")
        tid = t.get("id")
        demand(type(tid) is str and TASK_ID.fullmatch(tid) is not None,
               f"tasks[{index}].id: invalid identifier")
        demand(tid not in task_impls, f"tasks[{index}].id: duplicate {tid}")
        digest = sha(t.get("input_sha256"), f"tasks[{index}].input_sha256", SHA256)
        sha(t.get("reference_output_sha256"),
            f"tasks[{index}].reference_output_sha256", SHA256)
        positive_int(t.get("verified_units"), f"tasks[{index}].verified_units")
        implementations = t.get("implementations")
        demand(type(implementations) is list and len(implementations) >= 2,
               f"tasks[{index}].implementations: Rust and candidate required")
        langs: set[str] = set()
        for impl_index, item in enumerate(implementations):
            entry_impl = obj(item, f"tasks[{index}].implementations[{impl_index}]")
            language = nonempty(entry_impl.get("language"),
                                f"tasks[{index}].implementations[{impl_index}].language")
            demand(language not in langs,
                   f"tasks[{index}].implementations: duplicate language {language}")
            sha(entry_impl.get("source_sha"),
                f"tasks[{index}].implementations[{impl_index}].source_sha", SHA1)
            langs.add(language)
        demand("Rust" in langs, f"tasks[{index}].implementations: no Rust baseline")
        excluded = t.get("ineligible_candidates")
        demand(type(excluded) is list,
               f"tasks[{index}].ineligible_candidates: explicit N/A inventory required")
        ineligible: set[str] = set()
        for excluded_index, item in enumerate(excluded):
            entry_na = obj(item, f"tasks[{index}].ineligible_candidates[{excluded_index}]")
            language = nonempty(entry_na.get("language"), "ineligible language")
            demand(language in PLANNED_CANDIDATES,
                   f"tasks[{index}].ineligible_candidates: unknown primary language {language}")
            demand(language not in langs,
                   f"tasks[{index}].ineligible_candidates: implemented language {language} declared N/A")
            demand(language not in ineligible,
                   f"tasks[{index}].ineligible_candidates: duplicate language {language}")
            reason = nonempty(entry_na.get("reason"),
                              f"tasks[{index}].ineligible_candidates[{excluded_index}].reason")
            demand(len(reason.strip()) >= 20,
                   f"tasks[{index}].ineligible_candidates: N/A needs a substantive reason")
            evidence = nonempty(entry_na.get("evidence_url"),
                                f"tasks[{index}].ineligible_candidates[{excluded_index}].evidence_url")
            demand(evidence.startswith("https://"),
                   f"tasks[{index}].ineligible_candidates: evidence must be HTTPS URL")
            ineligible.add(language)
        eligible = langs & PLANNED_CANDIDATES
        demand(eligible | ineligible == PLANNED_CANDIDATES,
               f"tasks[{index}].ineligible_candidates: missing candidate or explicit N/A")
        expected_contrasts.update((tid, language) for language in eligible)
        task_impls[tid] = langs
        task_input[tid] = digest

    demand(set(task_impls) == EXPECTED_TASK_IDS,
           "tasks: IDs must match the nine published frozen corpus tasks")
    contrasts = p.get("contrasts")
    demand(type(contrasts) is list and len(contrasts) > 0,
           "contrasts: missing comparisons")
    seen: set[tuple[str, str]] = set()
    coverage: set[str] = set()
    for index, item in enumerate(contrasts):
        c = obj(item, f"contrasts[{index}]")
        tid, base, candidate = c.get("task"), c.get("baseline"), c.get("candidate")
        demand(type(tid) is str and tid in task_impls,
               f"contrasts[{index}].task: unknown")
        demand(base == "Rust", f"contrasts[{index}].baseline: must be Rust")
        demand(type(candidate) is str and candidate != "Rust"
               and candidate in task_impls[tid],
               f"contrasts[{index}].candidate: not preregistered for this task")
        demand(c.get("input_sha256") == task_input[tid],
               f"contrasts[{index}]: input digest mismatch (parity BLOCKED)")
        metrics = c.get("metrics")
        demand(type(metrics) is list and len(metrics) == 3
               and all(type(m) is str for m in metrics)
               and set(metrics) == METRICS,
               f"contrasts[{index}].metrics: all three primaries required")
        key = (tid, candidate)
        demand(key not in seen, f"contrasts[{index}]: duplicate {tid}/{candidate}")
        seen.add(key)
        coverage.add(tid)
    demand(seen == expected_contrasts,
           "contrasts: all eligible candidate/task cells must be declared; missing primary contrast")
    # Notice: structural matching is NOT output parity or metrology evidence.
    return {"tasks": len(tasks), "contrasts": len(contrasts),
            "planned_candidate_cells": len(tasks) * len(PLANNED_CANDIDATES),
            "explicit_na_cells": len(tasks) * len(PLANNED_CANDIDATES) - len(seen),
            "sessions": p["sessions"], "pairs_per_session": pairs}


def strict_json(text: str) -> object:
    """Reject ambiguous duplicate keys at every nesting level."""
    def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
        unique = {}
        for key, value in pairs:
            if key in unique:
                raise InvalidPlan(f"JSON duplicate key: {key}")
            unique[key] = value
        return unique

    def invalid_constant(value: str) -> None:
        raise InvalidPlan(f"JSON nonfinite constant: {value}")

    return json.loads(text, object_pairs_hook=no_duplicate_keys,
                      parse_constant=invalid_constant)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="frozen prospective plan JSON")
    args = parser.parse_args()
    try:
        plan = strict_json(args.manifest.read_text(encoding="utf-8"))
        facts = validate(plan)
    except (InvalidPlan, OSError, json.JSONDecodeError) as error:
        print(f"PREREG_BLOCKED reason={error}", file=sys.stderr)
        return 2
    print("PREREG_STRUCTURE_OK " +
          " ".join(f"{key}={value}" for key, value in facts.items()) +
          " proof=STRUCTURE_ONLY physical=NOT_CHECKED semantics=NOT_CHECKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
