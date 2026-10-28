#!/usr/bin/env python3
"""Read-only clock-resolution admission for physical T01 C/JS/SENS TSV.

This audits *measurement mechanics*, not SENS semantics. It never calculates a
speed ratio/CI or invents joules. It cannot infer independent sessions from
nine process starts within one GitHub Actions job.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import re
import sys

HEADER = ("round", "language", "wall_seconds", "peak_rss_kib", "child_exit", "stdout")
ORDER = (("C", "JS", "SENS"), ("JS", "SENS", "C"), ("SENS", "C", "JS"))
CENTISECOND = Decimal("0.01")
UINT = re.compile(r"(?:0|[1-9][0-9]*)", re.ASCII)
ELAPSED = re.compile(r"(?:0|[1-9][0-9]*)\.[0-9]{2}", re.ASCII)
SCHEMA = "sens-t01-clock-admission/v1"


class InvalidPhysicalEvidence(ValueError):
    pass


def audit(raw: bytes) -> dict:
    digest = hashlib.sha256(raw).hexdigest()
    try:
        decoded = raw.decode("utf-8")
        # csv.DictReader silently accepts duplicate column names: prohibit them.
        reader = csv.reader(io.StringIO(decoded, newline=""), delimiter="\t", strict=True)
        header = tuple(next(reader))
        if header != HEADER:
            raise InvalidPhysicalEvidence("T01_TSV_HEADER_MISMATCH")
        rows = list(reader)
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise InvalidPhysicalEvidence("T01_TSV_INVALID_ENCODING_OR_CSV") from exc

    if len(rows) != 9:
        raise InvalidPhysicalEvidence("T01_REQUIRES_EXACTLY_9_SAMPLES")

    zeros = []
    for idx, values in enumerate(rows):
        round_id, index = divmod(idx, 3)
        if len(values) != len(HEADER):
            raise InvalidPhysicalEvidence("T01_ROW_FIELD_COUNT")
        rnd, language, wall, rss, child_exit, output = values
        if rnd != str(round_id + 1) or language != ORDER[round_id][index]:
            raise InvalidPhysicalEvidence("T01_BALANCED_ORDER_OR_DUPLICATE_INVALID")
        if not ELAPSED.fullmatch(wall):
            raise InvalidPhysicalEvidence("T01_WALL_NOT_GNU_CENTISECOND_DECIMAL")
        try:
            elapsed = Decimal(wall)
        except InvalidOperation as exc:
            raise InvalidPhysicalEvidence("T01_BAD_ELAPSED") from exc
        if not UINT.fullmatch(rss) or int(rss) <= 0:
            raise InvalidPhysicalEvidence("T01_PEAK_RSS_INVALID")
        if child_exit != "0" or output != "144":
            raise InvalidPhysicalEvidence("T01_RESULT_OR_EXIT_NOT_VERIFIED")
        if elapsed < CENTISECOND:
            zeros.append({"round": round_id + 1, "language": language,
                          "reported_wall_seconds": wall})

    reasons = ["NO_INDEPENDENT_SESSION_EVIDENCE_IN_TSV"]
    if zeros:
        reasons.insert(0, "AT_LEAST_ONE_ELAPSED_VALUE_BELOW_GNU_TIME_RESOLUTION")
    return {
        "schema": SCHEMA,
        "raw_sha256": digest,
        "status": "DESCRIPTIVE_ONLY_NO_INFERENCE",
        "structure": "NINE_OUTPUT_VERIFIED_PROCESS_RECORDS",
        "clock_resolution_s": "0.01",
        "clock_admission": "BLOCKED_BELOW_RESOLUTION" if zeros else "REPORTED_PRECISION_ONLY",
        "zero_rounded_samples": zeros,
        "samples": len(rows),
        "languages": ["C", "JS", "SENS"],
        "functional_unit": "T01 naive Fibonacci(12) stdout 144",
        "expected_exit": 0,
        "inference_admitted": False,
        "inference_blockers": reasons,
        "speed_ratios": None,
        "confidence_intervals": None,
        "energy_status": "ENERGY_NOT_MEASURED",
        "energy_joules": None,
        "limits": [
            "GNU /usr/bin/time %e reports 0.01-second units; 0.00 is not zero runtime.",
            "One artifact/session and three process rounds are not independent sessions.",
            "Optimized C and debug SENS are different build profiles.",
            "No workload-size or contract changes; no SENS semantic laws are tested.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = audit(args.samples.read_bytes())
    except (OSError, InvalidPhysicalEvidence) as exc:
        print(f"T01_EVIDENCE_BLOCKED: {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"{report['status']}: samples={report['samples']} "
          f"clock={report['clock_admission']} raw_sha256={report['raw_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
