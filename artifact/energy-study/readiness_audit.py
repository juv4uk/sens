#!/usr/bin/env python3
"""Read-only preflight of research raw samples; NEVER a replication certificate.

Scope: #6291, existing sens-energy-study-raw/v1 sample files. This does not
convert them into FAIR manifests or infer missing measurements.

Basis: Wilkinson et al. (2016) FAIR, DOI 10.1038/sdata.2016.18;
Kalibera & Jones (2013), DOI 10.1145/2464157.2464160;
Pereira et al. (2017/2021), DOI 10.1145/3136014.3136031 and
10.1016/j.scico.2021.102609; Green Software Foundation SCI,
https://greensoftware.foundation/standards/sci/.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

SCHEMA = "sens-energy-study-raw/v1"
TASK_SCHEMA = "sens-paired-physical/v1"
SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_BYTES = 32 * 1024 * 1024


class InvalidRaw(ValueError):
    """Unreadable or structurally ambiguous research input."""


def _no_duplicate(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise InvalidRaw(f"duplicate JSON key: {name}")
        result[name] = value
    return result


def _no_constant(value):
    raise InvalidRaw(f"nonfinite JSON constant: {value}")


def load_raw(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise InvalidRaw("missing or linked raw file")
    if not 0 < path.stat().st_size <= MAX_BYTES:
        raise InvalidRaw("empty or oversized raw file")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=_no_duplicate,
                         parse_constant=_no_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidRaw(f"unreadable JSON: {path.name}") from exc
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise InvalidRaw("unsupported study raw schema")
    if not isinstance(raw.get("tasks"), dict) or not raw["tasks"]:
        raise InvalidRaw("missing task records")
    return raw


def _positive_number(value):
    return (type(value) in (int, float) and math.isfinite(value)
            and value > 0)


def audit_task(task: object) -> dict:
    issues: set[str] = set()
    if not isinstance(task, dict):
        return {"status": "READINESS_BLOCKED", "issues": ["TASK_NOT_OBJECT"],
                "pairs": 0, "process_ids": 0, "sessions": 0}
    if task.get("schema") != TASK_SCHEMA:
        issues.add("INVALID_PAIRED_SCHEMA")
    if task.get("metric") != "wall_time_ns":
        issues.add("TIME_BOUNDARY_UNSPECIFIED")
    parity = task.get("parity")
    if not isinstance(parity, dict) or parity.get("passed") is not True:
        issues.add("PARITY_NOT_VERIFIED")
    elif "selftest" in str(parity.get("oracle_id", "")).lower():
        issues.add("PARITY_SELFTEST_ONLY")
    provenance = task.get("provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    sha = provenance.get("git_sha")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        issues.add("SOURCE_SHA_NOT_PINNED")
    if not isinstance(provenance.get("cpu_model"), str) or provenance.get("cpu_model") in ("", "x86_64", "aarch64", "unknown"):
        issues.add("CPU_MODEL_UNSPECIFIED")
    if provenance.get("governor") in (None, "", "unknown"):
        issues.add("GOVERNOR_UNSPECIFIED")
    if provenance.get("affinity") in (None, "", "not-pinned", "unknown"):
        issues.add("AFFINITY_UNCONTROLLED")
    pairs = task.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        issues.add("PAIRS_MISSING")
        pairs = []
    processes, sessions, orders = set(), set(), []
    orders_by_session: dict[str, set[str]] = {}
    time_boundaries: set[str] = set()
    for i, record in enumerate(pairs):
        if not isinstance(record, dict):
            issues.add("MALFORMED_PAIR")
            continue
        if not (_positive_number(record.get("baseline_ns"))
                and _positive_number(record.get("candidate_ns"))):
            issues.add("INVALID_ELAPSED_TIME")
        order = record.get("order")
        if order not in ("AB", "BA"):
            issues.add("INVALID_AB_BA_ORDER")
        else:
            orders.append(order)
        for field, storage in (("process_id", processes), ("session_id", sessions)):
            value = record.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.add("MISSING_" + field.upper())
            else:
                storage.add(value)
        session = record.get("session_id")
        if isinstance(session, str) and session.strip() and order in ("AB", "BA"):
            orders_by_session.setdefault(session, set()).add(order)
        boundary = record.get("time_boundary", provenance.get("time_boundary"))
        if not isinstance(boundary, str) or not boundary.strip() or boundary in ("unknown", "unspecified"):
            issues.add("TIME_BOUNDARY_UNSPECIFIED")
        else:
            time_boundaries.add(boundary)
        if not isinstance(record.get("machine_id"), str) or not record["machine_id"].strip():
            issues.add("MISSING_MACHINE_ID")
        # This schema records two process peaks, NOT one generic peak_rss_kib.
        # T04/T05/T06 real study samples use these exact two keys.
        if not (_positive_number(record.get("baseline_peak_rss_kib"))
                and _positive_number(record.get("candidate_peak_rss_kib"))):
            issues.add("PEAK_RSS_NOT_RECORDED")
        if record.get("energy_not_measured") is not True:
            issues.add("ENERGY_MEASUREMENT_NOT_VERIFIED")
        if record.get("energy_uj") is not None:
            issues.add("ENERGY_CONFLICT_WITH_NOT_MEASURED")
    if orders and not ("AB" in orders and "BA" in orders):
        issues.add("ORDER_UNBALANCED")
    if any(seen != {"AB", "BA"} for seen in orders_by_session.values()):
        issues.add("SESSION_ORDER_UNBALANCED")
    if len(time_boundaries) > 1:
        issues.add("TIME_BOUNDARY_INCONSISTENT")
    if len(sessions) < 2:
        issues.add("INDEPENDENT_SESSIONS_NOT_DEMONSTRATED")
    note = task.get("energy_note")
    if not isinstance(note, str) or "ENERGY_NOT_MEASURED" not in note:
        issues.add("NO_SENSOR_STATUS_UNVERIFIED")
    warmup = task.get("warmup_note")
    if isinstance(warmup, str) and "no warmup" in warmup.lower():
        issues.add("JIT_WARMUP_NOT_CONTROLLED")
    return {"status": "READINESS_BLOCKED" if issues else "STRUCTURAL_PREFLIGHT_ONLY",
            "issues": sorted(issues), "pairs": len(pairs),
            "process_ids": len(processes), "sessions": len(sessions)}


def inspect(path: Path) -> dict:
    raw = load_raw(path)
    tasks = {name: audit_task(item) for name, item in sorted(raw["tasks"].items())}
    return {"source": str(path), "status": "READINESS_BLOCKED"
            if any(x["issues"] for x in tasks.values()) else "STRUCTURAL_PREFLIGHT_ONLY",
            "independent_reproduction": "NOT_REPRODUCED",
            "energy_status": "ENERGY_NOT_MEASURED" if all(
                "ENERGY_MEASUREMENT_NOT_VERIFIED" not in x["issues"] and
                "NO_SENSOR_STATUS_UNVERIFIED" not in x["issues"] and
                "ENERGY_CONFLICT_WITH_NOT_MEASURED" not in x["issues"]
                for x in tasks.values()) else "ENERGY_NOT_VERIFIED",
            "sens_semantics": "NOT_EVALUATED", "fair_integrity": "NOT_EVALUATED",
            "tasks": tasks}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path, help="Existing study raw JSON, read-only")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.raw)
    except InvalidRaw as exc:
        print(json.dumps({"status": "READINESS_BLOCKED", "error": str(exc),
                          "independent_reproduction": "NOT_REPRODUCED"},
                         ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 2 if report["status"] == "READINESS_BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
