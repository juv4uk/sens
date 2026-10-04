#!/usr/bin/env python3
"""Fail-closed validator for SENS FPGA exact-width JSONL evidence."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA = "sens-fpga-width-evidence/v1"
FAMILIES = {"decoder", "alu-add-xor", "ram1024"}
TIMING = {"measured", "no-register-to-register-path", "not-run"}
SOURCE_KINDS = {"local-pnr", "ci-pnr", "imported-vendor-report"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")

REQUIRED = {
    "schema", "case_id", "candidate", "family", "semantic_subject",
    "semantic_width", "physical_word_width", "logic", "registers",
    "bsram_blocks", "dsp_blocks", "fmax_hz", "timing_status", "tool",
    "tool_version", "device", "source_kind", "bench_source_sha256",
    "source_rpt_sha256", "notes",
}
OPTIONAL = {
    "cls", "latency_cycles", "initiation_interval", "logical_bits",
    "reserved_bits", "packing_efficiency",
}
ALLOWED = REQUIRED | OPTIONAL


def nonnegative_int(row, key):
    value = row.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{key}: expected non-negative integer, got {value!r}")


def positive_int(row, key):
    value = row.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{key}: expected positive integer, got {value!r}")


def validate(row, line_no):
    missing = sorted(REQUIRED - row.keys())
    extra = sorted(row.keys() - ALLOWED)
    if missing:
        raise ValueError(f"line {line_no}: missing fields: {missing}")
    if extra:
        raise ValueError(f"line {line_no}: unknown fields: {extra}")
    if row["schema"] != SCHEMA:
        raise ValueError(f"line {line_no}: schema must be {SCHEMA!r}")
    if row["family"] not in FAMILIES:
        raise ValueError(f"line {line_no}: unsupported family {row['family']!r}")
    if row["timing_status"] not in TIMING:
        raise ValueError(f"line {line_no}: invalid timing_status")
    if row["source_kind"] not in SOURCE_KINDS:
        raise ValueError(f"line {line_no}: invalid source_kind")

    positive_int(row, "semantic_width")
    positive_int(row, "physical_word_width")
    for key in ("logic", "registers", "bsram_blocks", "dsp_blocks"):
        nonnegative_int(row, key)

    for key in ("cls", "latency_cycles", "logical_bits", "reserved_bits"):
        if row.get(key) is not None:
            nonnegative_int(row, key)
    if row.get("initiation_interval") is not None:
        positive_int(row, "initiation_interval")

    fmax = row["fmax_hz"]
    if fmax is not None and (not isinstance(fmax, (int, float)) or isinstance(fmax, bool) or fmax <= 0):
        raise ValueError(f"line {line_no}: fmax_hz must be null or positive number")
    if row["timing_status"] == "measured" and fmax is None:
        raise ValueError(f"line {line_no}: measured timing requires fmax_hz")
    if row["timing_status"] != "measured" and fmax is not None:
        raise ValueError(f"line {line_no}: non-measured timing must not claim fmax_hz")

    eff = row.get("packing_efficiency")
    if eff is not None and (not isinstance(eff, (int, float)) or isinstance(eff, bool) or not (0 <= eff <= 1)):
        raise ValueError(f"line {line_no}: packing_efficiency must be null or [0,1]")

    if not SHA256.fullmatch(row["bench_source_sha256"]):
        raise ValueError(f"line {line_no}: invalid bench_source_sha256")
    if not SHA256.fullmatch(row["source_rpt_sha256"]):
        raise ValueError(f"line {line_no}: invalid source_rpt_sha256")

    # Semantic width is never inferred from physical storage. Padded controls are
    # expected to make this inequality explicit.
    if row["candidate"] == "padded-control" and row["physical_word_width"] <= row["semantic_width"]:
        raise ValueError(f"line {line_no}: padded-control must have physical width > semantic width")

    if row["family"] == "ram1024" and row["bsram_blocks"] == 0:
        raise ValueError(f"line {line_no}: ram1024 row must report BSRAM use")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    args = ap.parse_args()

    seen = set()
    count = 0
    for line_no, raw in enumerate(args.jsonl.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        row = json.loads(raw)
        validate(row, line_no)
        if row["case_id"] in seen:
            raise ValueError(f"line {line_no}: duplicate case_id {row['case_id']!r}")
        seen.add(row["case_id"])
        count += 1

    if not count:
        raise ValueError("evidence file is empty")
    print(f"validated {count} FPGA evidence rows from {args.jsonl}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
