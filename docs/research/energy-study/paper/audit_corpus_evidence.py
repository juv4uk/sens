#!/usr/bin/env python3
"""Research-only fail-closed admission audit of ENERGY-02 paired raw data.

Never a benchmark, SENS semantic oracle, confidence-interval estimator, or
energy meter. Even STRUCTURE_ONLY is not evidence of actual execution,
independence, energy measurement, reproduction or a language ranking.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class InvalidRaw(ValueError):
    pass


def strict_json(source: str) -> object:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        out = {}
        for key, value in pairs:
            if key in out:
                raise InvalidRaw(f"duplicate JSON field: {key}")
            out[key] = value
        return out

    def nonfinite(value: str) -> None:
        raise InvalidRaw(f"nonfinite JSON number: {value}")

    return json.loads(source, object_pairs_hook=unique, parse_constant=nonfinite)


def _valid_ns(value: object) -> bool:
    if type(value) not in (int, float) or value <= 0:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _check_reference(parity: object, blocked: set[str]) -> str | None:
    if not isinstance(parity, dict):
        parity = {}
    if parity.get("passed") is not True:
        blocked.add("PARITY_NOT_ASSERTED")
    oracle = parity.get("oracle_id")
    if type(oracle) is not str or not oracle.strip() or "selftest" in oracle.lower():
        blocked.add("PARITY_SELFTEST_IS_NOT_MEASURED_OUTPUT_PROOF")
    input_sha = parity.get("input_sha256")
    if parity.get("mode") != "external_run" or type(input_sha) is not str or not SHA256.fullmatch(input_sha):
        blocked.add("MEASURED_INPUT_NOT_PINNED")
    output_sha = parity.get("reference_output_sha256")
    if type(output_sha) is not str or not SHA256.fullmatch(output_sha):
        blocked.add("REFERENCE_OUTPUT_NOT_PINNED")
        return None
    return output_sha


def _check_timestamp(pair: dict, dates: set[str], blocked: set[str]) -> None:
    started = pair.get("session_started_utc")
    if not isinstance(started, str):
        blocked.add("SESSION_TIMESTAMP_MISSING")
        return
    try:
        stamp = datetime.fromisoformat(started.replace("Z", "+00:00"))
        if not started.endswith("Z") or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("not UTC Z")
    except (ValueError, AttributeError):
        blocked.add("SESSION_TIMESTAMP_INVALID")
        return
    dates.add(stamp.date().isoformat())


def _check_observation(pair: dict, output_sha: str | None, blocked: set[str]) -> None:
    if pair.get("order") not in ("AB", "BA"):
        blocked.add("ORDER_INVALID")
    if not _valid_ns(pair.get("baseline_ns")) or not _valid_ns(pair.get("candidate_ns")):
        blocked.add("WALL_TIME_INVALID")
    base, candidate = pair.get("baseline_output"), pair.get("candidate_output")
    if type(base) is not str or type(candidate) is not str:
        blocked.add("MEASURED_OUTPUTS_MISSING")
    elif base != candidate or (output_sha is not None
                               and hashlib.sha256(base.encode("utf-8")).hexdigest() != output_sha):
        blocked.add("MEASURED_OUTPUT_PARITY_MISMATCH")
    if pair.get("energy_not_measured") is not True or any(
        field in pair for field in ("energy_uj", "baseline_energy_uj", "candidate_energy_uj")
    ):
        blocked.add("ENERGY_SCOPE_UNVERIFIED")


def _check_pairs(pairs: list, output_sha: str | None, blocked: set[str]) -> tuple[int, int]:
    groups: dict[str, list[dict]] = defaultdict(list)
    process_sessions: dict[str, str] = {}
    sessions: dict[str, set[str]] = defaultdict(set)
    dates: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            blocked.add("MALFORMED_PAIR")
            continue
        process, session = pair.get("process_id"), pair.get("session_id")
        if not isinstance(process, str) or not process or not isinstance(session, str) or not session:
            blocked.add("PROCESS_OR_SESSION_ID_MISSING")
        else:
            if process in process_sessions and process_sessions[process] != session:
                blocked.add("PROCESS_REUSED_ACROSS_SESSIONS")
            process_sessions[process] = session
            groups[process].append(pair)
            sessions[session].add(process)
        _check_timestamp(pair, dates, blocked)
        _check_observation(pair, output_sha, blocked)
    if len(groups) < 8 or len(pairs) < 32:
        blocked.add("INSUFFICIENT_PROCESS_BLOCKS")
    if len(sessions) < 4 or len(dates) < 2:
        blocked.add("INSUFFICIENT_INDEPENDENT_SESSION_EVIDENCE")
    for group in groups.values():
        counts = {order: sum(p.get("order") == order for p in group) for order in ("AB", "BA")}
        if len(group) < 4 or counts["AB"] != counts["BA"]:
            blocked.add("UNBALANCED_PROCESS_PAIRS")
    return len(groups), len(sessions)


def _audit_task(task: object, source_sha: str) -> dict:
    if not isinstance(task, dict):
        raise InvalidRaw("task must be object")
    blocked: set[str] = set()
    if task.get("schema") != "sens-paired-physical/v1" or task.get("metric") != "wall_time_ns":
        blocked.add("INCOMPATIBLE_WALL_TIME_SCHEMA")
    provenance = task.get("provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    sha = provenance.get("git_sha")
    if type(sha) is not str or not SHA40.fullmatch(sha) or sha != source_sha:
        blocked.add("SOURCE_SHA_UNPINNED_OR_MISMATCHED")
    output_sha = _check_reference(task.get("parity"), blocked)
    pairs = task.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        blocked.add("PAIRS_MISSING")
        pairs = []
    process_count, session_count = _check_pairs(pairs, output_sha, blocked)
    return {
        "status": "BLOCKED" if blocked else "STRUCTURE_ONLY",
        "blockers": sorted(blocked),
        "recorded_processes": process_count,
        "recorded_sessions": session_count,
        "recorded_pairs": len(pairs),
        "energy": "ENERGY_NOT_MEASURED" if "ENERGY_SCOPE_UNVERIFIED" not in blocked else "UNVERIFIED",
        "independent_reproduction": "NOT_REPRODUCED",
    }


def audit(document: object, source_sha: str) -> dict:
    """Structural evidence only; never declare a language winner."""
    if not SHA40.fullmatch(source_sha):
        raise InvalidRaw("--source-sha must be a 40-character lowercase Git SHA")
    if not isinstance(document, dict) or document.get("schema") != "sens-energy-study-raw/v1":
        raise InvalidRaw("unsupported raw schema")
    tasks = document.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise InvalidRaw("raw tasks must be nonempty object")
    results = {task_id: _audit_task(task, source_sha) for task_id, task in sorted(tasks.items())}
    status = "BLOCKED" if any(item["status"] == "BLOCKED" for item in results.values()) else "STRUCTURE_ONLY"
    return {
        "status": status, "source_sha_claim": source_sha, "tasks": results,
        "scientific_conclusion": "NONE", "physical_energy": "NOT_VERIFIED",
        "independent_reproduction": "NOT_REPRODUCED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--source-sha", required=True, help="expected exact source Git SHA")
    args = parser.parse_args(argv)
    try:
        result = audit(strict_json(args.raw.read_text(encoding="utf-8")), args.source_sha)
    except (InvalidRaw, UnicodeError, OSError, json.JSONDecodeError) as error:
        print(f"EVIDENCE_BLOCKED reason={error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
