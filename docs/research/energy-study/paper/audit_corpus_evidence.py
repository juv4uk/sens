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


def audit(document: object, source_sha: str) -> dict:
    """Classify evidence readiness, without a scientific PASS/FASTER label."""
    if not SHA40.fullmatch(source_sha):
        raise InvalidRaw("--source-sha must be a 40-character lowercase Git SHA")
    if not isinstance(document, dict) or document.get("schema") != "sens-energy-study-raw/v1":
        raise InvalidRaw("unsupported raw schema")
    tasks = document.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise InvalidRaw("raw tasks must be nonempty object")
    results = {}
    for task_id, task in sorted(tasks.items()):
        if not isinstance(task, dict):
            raise InvalidRaw(f"invalid raw task: {task_id}")
        blocked: set[str] = set()
        if task.get("schema") != "sens-paired-physical/v1" or task.get("metric") != "wall_time_ns":
            blocked.add("INCOMPATIBLE_WALL_TIME_SCHEMA")
        provenance = task.get("provenance")
        provenance = provenance if isinstance(provenance, dict) else {}
        sha = provenance.get("git_sha")
        if type(sha) is not str or not SHA40.fullmatch(sha) or sha != source_sha:
            blocked.add("SOURCE_SHA_UNPINNED_OR_MISMATCHED")
        parity = task.get("parity")
        parity = parity if isinstance(parity, dict) else {}
        if parity.get("passed") is not True:
            blocked.add("PARITY_NOT_ASSERTED")
        oracle = parity.get("oracle_id")
        if type(oracle) is not str or not oracle.strip() or "selftest" in oracle.lower():
            blocked.add("PARITY_SELFTEST_IS_NOT_MEASURED_OUTPUT_PROOF")
        if (parity.get("mode") != "external_run"
                or not isinstance(parity.get("input_sha256"), str)
                or not SHA256.fullmatch(parity["input_sha256"])):
            blocked.add("MEASURED_INPUT_NOT_PINNED")
        output_sha = parity.get("reference_output_sha256")
        if type(output_sha) is not str or not SHA256.fullmatch(output_sha):
            blocked.add("REFERENCE_OUTPUT_NOT_PINNED")
        pairs = task.get("pairs")
        if not isinstance(pairs, list) or not pairs:
            blocked.add("PAIRS_MISSING")
            pairs = []
        groups: dict[str, list[dict]] = defaultdict(list)
        process_sessions: dict[str, str] = {}
        sessions: dict[str, set[str]] = defaultdict(set)
        dates: set[str] = set()
        for i, pair in enumerate(pairs):
            if not isinstance(pair, dict):
                blocked.add("MALFORMED_PAIR")
                continue
            process = pair.get("process_id")
            session = pair.get("session_id")
            order = pair.get("order")
            if not isinstance(process, str) or not process or not isinstance(session, str) or not session:
                blocked.add("PROCESS_OR_SESSION_ID_MISSING")
            else:
                if process in process_sessions and process_sessions[process] != session:
                    blocked.add("PROCESS_REUSED_ACROSS_SESSIONS")
                process_sessions[process] = session
                groups[process].append(pair)
                sessions[session].add(process)
            if order not in ("AB", "BA"):
                blocked.add("ORDER_INVALID")
            if not _valid_ns(pair.get("baseline_ns")) or not _valid_ns(pair.get("candidate_ns")):
                blocked.add("WALL_TIME_INVALID")
            started = pair.get("session_started_utc")
            if not isinstance(started, str):
                blocked.add("SESSION_TIMESTAMP_MISSING")
            else:
                try:
                    stamp = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    if not started.endswith("Z") or stamp.utcoffset().total_seconds() != 0:
                        raise ValueError("not UTC Z")
                    dates.add(stamp.date().isoformat())
                except (ValueError, AttributeError):
                    blocked.add("SESSION_TIMESTAMP_INVALID")
            base = pair.get("baseline_output")
            cand = pair.get("candidate_output")
            if type(base) is not str or type(cand) is not str:
                blocked.add("MEASURED_OUTPUTS_MISSING")
            elif base != cand or (type(output_sha) is str and SHA256.fullmatch(output_sha)
                                  and hashlib.sha256(base.encode("utf-8")).hexdigest() != output_sha):
                blocked.add("MEASURED_OUTPUT_PARITY_MISMATCH")
            if pair.get("energy_not_measured") is not True or any(
                name in pair for name in ("energy_uj", "baseline_energy_uj", "candidate_energy_uj")
            ):
                blocked.add("ENERGY_SCOPE_UNVERIFIED")
        if len(groups) < 8 or len(pairs) < 32:
            blocked.add("INSUFFICIENT_PROCESS_BLOCKS")
        if len(sessions) < 4 or len(dates) < 2:
            blocked.add("INSUFFICIENT_INDEPENDENT_SESSION_EVIDENCE")
        for grouped in groups.values():
            counts = {order: sum(p.get("order") == order for p in grouped) for order in ("AB", "BA")}
            if len(grouped) < 4 or counts["AB"] != counts["BA"]:
                blocked.add("UNBALANCED_PROCESS_PAIRS")
        results[task_id] = {
            "status": "BLOCKED" if blocked else "STRUCTURE_ONLY",
            "blockers": sorted(blocked),
            "recorded_processes": len(groups),
            "recorded_sessions": len(sessions),
            "recorded_pairs": len(pairs),
            "energy": "ENERGY_NOT_MEASURED" if "ENERGY_SCOPE_UNVERIFIED" not in blocked else "UNVERIFIED",
            "independent_reproduction": "NOT_REPRODUCED",
        }
    status = "BLOCKED" if any(r["status"] == "BLOCKED" for r in results.values()) else "STRUCTURE_ONLY"
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
