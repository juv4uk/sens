#!/usr/bin/env python3
"""Fail-closed validator for SENS FPGA exact-width JSONL evidence."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = "sens-fpga-width-evidence/v1"
FAMILIES = {
    "decoder",
    "alu-add-xor",
    "ram1024",
    "ram-packed",
    "limb-add",
    "limb-mul",
    "multi-limb",
}
TIMING = {"measured", "no-register-to-register-path", "not-run"}
SOURCE_KINDS = {"local-pnr", "ci-pnr", "imported-vendor-report"}
SEMANTIC_WIDTH_MODES = {"fixed", "mixed", "unbounded"}
PACKING_STRATEGIES = {"naive-byte", "word-aligned-32", "tight-32", "tagged-mixed"}
OPERATIONS = {"add", "sub", "cmp", "mul", "add-multi", "mul-multi"}
CORRECTNESS = {"pass", "fail"}
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
    "reserved_bits", "packing_efficiency", "semantic_width_mode",
    "packing_strategy", "depth_values", "physical_bits", "operation",
    "limb_width", "limb_count", "cycles", "timing_slack_ns",
    "clock_constraint_hz", "temporary_width", "state_count",
    "memory_reads", "memory_writes", "correctness", "input_class",
    "board",
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


def positive_number(row, key):
    value = row.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{key}: expected positive number, got {value!r}")


def require_present(row, *keys):
    missing = [key for key in keys if row.get(key) is None]
    if missing:
        raise ValueError(f"required for family {row['family']!r}: {missing}")


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

    semantic_width = row["semantic_width"]
    semantic_mode = row.get("semantic_width_mode")
    if semantic_width is None:
        if semantic_mode not in {"mixed", "unbounded"}:
            raise ValueError(
                f"line {line_no}: null semantic_width requires "
                "semantic_width_mode='mixed' or 'unbounded'"
            )
    else:
        positive_int(row, "semantic_width")
        if semantic_mode not in {None, "fixed"}:
            raise ValueError(
                f"line {line_no}: fixed semantic_width cannot use mode {semantic_mode!r}"
            )

    if semantic_mode is not None and semantic_mode not in SEMANTIC_WIDTH_MODES:
        raise ValueError(f"line {line_no}: invalid semantic_width_mode")

    positive_int(row, "physical_word_width")
    for key in ("logic", "registers", "bsram_blocks", "dsp_blocks"):
        nonnegative_int(row, key)

    for key in (
        "cls", "latency_cycles", "logical_bits", "reserved_bits",
        "physical_bits", "cycles", "state_count", "memory_reads",
        "memory_writes",
    ):
        if row.get(key) is not None:
            nonnegative_int(row, key)
    for key in ("initiation_interval", "depth_values", "limb_width", "limb_count", "temporary_width"):
        if row.get(key) is not None:
            positive_int(row, key)
    for key in ("clock_constraint_hz",):
        if row.get(key) is not None:
            positive_number(row, key)

    fmax = row["fmax_hz"]
    if fmax is not None and (
        not isinstance(fmax, (int, float)) or isinstance(fmax, bool) or fmax <= 0
    ):
        raise ValueError(f"line {line_no}: fmax_hz must be null or positive number")
    if row["timing_status"] == "measured" and fmax is None:
        raise ValueError(f"line {line_no}: measured timing requires fmax_hz")
    if row["timing_status"] != "measured" and fmax is not None:
        raise ValueError(f"line {line_no}: non-measured timing must not claim fmax_hz")

    slack = row.get("timing_slack_ns")
    if slack is not None and (
        not isinstance(slack, (int, float)) or isinstance(slack, bool)
    ):
        raise ValueError(f"line {line_no}: timing_slack_ns must be null or number")

    eff = row.get("packing_efficiency")
    if eff is not None and (
        not isinstance(eff, (int, float))
        or isinstance(eff, bool)
        or not (0 <= eff <= 1)
    ):
        raise ValueError(f"line {line_no}: packing_efficiency must be null or [0,1]")

    strategy = row.get("packing_strategy")
    if strategy is not None and strategy not in PACKING_STRATEGIES:
        raise ValueError(f"line {line_no}: invalid packing_strategy")

    operation = row.get("operation")
    if operation is not None and operation not in OPERATIONS:
        raise ValueError(f"line {line_no}: invalid operation")

    correctness = row.get("correctness")
    if correctness is not None and correctness not in CORRECTNESS:
        raise ValueError(f"line {line_no}: invalid correctness")

    for key in ("input_class", "board"):
        value = row.get(key)
        if value is not None and (not isinstance(value, str) or not value):
            raise ValueError(f"line {line_no}: {key} must be null or non-empty string")

    if not SHA256.fullmatch(row["bench_source_sha256"]):
        raise ValueError(f"line {line_no}: invalid bench_source_sha256")
    if not SHA256.fullmatch(row["source_rpt_sha256"]):
        raise ValueError(f"line {line_no}: invalid source_rpt_sha256")

    # Semantic width is never inferred from physical storage. Padded controls are
    # expected to make this inequality explicit.
    if row["candidate"] == "padded-control":
        if semantic_width is None:
            raise ValueError(f"line {line_no}: padded-control requires fixed semantic_width")
        if row["physical_word_width"] <= semantic_width:
            raise ValueError(
                f"line {line_no}: padded-control must have physical width > semantic width"
            )

    if row["family"] == "ram1024" and row["bsram_blocks"] == 0:
        raise ValueError(f"line {line_no}: ram1024 row must report BSRAM use")

    if row["family"] == "ram-packed":
        require_present(
            row,
            "packing_strategy",
            "depth_values",
            "logical_bits",
            "physical_bits",
            "reserved_bits",
            "packing_efficiency",
        )
        physical_bits = row["physical_bits"]
        logical_bits = row["logical_bits"]
        reserved_bits = row["reserved_bits"]
        if physical_bits <= 0:
            raise ValueError(f"line {line_no}: ram-packed physical_bits must be > 0")
        if logical_bits > physical_bits:
            raise ValueError(f"line {line_no}: logical_bits cannot exceed physical_bits")
        if reserved_bits != physical_bits - logical_bits:
            raise ValueError(
                f"line {line_no}: reserved_bits must equal physical_bits-logical_bits"
            )
        expected_eff = logical_bits / physical_bits
        if not math.isclose(
            row["packing_efficiency"], expected_eff, rel_tol=1e-12, abs_tol=1e-12
        ):
            raise ValueError(
                f"line {line_no}: packing_efficiency does not match logical/physical bits"
            )
        if semantic_width is None:
            if semantic_mode != "mixed":
                raise ValueError(
                    f"line {line_no}: mixed ram-packed stream requires semantic_width_mode='mixed'"
                )
        else:
            expected_logical = semantic_width * row["depth_values"]
            if logical_bits != expected_logical:
                raise ValueError(
                    f"line {line_no}: fixed-width ram-packed logical_bits must equal "
                    "semantic_width*depth_values"
                )

    limb_families = {"limb-add", "limb-mul", "multi-limb"}
    if row["family"] in limb_families:
        if semantic_width is not None or semantic_mode != "unbounded":
            raise ValueError(
                f"line {line_no}: Number limb evidence must use "
                "semantic_width=null and semantic_width_mode='unbounded'"
            )
        require_present(row, "limb_width", "operation")
        if row["family"] == "limb-add" and operation != "add":
            raise ValueError(f"line {line_no}: limb-add requires operation='add'")
        if row["family"] == "limb-mul" and operation != "mul":
            raise ValueError(f"line {line_no}: limb-mul requires operation='mul'")
        if row["family"] == "multi-limb":
            require_present(row, "limb_count")
            if operation not in {"add", "mul", "add-multi", "mul-multi"}:
                raise ValueError(
                    f"line {line_no}: multi-limb requires add/mul operation"
                )

        limb_width = row["limb_width"]
        temp_width = row.get("temporary_width")
        if row["family"] == "limb-add" and temp_width is not None:
            if temp_width < limb_width + 1:
                raise ValueError(
                    f"line {line_no}: exact limb-add temporary_width must cover carry bit"
                )
        if row["family"] == "limb-mul":
            require_present(row, "temporary_width")
            if temp_width < 2 * limb_width:
                raise ValueError(
                    f"line {line_no}: exact limb-mul temporary_width must be >= 2*limb_width"
                )


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
