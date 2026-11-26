#!/usr/bin/env python3
"""Fail-closed *physical evidence* sanity, not a SENS semantic interpreter."""
from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "t01-cold-40724311685.json"
SOURCE_SHA = "1a4635d8fc812bb889e09a01dbb79ebdcdb274f5"
SOURCE_BLOB = "ecaead4c0f7ffa881b936396bdececbd4f5b2153"
JOB_ID = 122943309505
EXPECTED_RAW = (
    (1, "0.53", 22136, "0.52", "0.00"),
    (2, "0.52", 22076, "0.51", "0.00"),
    (3, "0.52", 21948, "0.51", "0.00"),
    (4, "0.53", 21956, "0.52", "0.00"),
    (5, "0.51", 22108, "0.51", "0.00"),
)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("schema") != "sens-t01-cold-observation/v1":
        errors.append("SCHEMA_INVALID")
    if doc.get("status") != "EXPLORATORY_NOT_ADMITTED":
        errors.append("STATUS_NOT_EXPLORATORY")
    p = doc.get("provenance", {})
    if not isinstance(p, dict) or (
        p.get("git_sha") != SOURCE_SHA
        or p.get("source_measure_git_blob") != SOURCE_BLOB
        or p.get("github_run_id") != 40724311685
        or p.get("github_job_id") != JOB_ID
    ):
        errors.append("PROVENANCE_MISMATCH")
    w = doc.get("workload", {})
    if not isinstance(w, dict) or (
        w.get("id") != "T01-symbolic-recursion"
        or w.get("input_n") != 24
        or w.get("verified_output") != "46368"
        or w.get("language") != "SENS"
    ):
        errors.append("WORKLOAD_OR_PARITY_MISMATCH")
    env = doc.get("environment", {})
    if not isinstance(env, dict) or env.get("sessions") != 1 or env.get("independent_sessions") != 1:
        errors.append("SESSION_COUNT_INVALID")
    m = doc.get("measurement", {})
    if not isinstance(m, dict) or (
        m.get("energy_status") != "ENERGY_NOT_MEASURED"
        or m.get("energy_joules") is not None
        or m.get("confidence_interval") is not None
        or m.get("comparison_winner") is not None
        or m.get("time_unit") != "seconds"
        or m.get("memory_unit") != "KiB"
    ):
        errors.append("ENERGY_OR_INFERENCE_FABRICATED")
    samples = doc.get("samples")
    if not isinstance(samples, list) or len(samples) != 5:
        errors.append("SAMPLE_COUNT_INVALID")
        return errors
    for index, row in enumerate(samples):
        if not isinstance(row, dict):
            errors.append("SAMPLE_INVALID")
            continue
        try:
            observed = (
                row["trial"], row["elapsed_seconds"], row["peak_rss_kib"],
                row["user_seconds"], row["system_seconds"],
            )
            if observed != EXPECTED_RAW[index]:
                errors.append(f"RAW_LOG_MISMATCH:{index + 1}")
            for field in ("elapsed_seconds", "user_seconds", "system_seconds"):
                value = row[field]
                if not isinstance(value, str) or not Decimal(value).is_finite() or Decimal(value) < 0:
                    errors.append(f"TIME_INVALID:{index + 1}:{field}")
            if Decimal(row["elapsed_seconds"]) <= 0 or (
                type(row["peak_rss_kib"]) is not int or row["peak_rss_kib"] <= 0
            ):
                errors.append(f"PHYSICAL_INVALID:{index + 1}")
        except (KeyError, TypeError, InvalidOperation, ValueError):
            errors.append(f"SAMPLE_INVALID:{index + 1}")
    return errors


def main(path: Path = EVIDENCE) -> int:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        errors = validate(doc)
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        print(f"EVIDENCE_BLOCKED: {error}", file=sys.stderr)
        return 2
    if errors:
        print(f"EVIDENCE_BLOCKED: {','.join(errors)}", file=sys.stderr)
        return 2
    print("EVIDENCE_STRUCTURAL_PASS raw_rows=5 sessions=1 energy=ENERGY_NOT_MEASURED admission=EXPLORATORY_NOT_ADMITTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) == 2 else EVIDENCE))
