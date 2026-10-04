#!/usr/bin/env python3
"""Focused semantic guard tests for the FPGA evidence validator."""

from __future__ import annotations

from copy import deepcopy

from validate import validate

SHA = "0" * 64


def base_row() -> dict[str, object]:
    return {
        "schema": "sens-fpga-width-evidence/v1",
        "case_id": "selftest/base",
        "candidate": "selftest",
        "family": "decoder",
        "semantic_subject": "Core.D3",
        "semantic_width": 3,
        "physical_word_width": 3,
        "logic": 0,
        "registers": 0,
        "bsram_blocks": 0,
        "dsp_blocks": 0,
        "fmax_hz": None,
        "timing_status": "not-run",
        "tool": "selftest",
        "tool_version": "1",
        "device": "none",
        "source_kind": "ci-pnr",
        "bench_source_sha256": SHA,
        "source_rpt_sha256": SHA,
        "notes": "validator selftest only",
    }


def expect_ok(row: dict[str, object]) -> None:
    validate(row, 1)


def expect_bad(row: dict[str, object], needle: str) -> None:
    try:
        validate(row, 1)
    except ValueError as exc:
        if needle not in str(exc):
            raise AssertionError(f"expected {needle!r} in {exc!r}") from exc
    else:
        raise AssertionError(f"expected rejection containing {needle!r}")


def main() -> None:
    fixed = base_row()
    expect_ok(fixed)

    packed = base_row()
    packed.update(
        {
            "case_id": "selftest/packed-d3",
            "family": "ram-packed",
            "semantic_subject": "Core.D3",
            "semantic_width": 3,
            "semantic_width_mode": "fixed",
            "physical_word_width": 32,
            "packing_strategy": "tight-32",
            "depth_values": 256,
            "logical_bits": 768,
            "physical_bits": 768,
            "reserved_bits": 0,
            "packing_efficiency": 1.0,
            "bsram_blocks": 1,
        }
    )
    expect_ok(packed)

    mixed = deepcopy(packed)
    mixed.update(
        {
            "case_id": "selftest/packed-mixed",
            "semantic_subject": "mixed Core domains",
            "semantic_width": None,
            "semantic_width_mode": "mixed",
            "packing_strategy": "tagged-mixed",
            "logical_bits": 700,
            "physical_bits": 768,
            "reserved_bits": 68,
            "packing_efficiency": 700 / 768,
        }
    )
    expect_ok(mixed)

    limb = base_row()
    limb.update(
        {
            "case_id": "selftest/limb24-mul",
            "family": "limb-mul",
            "semantic_subject": "Number",
            "semantic_width": None,
            "semantic_width_mode": "unbounded",
            "physical_word_width": 24,
            "operation": "mul",
            "limb_width": 24,
            "temporary_width": 48,
            "dsp_blocks": 1,
            "correctness": "pass",
        }
    )
    expect_ok(limb)

    bad_semantic_limb = deepcopy(limb)
    bad_semantic_limb["semantic_width"] = 24
    bad_semantic_limb["semantic_width_mode"] = "fixed"
    expect_bad(bad_semantic_limb, "Number limb evidence")

    bad_mul_width = deepcopy(limb)
    bad_mul_width["temporary_width"] = 47
    expect_bad(bad_mul_width, "2*limb_width")

    bad_pack = deepcopy(packed)
    bad_pack["reserved_bits"] = 1
    expect_bad(bad_pack, "reserved_bits must equal")

    bad_null = base_row()
    bad_null["semantic_width"] = None
    expect_bad(bad_null, "null semantic_width requires")

    print("PASS FPGA evidence validator semantic guards")


if __name__ == "__main__":
    main()
